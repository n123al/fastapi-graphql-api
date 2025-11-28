"""
GraphQL Queries Module.

This module exports all GraphQL query resolver classes for unified import.
Each query class is responsible for handling specific entity-related queries.
"""

from app.graphql.queries.system_queries import SystemQueries
from app.graphql.queries.user_queries import UserQueries

__all__ = ["UserQueries", "SystemQueries"]
