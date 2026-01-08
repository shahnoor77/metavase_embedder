import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx

from app.config import settings  # Ensure this matches your config import style
from app.database import engine, SessionLocal
from app.models import Base
from app.metabase.client import MetabaseClient
from app.metabase.sync import run_system_sync  # The new self-healing sync

# Import routers
from app.auth.routes import router as auth_router
from app.workspace.routes import router as workspace_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Local Database Tables Initialization
    Base.metadata.create_all(bind=engine)

    # 2. Metabase Initialization
    mb_client = MetabaseClient(
        base_url=settings.METABASE_URL,
        admin_email=settings.METABASE_ADMIN_EMAIL,
        admin_password=settings.METABASE_ADMIN_PASSWORD,
        embedding_secret=settings.METABASE_EMBEDDING_SECRET
    )
    
    if await mb_client.check_health():
        logger.info("Metabase online. Starting initialization...")
        
        # Handle First-Run Setup (Provision Admin)
        setup_token = await mb_client.get_setup_token()
        if setup_token:
            logger.info("Fresh Metabase instance detected. Provisioning Admin...")
            try:
                await mb_client.setup_admin(setup_token)
                logger.info("Admin setup completed successfully.")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.info("Admin already exists. Skipping initial setup.")
                else:
                    logger.error(f"Setup error: {e.response.text}")
        
        # Always run global settings (Enable Embedding globally)
        await mb_client.setup_metabase()

        # 3. Connect Analytics Database to Metabase
        try:
            databases = await mb_client.list_databases()
            analytics_db = next(
                (db for db in databases if isinstance(db, dict) and db.get('name') == 'Analytics Database'),
                None
            )
            
            db_id = None
            if not analytics_db:
                logger.info("Connecting Metabase to the Analytics Container...")
                db_result = await mb_client.add_database(
                    name="Analytics Database",
                    engine="postgres",
                    host=settings.ANALYTICS_DB_HOST,
                    port=settings.ANALYTICS_DB_PORT,
                    dbname=settings.ANALYTICS_DB_NAME,
                    user=settings.ANALYTICS_DB_USER,
                    password=settings.ANALYTICS_DB_PASSWORD
                )
                if db_result:
                    db_id = db_result.get('id')
            else:
                db_id = analytics_db.get('id')

            if db_id:
                group_id = await mb_client.get_all_users_group_id()
                await mb_client.set_database_permissions(group_id, db_id, "public", "all")
                logger.info(f"Analytics Database (ID: {db_id}) connected and verified.")
        except Exception as e:
            logger.error(f"Failed to provision Analytics DB: {e}")

        # 4. RUN SELF-HEALING SYNC
        # This fixes 404/Not Found errors for collections and imports dashboards
        db = SessionLocal()
        try:
            logger.info("Running autonomous Metabase sync...")
            await run_system_sync(db, mb_client)
            logger.info("Sync completed successfully.")
        except Exception as sync_err:
            logger.error(f"Lifespan Sync Error: {sync_err}")
        finally:
            db.close()
            
    yield

app = FastAPI(title="Metabase Embedder API", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardize Prefixing
# Note: workspace_router already has /api/workspaces, auth usually has /auth.
# Make sure your imports inside routers match these paths.
app.include_router(auth_router)
app.include_router(workspace_router)  # Prefix is already in the router file
# Standardize Prefixing in main.py


@app.get("/")
async def root():
    return {"status": "ok", "message": "Metabase Embedder API is running"}