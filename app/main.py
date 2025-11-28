from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from strawberry.fastapi import GraphQLRouter
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, cast
import uvicorn
import structlog
from datetime import datetime, timezone

from app.core.config import settings
from app.core.motor_database import init_db, close_db, motor_db_manager
from app.core.security import SecurityManager, get_current_user
from app.core.exceptions import ApplicationError, AuthenticationError, AuthorizationError
from app.graphql.schema import create_graphql_schema


# Configure structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting FastAPI GraphQL API with Strawberry...")
    try:
        await init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        logger.warning("Continuing startup in degraded mode without database connection")
    try:
        await setup_graphql()
    except Exception as e:
        logger.error("Failed to setup GraphQL", error=str(e), exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    try:
        await close_db()
        logger.info("Application shut down successfully")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Clean FastAPI GraphQL API with Strawberry's built-in Playground",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(ApplicationError)
async def application_exception_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Handle application-specific exceptions."""
    logger.error("Application error occurred", error=exc.message, code=exc.code)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code,
                "details": exc.details
            }
        }
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning("Authentication error occurred", error=exc.message, code=exc.code)
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code
            }
        }
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle authorization errors."""
    logger.warning("Authorization error occurred", error=exc.message, code=exc.code)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning("HTTP exception occurred", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "code": f"HTTP_{exc.status_code}"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error("Unexpected error occurred", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An internal server error occurred",
                "code": "INTERNAL_ERROR"
            }
        }
    )


# Security manager
security_manager = SecurityManager()


async def get_graphql_context(request: Request) -> Dict[str, Any]:
    """Create GraphQL context compatible with Strawberry (dict-based)."""
    return {
        "request": request,
        "motor_db_manager": motor_db_manager,
        "security_manager": security_manager,
    }


# Setup GraphQL with Strawberry's built-in Playground
async def setup_graphql() -> None:
    """Setup GraphQL router with Strawberry's built-in GraphiQL Playground."""
    try:
        logger.info("Setting up GraphQL...")
        logger.info(f"Motor DB Manager connected: {motor_db_manager.is_connected}")
        logger.info(f"Motor DB Manager database: {motor_db_manager.database}")
        
        # Create GraphQL schema using the new modular structure
        schema = await create_graphql_schema()
        
        # Create GraphQL router with Strawberry's built-in GraphiQL (Playground)
        graphql_app: GraphQLRouter = GraphQLRouter(
            schema,
            path="/graphql",
            graphiql=True,
            allow_queries_via_get=True,
            context_getter=cast(Any, get_graphql_context),
        )
        
        # Include the GraphQL router
        app.include_router(graphql_app, prefix="/api")
        
        logger.info("GraphQL setup completed with Strawberry's built-in GraphiQL Playground")
        logger.info(f"Visit http://{settings.HOST}:{settings.PORT}/api/graphql to access the GraphQL Playground")
        
    except Exception as e:
        logger.error("Failed to setup GraphQL", error=str(e), exc_info=True)
        raise


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": ["strawberry_graphql", "motor_driver", "graphiql_playground"]
    }


@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with database connectivity."""
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": {
            "strawberry_graphql": "enabled",
            "motor_driver": "enabled",
            "graphiql_playground": "enabled",
            "database_connected": False
        },
        "services": {
            "api": "healthy",
            "database": "unknown"
        }
    }
    
    try:
        db_health = await motor_db_manager.check_health()
        health_status["features"]["database_connected"] = db_health.get("connected", False)
        health_status["database_health"] = db_health
        latency = db_health.get("latency_ms") or 0
        if db_health.get("connected") and db_health.get("query_ok"):
            if latency >= 800:
                health_status["services"]["database"] = "degraded"
                health_status["status"] = "degraded"
            else:
                health_status["services"]["database"] = "healthy"
                try:
                    stats = await motor_db_manager.get_collection_stats()
                    health_status["database_stats"] = stats
                except Exception as stats_error:
                    logger.warning("Failed to get database stats", error=str(stats_error))
        else:
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "unhealthy" if db_health.get("error") else "degraded"
    except Exception as e:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "unhealthy"
        health_status["features"]["database_connected"] = False
        logger.error("Database health check failed", error=str(e))
    
    return health_status


# API information endpoint
@app.get("/api/info")
async def api_info() -> Dict[str, Any]:
    """Get comprehensive API information."""
    db_connected = motor_db_manager.is_connected
    collections = []
    
    if db_connected and motor_db_manager.database is not None:
        try:
            collections = await motor_db_manager.database.list_collection_names()
            collections = [col for col in collections if not col.startswith("system.")]
        except Exception:
            collections = []
    
    return {
        "name": settings.APP_NAME,
        "version": "2.0.0",
        "description": "Clean FastAPI GraphQL API with Strawberry's built-in GraphiQL Playground",
        "features": [
            "Strawberry GraphQL with Built-in GraphiQL",
            "MongoDB Motor Driver",
            "JWT Authentication",
            "Role-Based Authorization",
            "User Management",
            "Permission System",
            "Group Management",
            "Real-time Subscriptions"
        ],
        "technology_stack": {
            "framework": "FastAPI",
            "database": "MongoDB with Motor driver",
            "graphql": "Strawberry GraphQL",
            "authentication": "JWT",
            "orm_pattern": "Repository Pattern with Motor"
        },
        "authentication": {
            "type": "JWT",
            "algorithm": settings.ALGORITHM,
            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_MINUTES // (60 * 24),
            "strategies": ["username_password", "email"]
        },
        "database": {
            "type": "MongoDB",
            "driver": "Motor (async)",
            "name": settings.DATABASE_NAME,
            "connected": db_connected,
            "collections": collections,
            "dynamic_schema": True
        },
        "graphql": {
            "endpoint": "/api/graphql",
            "playground": "/api/graphql (Strawberry GraphiQL)",
            "schema_generation": "strawberry_auto",
            "introspection": True,
            "subscriptions": True,
            "ide": "GraphiQL (Strawberry built-in)"
        },
        "endpoints": {
            "graphql": "/api/graphql",
            "playground": "/api/graphql (GraphiQL interface)",
            "health": "/health",
            "detailed_health": "/health/detailed",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with welcome information."""
    return {
        "message": "Welcome to FastAPI GraphQL API with Strawberry's built-in GraphiQL",
        "version": "2.0.0",
        "features": [
            "Strawberry GraphQL with Built-in GraphiQL Playground",
            "MongoDB Motor Driver",
            "JWT Authentication",
            "Role-Based Authorization"
        ],
        "endpoints": {
            "graphql": "/api/graphql",
            "playground": "/api/graphql (Strawberry GraphiQL)",
            "docs": "/docs",
            "health": "/health",
            "info": "/api/info"
        },
        "note": "Visit http://localhost:8000/api/graphql to access Strawberry's built-in GraphiQL Playground"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    )