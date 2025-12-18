from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Dict, List, Optional, cast

import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.core.config import settings
from app.core.constants import (
    DEFAULT_GROUPS,
    DEFAULT_PERMISSIONS,
    DEFAULT_ROLES,
    MONGODB_SETTINGS,
)
from app.core.exceptions import DatabaseError

logger = structlog.get_logger()


class MotorDatabaseManager:
    """MongoDB database manager using Motor driver for native performance."""

    def __init__(self) -> None:
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.is_connected = False
        self.repositories: Dict[str, Any] = {}

    async def connect(self) -> None:
        """Connect to MongoDB with Motor driver."""
        try:
            logger.info("Connecting to MongoDB with Motor driver...")

            # Create MongoDB client with advanced connection pool settings
            client_kwargs = {
                "maxPoolSize": MONGODB_SETTINGS["MAX_CONNECTION_POOL_SIZE"],
                "minPoolSize": MONGODB_SETTINGS["MIN_CONNECTION_POOL_SIZE"],
                "maxIdleTimeMS": MONGODB_SETTINGS["MAX_IDLE_TIME_MS"],
                "maxConnecting": 5,
                "retryWrites": MONGODB_SETTINGS["RETRY_WRITES"],
                "retryReads": MONGODB_SETTINGS["RETRY_READS"],
                "socketTimeoutMS": MONGODB_SETTINGS["SOCKET_TIMEOUT_MS"],
                "connectTimeoutMS": MONGODB_SETTINGS["CONNECT_TIMEOUT_MS"],
                "serverSelectionTimeoutMS": MONGODB_SETTINGS[
                    "SERVER_SELECTION_TIMEOUT_MS"
                ],
                "waitQueueTimeoutMS": MONGODB_SETTINGS["WAIT_QUEUE_TIMEOUT_MS"],
            }

            if settings.MONGODB_URL.startswith("mongodb+srv://"):
                client_kwargs["tls"] = True
                client_kwargs["directConnection"] = False

            # Ensure datetimes are timezone-aware
            client_kwargs["tz_aware"] = True

            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL, **cast(Dict[str, Any], client_kwargs)
            )

            self.database = self.client[settings.DATABASE_NAME]

            # Test connection
            await self.client.admin.command("ping")

            self.is_connected = True
            logger.info(
                "MongoDB connected successfully with Motor driver",
                database=settings.DATABASE_NAME,
            )

            # Initialize repositories (temporarily disabled for testing)
            # await self._initialize_repositories()

            # Create default data (temporarily disabled for testing)
            # await self._create_default_data()

            # Create indexes (temporarily disabled for testing)
            # await self._create_indexes()

        except Exception as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB disconnected")

    async def ping(self) -> bool:
        """Ping the database to check connectivity."""
        if not self.client:
            self.is_connected = False
            return False

        try:
            await self.client.admin.command("ping")
            self.is_connected = True
            return True
        except Exception:
            self.is_connected = False
            return False

    async def check_health(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "connected": False,
            "latency_ms": None,
            "query_ok": False,
            "error": None,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        start = perf_counter()
        if not self.client:
            self.is_connected = False
            result["error"] = "client_not_initialized"
            result["latency_ms"] = int((perf_counter() - start) * 1000)
            result["checked_at"] = datetime.now(timezone.utc).isoformat()
            return result
        try:
            await self.client.admin.command("ping")
            result["latency_ms"] = int((perf_counter() - start) * 1000)
            self.is_connected = True
            result["connected"] = True
            if self.database is not None:
                try:
                    await self.database.command({"ping": 1})
                    result["query_ok"] = True
                except Exception as qe:
                    result["query_ok"] = False
                    result["error"] = str(qe)
            result["checked_at"] = datetime.now(timezone.utc).isoformat()
            return result
        except Exception as e:
            self.is_connected = False
            result["latency_ms"] = int((perf_counter() - start) * 1000)
            result["error"] = str(e)
            result["checked_at"] = datetime.now(timezone.utc).isoformat()
            return result

    async def _initialize_repositories(self) -> None:
        """Initialize all repositories."""
        from app.data import (
            GroupRepository,
            PermissionRepository,
            RoleRepository,
            UserRepository,
        )

        self.repositories = {
            "users": UserRepository(),
            "roles": RoleRepository(),
            "permissions": PermissionRepository(),
            "groups": GroupRepository(),
        }

        logger.info("Repositories initialized", count=len(self.repositories))

    async def _create_default_data(self) -> None:
        """Create default permissions, roles, and groups."""
        try:
            logger.info("Creating default data...")

            # Create default permissions
            await self._create_default_permissions()

            # Create default roles
            await self._create_default_roles()

            # Create default groups
            await self._create_default_groups()

            logger.info("Default data created successfully")

        except Exception as e:
            logger.error("Failed to create default data", error=str(e))
            # Don't raise here, as this is not critical for startup

    async def _create_default_permissions(self) -> None:
        """Create default permissions if they don't exist."""
        permission_repo = self.repositories["permissions"]

        for perm_name, description in DEFAULT_PERMISSIONS.items():
            existing = await permission_repo.get_by_name(perm_name)
            if not existing:
                permission_data = {"name": perm_name, "description": description}
                await permission_repo.create(permission_data)
                logger.debug("Created default permission", name=perm_name)

    async def _create_default_roles(self) -> None:
        """Create default roles if they don't exist."""
        role_repo = self.repositories["roles"]
        permission_repo = self.repositories["permissions"]

        for role_name, role_data in DEFAULT_ROLES.items():
            existing = await role_repo.get_by_name(role_name)
            if not existing:
                # Get permissions for this role
                permissions = []
                for perm_name in cast(List[str], role_data["permissions"]):
                    perm = await permission_repo.get_by_name(perm_name)
                    if perm:
                        permissions.append(perm["_id"])

                role_dict = {
                    "name": role_name,
                    "description": role_data["description"],
                    "permissions": permissions,
                    "is_system_role": role_data.get("is_system_role", False),
                    "is_active": True,
                }

                await role_repo.create(role_dict)
                logger.debug(
                    "Created default role",
                    name=role_name,
                    permission_count=len(permissions),
                )

    async def _create_default_groups(self) -> None:
        """Create default groups if they don't exist."""
        group_repo = self.repositories["groups"]

        for group_name, group_data in DEFAULT_GROUPS.items():
            existing = await group_repo.get_by_name(group_name)
            if not existing:
                group_dict = {
                    "name": group_name,
                    "description": group_data["description"],
                    "is_system_group": group_data.get("is_system_group", False),
                    "is_active": True,
                    "metadata": group_data.get("metadata", {}),
                }

                await group_repo.create(group_dict)
                logger.debug("Created default group", name=group_name)

    async def _create_indexes(self) -> None:
        """Create database indexes for all collections."""
        try:
            logger.info("Creating database indexes...")

            for repo_name, repository in self.repositories.items():
                await repository.create_indexes()
                logger.debug("Created indexes for collection", collection=repo_name)

            logger.info("Database indexes created successfully")

        except Exception as e:
            logger.error("Failed to create indexes", error=str(e))

    def get_repository(self, collection_name: str) -> Any:
        """Get repository for a collection."""
        return self.repositories.get(collection_name)

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        if self.database is None:
            return {}

        try:
            stats = {}
            collections = ["users", "roles", "permissions", "groups"]

            for collection_name in collections:
                try:
                    collection = self.database[collection_name]
                    count = await collection.estimated_document_count()
                    stats[collection_name] = {
                        "count": count,
                        "indexes": len(await collection.list_indexes().to_list(None)),
                    }
                except Exception as e:
                    logger.warning(
                        f"Failed to get stats for {collection_name}", error=str(e)
                    )
                    stats[collection_name] = {"count": 0, "indexes": 0}

            return stats
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {}

    async def execute_command(self, command: Dict[str, Any]) -> Any:
        """Execute a MongoDB command."""
        try:
            if self.database is None:
                raise DatabaseError("Database connection not available")
            return await self.database.command(command)
        except Exception as e:
            logger.error("Failed to execute command", command=command, error=str(e))
            raise DatabaseError(f"Failed to execute command: {str(e)}")

    async def get_server_status(self) -> Dict[str, Any]:
        """Get MongoDB server status."""
        try:
            return cast(Dict[str, Any], await self.execute_command({"serverStatus": 1}))
        except Exception as e:
            logger.error("Failed to get server status", error=str(e))
            return {"error": str(e)}


# Global Motor database manager instance
motor_db_manager = MotorDatabaseManager()


# Convenience functions
async def init_db() -> None:
    """Initialize database connection."""
    await motor_db_manager.connect()


async def close_db() -> None:
    """Close database connection."""
    await motor_db_manager.disconnect()


async def get_db_stats() -> Dict[str, Any]:
    """Get database statistics."""
    return await motor_db_manager.get_collection_stats()


def get_repository(collection_name: str) -> Any:
    """Get repository for a collection."""
    return motor_db_manager.get_repository(collection_name)
