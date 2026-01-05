"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.observability.logger import configure_logging, get_logger

# Configure logging
configure_logging(log_level=settings.log_level.upper())
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        environment=settings.environment,
        log_level=settings.log_level,
    )

    # Initialize Sentry if DSN is provided
    if settings.sentry_dsn:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=1.0 if settings.environment == "development" else 0.1,
        )
        logger.info("sentry_initialized")

    # Set up LangSmith tracing
    if settings.langchain_tracing_v2 and settings.langchain_api_key:
        import os

        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
        logger.info("langsmith_tracing_enabled", project=settings.langchain_project)

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title="AgentOps Studio",
    description="Production-grade LLM agent orchestration for value proposition extraction",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["workflows"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "AgentOps Studio",
        "version": "0.1.0",
        "description": "Production LLM agent orchestration",
        "docs": "/docs",
        "health": "/api/v1/health",
        "metrics": "/api/v1/metrics",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.environment == "development",
    )
