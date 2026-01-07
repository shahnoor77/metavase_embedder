"""
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.database import engine
from app.models import Base
from app.auth.routes import router as auth_router
from app.workspace.routes import router as workspace_router
from app.dashboard.routes import router as dashboard_router
from app.metabase.routes import router as metabase_router
from app.metabase.client import MetabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the application.
    Handles startup and shutdown operations.
    """
    # Startup
    logger.info("Starting Metabase Embedder application...")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
    
    # Initialize Metabase
    try:
        mb_client = MetabaseClient(
            base_url=settings.METABASE_URL,
            admin_email=settings.METABASE_ADMIN_EMAIL,
            admin_password=settings.METABASE_ADMIN_PASSWORD,
            embedding_secret=settings.METABASE_EMBEDDING_SECRET
        )
        
        # Check if Metabase is healthy
        is_healthy = await mb_client.check_health()
        
        if not is_healthy:
            logger.warning("Metabase is not healthy yet, it might still be starting up")
        else:
            logger.info("Metabase is healthy")
            
            # Check if Metabase needs initial setup
            setup_token = await mb_client.get_setup_token()
            
            if setup_token:
                logger.info("Metabase needs initial setup, setting it up now...")
                try:
                    await mb_client.setup_metabase(
                    admin_email=settings.METABASE_ADMIN_EMAIL,
                    admin_password=settings.METABASE_ADMIN_PASSWORD,
                    first_name="Admin",
                    last_name="User"
                )
                    logger.info("Metabase setup completed")
                except Exception as e:
                    if "403" in str(e):
                        logger.error("Metabase is already configured")
                    else:
                        logger.error(f"Error setting up Metabase: {str(e)}")
                        raise e
            else:
                logger.info("Metabase is already configured")
                
            # Add analytics database to Metabase
            try:
                databases = await mb_client.list_databases()
                analytics_db_exists = False
                if isinstance(databases, list):
                    analytics_db_exists = any(
                        isinstance(db, dict) and db.get('name') == 'Analytics Database'
                        for db in databases
                    )
                
                if not analytics_db_exists:
                    logger.info("Adding analytics database to Metabase...")
                    await mb_client.add_database(
                        name="Analytics Database",
                        engine="postgres",
                        host=settings.ANALYTICS_DB_HOST,
                        port=settings.ANALYTICS_DB_PORT,
                        dbname=settings.ANALYTICS_DB_NAME,
                        user=settings.ANALYTICS_DB_USER,
                        password=settings.ANALYTICS_DB_PASSWORD
                    )
                    logger.info("Analytics database added successfully")
                else:
                    logger.info("Analytics database already exists in Metabase")
                    
            except Exception as e:
                logger.error(f"Error setting up analytics database: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error initializing Metabase: {str(e)}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="Metabase Embedder",
    description="Metabase integration with workspace management and embedding",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500
        }
    )


# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(workspace_router)  # already prefixed with /api/workspaces
app.include_router(dashboard_router, prefix="/api/dashboards", tags=["dashboards"])
app.include_router(metabase_router, prefix="/api/metabase", tags=["metabase"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Metabase Embedder API",
        "version": "1.0.0",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "metabase-embedder-backend"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )