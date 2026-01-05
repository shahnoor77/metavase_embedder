"""
Metabase API client for managing collections, groups, and embedding.
"""
import logging
import httpx
import jwt
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetabaseClient:
    """Client for interacting with Metabase API."""
    
    def __init__(self, base_url: str, admin_email: str, admin_password: str, embedding_secret: str):
        """
        Initialize Metabase client.
        
        Args:
            base_url: Metabase base URL (e.g., http://metabase:3000)
            admin_email: Admin user email
            admin_password: Admin user password
            embedding_secret: Secret key for JWT embedding
        """
        self.base_url = base_url.rstrip('/')
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.embedding_secret = embedding_secret
        self.session_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid admin session token."""
        if self.session_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/session",
                    json={
                        "username": self.admin_email,
                        "password": self.admin_password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.session_token = data.get("id")
                    # Metabase sessions typically last 14 days, but we'll refresh after 1 day
                    self.token_expiry = datetime.utcnow() + timedelta(days=1)
                    logger.info("Successfully authenticated with Metabase")
                else:
                    logger.error(f"Failed to authenticate with Metabase: {response.status_code}")
                    raise Exception(f"Metabase authentication failed: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error authenticating with Metabase: {str(e)}")
            raise
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        json: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[Any, Any]:
        """
        Make an authenticated request to Metabase API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            json: JSON body
            params: Query parameters
            
        Returns:
            Response JSON
        """
        await self._ensure_authenticated()
        
        headers = {
            "X-Metabase-Session": self.session_token,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    params=params
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    return response.json() if response.text else {}
                else:
                    logger.error(f"Metabase API error: {response.status_code} - {response.text}")
                    raise Exception(f"Metabase API error: {response.status_code} - {response.text}")
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout making request to {url}")
            raise Exception("Metabase request timed out")
        except Exception as e:
            logger.error(f"Error making request to {url}: {str(e)}")
            raise
    
    # ==================== Collection Management ====================
    
    async def create_collection(self, name: str, description: str = "", parent_id: Optional[int] = None) -> Dict:
        """
        Create a new collection in Metabase.
        
        Args:
            name: Collection name
            description: Collection description
            parent_id: Parent collection ID (None for root)
            
        Returns:
            Created collection data
        """
        logger.info(f"Creating collection: {name}")
        
        collection_data = {
            "name": name,
            "description": description,
            "color": "#509EE3"
        }
        
        if parent_id is not None:
            collection_data["parent_id"] = parent_id
        
        return await self._request("POST", "collection", json=collection_data)
    
    async def get_collection(self, collection_id: int) -> Dict:
        """Get collection details."""
        return await self._request("GET", f"collection/{collection_id}")
    
    async def list_collections(self) -> List[Dict]:
        """List all collections."""
        return await self._request("GET", "collection")
    
    async def update_collection(self, collection_id: int, name: str = None, description: str = None) -> Dict:
        """Update collection details."""
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
            
        return await self._request("PUT", f"collection/{collection_id}", json=data)
    
    async def delete_collection(self, collection_id: int) -> None:
        """Delete a collection."""
        logger.info(f"Deleting collection: {collection_id}")
        await self._request("DELETE", f"collection/{collection_id}")
    
    # ==================== Group Management ====================
    
    async def create_group(self, name: str) -> Dict:
        """
        Create a permission group in Metabase.
        
        Args:
            name: Group name
            
        Returns:
            Created group data
        """
        logger.info(f"Creating group: {name}")
        
        return await self._request("POST", "permissions/group", json={"name": name})
    
    async def get_group(self, group_id: int) -> Dict:
        """Get group details."""
        return await self._request("GET", f"permissions/group/{group_id}")
    
    async def list_groups(self) -> List[Dict]:
        """List all permission groups."""
        return await self._request("GET", "permissions/group")
    
    async def delete_group(self, group_id: int) -> None:
        """Delete a permission group."""
        logger.info(f"Deleting group: {group_id}")
        await self._request("DELETE", f"permissions/group/{group_id}")
    
    # ==================== Permission Management ====================
    
    async def set_collection_permissions(self, group_id: int, collection_id: int, permission: str = "write") -> None:
        """
        Set permissions for a group on a collection.
        
        Args:
            group_id: Permission group ID
            collection_id: Collection ID
            permission: Permission level ('read', 'write', or 'none')
        """
        logger.info(f"Setting {permission} permission for group {group_id} on collection {collection_id}")
        
        # Get current permissions graph
        permissions_graph = await self._request("GET", "collection/graph")
        
        # Update permissions for the specific collection
        if "groups" not in permissions_graph:
            permissions_graph["groups"] = {}
        
        if str(group_id) not in permissions_graph["groups"]:
            permissions_graph["groups"][str(group_id)] = {}
        
        permissions_graph["groups"][str(group_id)][str(collection_id)] = permission
        
        # Update the permissions graph
        await self._request("PUT", "collection/graph", json=permissions_graph)
    
    async def add_user_to_group(self, user_id: int, group_id: int) -> None:
        """
        Add a user to a permission group.
        
        Args:
            user_id: Metabase user ID
            group_id: Permission group ID
        """
        logger.info(f"Adding user {user_id} to group {group_id}")
        
        await self._request("POST", f"permissions/membership", json={
            "user_id": user_id,
            "group_id": group_id
        })
    
    async def remove_user_from_group(self, membership_id: int) -> None:
        """Remove a user from a permission group."""
        logger.info(f"Removing membership {membership_id}")
        await self._request("DELETE", f"permissions/membership/{membership_id}")
    
    # ==================== Database Management ====================
    
    async def add_database(
        self, 
        name: str, 
        engine: str, 
        host: str, 
        port: int, 
        dbname: str, 
        user: str, 
        password: str
    ) -> Dict:
        """
        Add a database connection to Metabase.
        
        Args:
            name: Database display name
            engine: Database engine (e.g., 'postgres')
            host: Database host
            port: Database port
            dbname: Database name
            user: Database user
            password: Database password
            
        Returns:
            Created database data
        """
        logger.info(f"Adding database: {name}")
        
        db_data = {
            "name": name,
            "engine": engine,
            "details": {
                "host": host,
                "port": port,
                "dbname": dbname,
                "user": user,
                "password": password,
                "ssl": False,
                "tunnel-enabled": False
            },
            "auto_run_queries": True,
            "is_full_sync": True,
            "schedules": {
                "metadata_sync": {
                    "schedule_type": "hourly"
                },
                "cache_field_values": {
                    "schedule_type": "daily"
                }
            }
        }
        
        return await self._request("POST", "database", json=db_data)
    
    async def list_databases(self) -> List[Dict]:
        """List all databases."""
        response = await self.client.get("/api/database")
        if response.status_code == 200:
            return response.json()
        return []
    
    async def sync_database(self, database_id: int) -> None:
        """Trigger database schema sync."""
        logger.info(f"Syncing database: {database_id}")
        await self._request("POST", f"database/{database_id}/sync_schema")
    
    # ==================== Dashboard Management ====================
    
    async def create_dashboard(self, name: str, collection_id: int, description: str = "") -> Dict:
        """
        Create a new dashboard in a collection.
        
        Args:
            name: Dashboard name
            collection_id: Collection ID
            description: Dashboard description
            
        Returns:
            Created dashboard data
        """
        logger.info(f"Creating dashboard: {name} in collection {collection_id}")
        
        return await self._request("POST", "dashboard", json={
            "name": name,
            "description": description,
            "collection_id": collection_id
        })
    
    async def get_dashboard(self, dashboard_id: int) -> Dict:
        """Get dashboard details."""
        return await self._request("GET", f"dashboard/{dashboard_id}")
    
    async def list_dashboards(self, collection_id: Optional[int] = None) -> List[Dict]:
        """List dashboards, optionally filtered by collection."""
        params = {}
        if collection_id is not None:
            params["collection"] = collection_id
            
        return await self._request("GET", "dashboard", params=params)
    
    # ==================== Embedding ====================
    
    def generate_embedding_token(
        self, 
        resource: Dict[str, Any], 
        params: Dict[str, Any] = None,
        exp_minutes: int = 10
    ) -> str:
        """
        Generate a signed JWT token for embedding.
        
        Args:
            resource: Resource to embed (e.g., {"dashboard": 123})
            params: Parameters for the embedded resource
            exp_minutes: Token expiration in minutes
            
        Returns:
            Signed JWT token
        """
        payload = {
            "resource": resource,
            "params": params or {},
            "exp": int(time.time()) + (exp_minutes * 60)
        }
        
        token = jwt.encode(payload, self.embedding_secret, algorithm="HS256")
        return token
    
    def get_embedded_dashboard_url(self, dashboard_id: int, params: Dict[str, Any] = None) -> str:
        """
        Get the full embedded URL for a dashboard.
        
        Args:
            dashboard_id: Dashboard ID
            params: Parameters for filtering the dashboard
            
        Returns:
            Full embedded URL
        """
        token = self.generate_embedding_token(
            resource={"dashboard": dashboard_id},
            params=params or {}
        )
        
        # Note: Frontend should use localhost:3000, but we return the path
        return f"/embed/dashboard/{token}"
    
    def get_embedded_collection_url(self, collection_id: int) -> str:
        """
        Get the embedded URL for a collection.
        
        Args:
            collection_id: Collection ID
            
        Returns:
            Collection URL path
        """
        token = self.generate_embedding_token(
            resource={"collection": collection_id}
        )
        
        return f"/embed/collection/{token}"
    
    # ==================== Setup & Health ====================
    
    async def check_health(self) -> bool:
        """Check if Metabase is healthy."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
    
    async def get_setup_token(self) -> Optional[str]:
        """Get setup token if Metabase is not yet set up."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/session/properties")
                if response.status_code == 200:
                    data = response.json()
                    return data.get("setup-token")
        except Exception as e:
            logger.error(f"Error getting setup token: {str(e)}")
        return None
    
    async def setup_metabase(self, admin_email: str, admin_password: str, first_name: str = "Admin", last_name: str = "User") -> Dict:
        """
        Complete initial Metabase setup.
        
        Args:
            admin_email: Admin email
            admin_password: Admin password
            first_name: Admin first name
            last_name: Admin last name
            
        Returns:
            Setup response
        """
        setup_token = await self.get_setup_token()
        
        if not setup_token:
            logger.info("Metabase is already set up")
            return {"status": "already_setup"}
        
        logger.info("Setting up Metabase for the first time")
        
        setup_data = {
            "token": setup_token,
            "user": {
                "first_name": first_name,
                "last_name": last_name,
                "email": admin_email,
                "password": admin_password,
                "site_name": "Metabase Analytics"
            },
            "database": None,
            "invite": None,
            "prefs": {
                "site_name": "Metabase Analytics",
                "allow_tracking": False
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/setup",
                    json=setup_data
                )
                
                if response.status_code == 200:
                    logger.info("Metabase setup completed successfully")
                    return response.json()
                else:
                    logger.error(f"Setup failed: {response.status_code} - {response.text}")
                    raise Exception(f"Setup failed: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error during Metabase setup: {str(e)}")
            raise