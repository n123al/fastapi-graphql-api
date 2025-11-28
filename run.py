"""
FastAPI GraphQL API with MongoDB
A comprehensive, object-oriented API with authentication and authorization.
"""

import uvicorn
import structlog
from app.main import app
from app.core.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def main():
    """Main entry point for the application."""
    try:
        logger.info(
            "Starting FastAPI GraphQL API",
            app_name=settings.APP_NAME,
            version="1.0.0",
            debug=settings.DEBUG,
            host=settings.HOST,
            port=settings.PORT
        )
        
        uvicorn.run(
            "app.main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="info",
            access_log=True,
            use_colors=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error("Application failed to start", error=str(e))
        raise


if __name__ == "__main__":
    main()