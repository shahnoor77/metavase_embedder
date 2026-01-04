from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import User, Workspace, Dashboard, DashboardVersion
from app.auth.dependencies import get_current_user
from app.metabase.client import MetabaseClient

router = APIRouter()

class DashboardCreate(BaseModel):
    workspace_id: int
    name: str

class DashboardResponse(BaseModel):
    id: int
    workspace_id: int
    metabase_dashboard_id: int
    name: str
    created_by_id: int
    embed_url: Optional[str] = None
    
    class Config:
        from_attributes = True

@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workspace = db.query(Workspace).filter(
        Workspace.id == dashboard_data.workspace_id
    ).first()
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
    
    mb_client = MetabaseClient()
    await mb_client.login()
    
    try:
        mb_dashboard = await mb_client.create_dashboard(
            dashboard_data.name,
            workspace.metabase_collection_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create dashboard in Metabase: {str(e)}"
        )
    
    dashboard = Dashboard(
        workspace_id=workspace.id,
        metabase_dashboard_id=mb_dashboard["id"],
        name=dashboard_data.name,
        created_by_id=current_user.id
    )
    
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    
    version = DashboardVersion(
        dashboard_id=dashboard.id,
        snapshot=mb_dashboard
    )
    db.add(version)
    db.commit()
    
    return dashboard

@router.get("", response_model=List[DashboardResponse])
def list_dashboards(
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
    
    return workspace.dashboards

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dashboard not found"
        )
    
    if current_user not in dashboard.workspace.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    mb_client = MetabaseClient()
    await mb_client.login()
    
    try:
        embed_url = mb_client.generate_embed_url(dashboard.metabase_dashboard_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embed URL: {str(e)}"
        )
    
    response_data = DashboardResponse.model_validate(dashboard)
    response_data.embed_url = embed_url
    return response_data