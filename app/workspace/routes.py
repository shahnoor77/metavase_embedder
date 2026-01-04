from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models import User, Workspace
from app.auth.dependencies import get_current_user
from app.metabase.client import MetabaseClient

router = APIRouter()

class WorkspaceCreate(BaseModel):
    name: str
    slug: str

class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    owner_id: int
    metabase_group_id: int | None
    metabase_collection_id: int | None
    
    class Config:
        from_attributes = True

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Workspace).filter(Workspace.slug == workspace_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug already exists"
        )
    
    mb_client = MetabaseClient()
    await mb_client.login()
    
    try:
        group = await mb_client.create_group(workspace_data.name)
        collection = await mb_client.create_collection(workspace_data.name, group["id"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Metabase resources: {str(e)}"
        )
    
    workspace = Workspace(
        name=workspace_data.name,
        slug=workspace_data.slug,
        owner_id=current_user.id,
        metabase_group_id=group["id"],
        metabase_collection_id=collection["id"]
    )
    workspace.users.append(current_user)
    
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    
    return workspace

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return current_user.workspaces

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    if current_user not in workspace.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return workspace