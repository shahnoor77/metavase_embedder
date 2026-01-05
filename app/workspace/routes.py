"""
Workspace routes for creating and managing user workspaces with Metabase integration.
"""
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Workspace, WorkspaceMember, Dashboard
from app.auth.routes import get_current_user
from app.metabase.client import MetabaseClient
from app.config import Settings

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])
logger = logging.getLogger(__name__)
settings = Settings()


# ==================== Dependency Injection ====================

def get_metabase_client() -> MetabaseClient:
    """Get Metabase client instance."""
    return MetabaseClient(
        base_url=settings.METABASE_URL,
        admin_email=settings.METABASE_ADMIN_EMAIL,
        admin_password=settings.METABASE_ADMIN_PASSWORD,
        embedding_secret=settings.METABASE_EMBEDDING_SECRET
    )


# ==================== Pydantic Schemas ====================

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    metabase_collection_id: Optional[int]
    metabase_collection_name: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    id: int
    workspace_id: int
    metabase_dashboard_id: int
    metabase_dashboard_name: str
    description: Optional[str]
    is_public: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmbeddedUrlResponse(BaseModel):
    url: str
    expires_in_minutes: int


# ==================== Workspace Routes ====================

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mb_client: MetabaseClient = Depends(get_metabase_client)
):
    """
    Create a new workspace with Metabase collection and permissions.
    
    This endpoint:
    1. Creates a workspace in the application database
    2. Creates a corresponding collection in Metabase
    3. Creates a permission group for the workspace
    4. Sets up write permissions for the group on the collection
    5. Adds the current user to the permission group
    
    Args:
        workspace_data: Workspace creation data
        current_user: Current authenticated user
        db: Database session
        mb_client: Metabase client
        
    Returns:
        Created workspace with Metabase integration details
    """
    try:
        # 1. Create Metabase collection
        logger.info(f"Creating Metabase collection for workspace: {workspace_data.name}")
        
        collection = await mb_client.create_collection(
            name=workspace_data.name,
            description=workspace_data.description or ""
        )
        
        collection_id = collection.get("id")
        collection_name = collection.get("name")
        
        logger.info(f"Created Metabase collection: {collection_id}")
        
        # 2. Create Metabase permission group
        logger.info(f"Creating Metabase group for workspace: {workspace_data.name}")
        
        group_name = f"{workspace_data.name} Team"
        group = await mb_client.create_group(name=group_name)
        
        group_id = group.get("id")
        group_name = group.get("name")
        
        logger.info(f"Created Metabase group: {group_id}")
        
        # 3. Set collection permissions for the group (write access)
        logger.info(f"Setting write permissions for group {group_id} on collection {collection_id}")
        
        await mb_client.set_collection_permissions(
            group_id=group_id,
            collection_id=collection_id,
            permission="write"
        )
        
        # 4. Create workspace in application database
        new_workspace = Workspace(
            name=workspace_data.name,
            description=workspace_data.description,
            owner_id=current_user.id,
            metabase_collection_id=collection_id,
            metabase_collection_name=collection_name,
            metabase_group_id=group_id,
            metabase_group_name=group_name,
            is_active=True
        )
        
        db.add(new_workspace)
        db.commit()
        db.refresh(new_workspace)
        
        # 5. Add owner as workspace member
        member = WorkspaceMember(
            workspace_id=new_workspace.id,
            user_id=current_user.id,
            role="owner"
        )
        
        db.add(member)
        db.commit()
        
        logger.info(f"Successfully created workspace {new_workspace.id} with Metabase integration")
        
        return new_workspace
        
    except Exception as e:
        logger.error(f"Error creating workspace: {str(e)}")
        db.rollback()
        
        # Attempt cleanup if we created Metabase resources
        try:
            if 'collection_id' in locals():
                await mb_client.delete_collection(collection_id)
            if 'group_id' in locals():
                await mb_client.delete_group(group_id)
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup: {str(cleanup_error)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workspace: {str(e)}"
        )


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all workspaces the current user has access to.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of workspaces
    """
    # Get workspaces where user is owner or member
    owned_workspaces = db.query(Workspace).filter(
        Workspace.owner_id == current_user.id,
        Workspace.is_active == True
    ).all()
    
    member_workspaces = db.query(Workspace).join(WorkspaceMember).filter(
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.workspace_id != None,
        Workspace.is_active == True
    ).all()
    
    # Combine and deduplicate
    workspace_ids = set()
    workspaces = []
    
    for ws in owned_workspaces + member_workspaces:
        if ws.id not in workspace_ids:
            workspace_ids.add(ws.id)
            workspaces.append(ws)
    
    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific workspace by ID.
    
    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Workspace details
        
    Raises:
        HTTPException: If workspace not found or user doesn't have access
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.is_active == True
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check if user has access
    is_owner = workspace.owner_id == current_user.id
    is_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first() is not None
    
    if not (is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: int,
    workspace_data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mb_client: MetabaseClient = Depends(get_metabase_client)
):
    """
    Update a workspace.
    
    Args:
        workspace_id: Workspace ID
        workspace_data: Update data
        current_user: Current authenticated user
        db: Database session
        mb_client: Metabase client
        
    Returns:
        Updated workspace
        
    Raises:
        HTTPException: If workspace not found or user is not owner
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.is_active == True
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can update it"
        )
    
    try:
        # Update workspace in database
        if workspace_data.name:
            workspace.name = workspace_data.name
            
            # Update Metabase collection name
            if workspace.metabase_collection_id:
                await mb_client.update_collection(
                    collection_id=workspace.metabase_collection_id,
                    name=workspace_data.name
                )
        
        if workspace_data.description is not None:
            workspace.description = workspace_data.description
            
            # Update Metabase collection description
            if workspace.metabase_collection_id:
                await mb_client.update_collection(
                    collection_id=workspace.metabase_collection_id,
                    description=workspace_data.description
                )
        
        workspace.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(workspace)
        
        return workspace
        
    except Exception as e:
        logger.error(f"Error updating workspace: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workspace: {str(e)}"
        )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mb_client: MetabaseClient = Depends(get_metabase_client)
):
    """
    Delete a workspace (soft delete).
    
    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session
        mb_client: Metabase client
        
    Raises:
        HTTPException: If workspace not found or user is not owner
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.is_active == True
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    if workspace.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the workspace owner can delete it"
        )
    
    try:
        # Soft delete in database
        workspace.is_active = False
        workspace.updated_at = datetime.utcnow()
        
        # Delete from Metabase
        if workspace.metabase_collection_id:
            await mb_client.delete_collection(workspace.metabase_collection_id)
        
        if workspace.metabase_group_id:
            await mb_client.delete_group(workspace.metabase_group_id)
        
        db.commit()
        
        logger.info(f"Successfully deleted workspace {workspace_id}")
        
    except Exception as e:
        logger.error(f"Error deleting workspace: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workspace: {str(e)}"
        )


@router.get("/{workspace_id}/embedded-url", response_model=EmbeddedUrlResponse)
async def get_workspace_embedded_url(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    mb_client: MetabaseClient = Depends(get_metabase_client)
):
    """
    Get the embedded URL for accessing the workspace collection in Metabase.
    
    This URL can be used in an iframe to display the Metabase collection interface.
    
    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session
        mb_client: Metabase client
        
    Returns:
        Embedded URL and expiration time
        
    Raises:
        HTTPException: If workspace not found or user doesn't have access
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.is_active == True
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Check access
    is_owner = workspace.owner_id == current_user.id
    is_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first() is not None
    
    if not (is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    if not workspace.metabase_collection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace doesn't have a Metabase collection"
        )
    
    # Generate embedded URL
    url_path = mb_client.get_embedded_collection_url(workspace.metabase_collection_id)
    
    return {
        "url": url_path,
        "expires_in_minutes": 10
    }


@router.get("/{workspace_id}/dashboards", response_model=List[DashboardResponse])
async def list_workspace_dashboards(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all dashboards in a workspace.
    
    Args:
        workspace_id: Workspace ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of dashboards
    """
    # Verify access
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.is_active == True
    ).first()
    
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    is_owner = workspace.owner_id == current_user.id
    is_member = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == current_user.id
    ).first() is not None
    
    if not (is_owner or is_member):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Get dashboards
    dashboards = db.query(Dashboard).filter(
        Dashboard.workspace_id == workspace_id
    ).all()
    
    return dashboards