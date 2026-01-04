import httpx
import jwt
import time
from typing import Dict, Any, Optional
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetabaseClient:
    def __init__(self):
        self.base_url = settings.METABASE_URL
        self.email = settings.METABASE_EMAIL
        self.password = settings.METABASE_PASSWORD
        self.embedding_secret = settings.METABASE_EMBEDDING_SECRET
        self.session_token: Optional[str] = None
        self.sqlserver_db_id: Optional[int] = None
    
    async def login(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/session",
                json={"username": self.email, "password": self.password}
            )
            response.raise_for_status()
            self.session_token = response.json()["id"]
            logger.info("Successfully logged into Metabase")
    
    def _headers(self) -> Dict[str, str]:
        if not self.session_token:
            raise ValueError("Not logged in. Call login() first.")
        return {"X-Metabase-Session": self.session_token}
    
    async def setup_sqlserver_database(self) -> Optional[Dict[str, Any]]:
        """Setup SQL Server as the default database in Metabase"""
        if not settings.SQLSERVER_HOST:
            logger.warning("SQL Server configuration not provided, skipping setup")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Check if SQL Server database already exists
                databases_response = await client.get(
                    f"{self.base_url}/api/database",
                    headers=self._headers()
                )
                databases_response.raise_for_status()
                databases = databases_response.json()
                
                for db in databases:
                    if db.get("engine") == "sqlserver" and db.get("name") == "SQL Server Analytics":
                        logger.info(f"SQL Server database already exists with ID: {db['id']}")
                        self.sqlserver_db_id = db["id"]
                        return db
                
                # Create new SQL Server connection
                connection_string = f"sqlserver://{settings.SQLSERVER_HOST}:{settings.SQLSERVER_PORT};database={settings.SQLSERVER_DATABASE};trustServerCertificate={settings.SQLSERVER_TRUST_CERTIFICATE}"
                
                db_config = {
                    "engine": "sqlserver",
                    "name": "SQL Server Analytics",
                    "details": {
                        "host": settings.SQLSERVER_HOST,
                        "port": settings.SQLSERVER_PORT,
                        "db": settings.SQLSERVER_DATABASE,
                        "user": settings.SQLSERVER_USER,
                        "password": settings.SQLSERVER_PASSWORD,
                        "ssl": False,
                        "tunnel-enabled": False,
                        "advanced-options": False
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/api/database",
                    headers=self._headers(),
                    json=db_config
                )
                response.raise_for_status()
                db = response.json()
                self.sqlserver_db_id = db["id"]
                
                logger.info(f"SQL Server database created successfully with ID: {db['id']}")
                
                # Trigger schema sync
                await client.post(
                    f"{self.base_url}/api/database/{db['id']}/sync_schema",
                    headers=self._headers()
                )
                logger.info("SQL Server schema sync initiated")
                
                return db
                
        except Exception as e:
            logger.error(f"Failed to setup SQL Server database: {str(e)}")
            return None
    
    async def setup_postgres_fallback(self) -> Optional[Dict[str, Any]]:
        """Setup PostgreSQL as fallback if SQL Server fails"""
        if not settings.ANALYTICS_DB_HOST:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/database",
                    headers=self._headers(),
                    json={
                        "engine": "postgres",
                        "name": "PostgreSQL Analytics (Fallback)",
                        "details": {
                            "host": settings.ANALYTICS_DB_HOST,
                            "port": settings.ANALYTICS_DB_PORT,
                            "dbname": settings.ANALYTICS_DB_NAME,
                            "user": settings.ANALYTICS_DB_USER,
                            "password": settings.ANALYTICS_DB_PASSWORD
                        }
                    }
                )
                response.raise_for_status()
                logger.info("PostgreSQL fallback database created successfully")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL fallback: {str(e)}")
            return None
    
    async def get_default_database_id(self) -> Optional[int]:
        """Get the ID of the default analytics database (SQL Server or fallback)"""
        if self.sqlserver_db_id:
            return self.sqlserver_db_id
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/database",
                    headers=self._headers()
                )
                response.raise_for_status()
                databases = response.json()
                
                for db in databases:
                    if db.get("engine") == "sqlserver":
                        return db["id"]
                    
                for db in databases:
                    if db.get("engine") == "postgres" and "Analytics" in db.get("name", ""):
                        return db["id"]
                
                if databases:
                    return databases[0]["id"]
                    
        except Exception as e:
            logger.error(f"Failed to get default database: {str(e)}")
        
        return None
    
    async def create_group(self, name: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/permissions/group",
                headers=self._headers(),
                json={"name": name}
            )
            response.raise_for_status()
            return response.json()
    
    async def create_collection(self, name: str, group_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/collection",
                headers=self._headers(),
                json={"name": name, "color": "#509EE3"}
            )
            response.raise_for_status()
            collection = response.json()
            
            await client.put(
                f"{self.base_url}/api/collection/graph",
                headers=self._headers(),
                json={
                    "groups": {
                        str(group_id): {str(collection["id"]): "write"}
                    }
                }
            )
            
            return collection
    
    async def create_dashboard(self, name: str, collection_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/api/dashboard",
                headers=self._headers(),
                json={
                    "name": name,
                    "collection_id": collection_id
                }
            )
            response.raise_for_status()
            dashboard = response.json()
            
            await client.put(
                f"{self.base_url}/api/dashboard/{dashboard['id']}",
                headers=self._headers(),
                json={
                    "enable_embedding": True,
                    "embedding_params": {}
                }
            )
            
            return dashboard
    
    async def get_dashboard(self, dashboard_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/api/dashboard/{dashboard_id}",
                headers=self._headers()
            )
            response.raise_for_status()
            return response.json()
    
    def generate_embed_url(self, dashboard_id: int, params: Optional[Dict[str, Any]] = None) -> str:
        payload = {
            "resource": {"dashboard": dashboard_id},
            "params": params or {},
            "exp": round(time.time()) + (60 * 60 * 24)
        }
        
        token = jwt.encode(payload, self.embedding_secret, algorithm="HS256")
        return f"{self.base_url}/embed/dashboard/{token}#bordered=false&titled=false"