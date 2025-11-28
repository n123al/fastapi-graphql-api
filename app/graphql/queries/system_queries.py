"""
GraphQL query resolvers for system information and health checks.

This module contains all GraphQL query operations related to system status,
health checks, and general API information.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import strawberry

from app.core.motor_database import motor_db_manager


class SystemQueries:
    """
    GraphQL query resolvers for system-related operations.

    This class contains all query methods for retrieving system information,
    health status, and API metadata.
    """

    async def health(self) -> str:
        """
        Check the health status of the application and database connection.

        Returns:
            "healthy" if database is connected, "database_disconnected" otherwise

        Note:
            This is a basic health check that verifies database connectivity
        """
        return "healthy" if motor_db_manager.is_connected else "database_disconnected"

    async def info(self) -> str:
        """
        Get basic API information including database connection status.

        Returns:
            String containing API information and database status

        Note:
            Provides a quick overview of the API's current operational state
        """
        return f"FastAPI GraphQL API with Strawberry - Database: {'Connected' if motor_db_manager.is_connected else 'Disconnected'}"

    async def api_version(self) -> str:
        """
        Get the current API version.

        Returns:
            Current API version string
        """
        return "2.0.0"

    async def database_status(self) -> Dict[str, Any]:
        """
        Get detailed database connection status and statistics.

        Returns:
            Dictionary containing database connection status and basic statistics

        Note:
            Provides detailed information about database connectivity and collection counts
        """
        try:
            if not motor_db_manager.is_connected or motor_db_manager.database is None:
                return {"connected": False, "error": "Database not connected"}

            # Get collection names
            collections = await motor_db_manager.database.list_collection_names()
            collections = [col for col in collections if not col.startswith("system.")]

            # Get basic stats for each collection
            stats = {}
            for collection_name in collections:
                try:
                    count = await motor_db_manager.database[
                        collection_name
                    ].count_documents({})
                    stats[collection_name] = {"count": count, "status": "ok"}
                except Exception as e:
                    stats[collection_name] = {
                        "count": 0,
                        "status": "error",
                        "error": str(e),
                    }

            return {
                "connected": True,
                "database_name": motor_db_manager.database.name,
                "collections": collections,
                "collection_stats": stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            return {
                "connected": False,
                "error": f"Failed to get database status: {str(e)}",
            }

    async def system_status(self) -> str:
        """
        Get overall system status consistent with schema.
        Returns "healthy" when DB is connected, otherwise "database_disconnected".
        """
        return "healthy" if motor_db_manager.is_connected else "database_disconnected"
