"""Main application entry point for GenAI Learning Assistant."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse

from src import __version__
from src.api import router
from src.config import get_settings
from src.utils import setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging()

# Create FastAPI application
app = FastAPI(
    title="GenAI Learning Assistant",
    description="Production-ready GenAI Learning Assistant using AWS Bedrock AgentCore and Strand Agent",
    version=__version__,
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(router, prefix=settings.api_prefix)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API docs."""
    return RedirectResponse(url=f"{settings.api_prefix}/docs")


@app.on_event("startup")
async def startup_event() -> None:
    """Run on application startup."""
    from src.utils import get_logger

    logger = get_logger(__name__)
    logger.info(
        "Starting GenAI Learning Assistant",
        version=__version__,
        environment=settings.environment,
        api_prefix=settings.api_prefix,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Run on application shutdown."""
    from src.utils import get_logger

    logger = get_logger(__name__)
    logger.info("Shutting down GenAI Learning Assistant")


def main() -> None:
    """Run the application."""
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
