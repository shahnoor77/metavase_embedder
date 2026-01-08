import logging
from sqlalchemy.orm import Session
from app.models import Workspace, Dashboard
from app.metabase.client import MetabaseClient

logger = logging.getLogger(__name__)

async def run_system_sync(db: Session, mb_client: MetabaseClient):
    """
    Synchronizes Metabase collections with the local database.
    
    1. Repairs: Forces 'Enable Embedding' toggle to ON for all collections.
    2. Discovers: Finds new dashboards in Metabase and adds them to the local DB.
    """
    try:
        # Fetch all active workspaces that have a linked Metabase collection
        workspaces = db.query(Workspace).filter(Workspace.is_active == True).all()
        
        for ws in workspaces:
            if not ws.metabase_collection_id:
                continue

            # 1. Automatic Repair: Ensure the collection is "Published"
            # This is the primary fix for the "Not Found" 404 error
            logger.info(f"Syncing Metabase permissions for Workspace: {ws.name}")
            await mb_client.enable_collection_embedding(ws.metabase_collection_id)

            # 2. Automatic Discovery: Sync Dashboards inside the collection
            items = await mb_client.get_collection_items(ws.metabase_collection_id)
            
            for item in items:
                # Metabase returns several types of items; we only want dashboards
                if item.get("model") == "dashboard":
                    mb_id = item.get("id")
                    mb_name = item.get("name")

                    # Check if this dashboard is already in our local database
                    exists = db.query(Dashboard).filter_by(metabase_dashboard_id=mb_id).first()
                    
                    if not exists:
                        logger.info(f"Importing new dashboard found in Metabase: {mb_name}")
                        new_dash = Dashboard(
                            workspace_id=ws.id,
                            metabase_dashboard_id=mb_id,
                            metabase_dashboard_name=mb_name,
                            is_public=False
                        )
                        db.add(new_dash)
        
        # Commit all new dashboards found during the sync
        db.commit()
        logger.info("Metabase System Sync: SUCCESS")
        
    except Exception as e:
        logger.error(f"Metabase System Sync: FAILED - {str(e)}")
        db.rollback()