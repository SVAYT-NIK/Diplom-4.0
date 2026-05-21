"""
FastAPI application for heat consumption analytics.
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from backend.config.settings import settings
from backend.services.db import init_db, engine


# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=settings.log_level,
)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up application")
    
    # Ensure data directory exists
    data_dir = Path(settings.db_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized", db_path=settings.db_path)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Dispose database engine
    await engine.dispose()


app = FastAPI(
    title="Heat Analytics API",
    description="Система анализа теплопотребления многоквартирных домов (МКД)",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "db_path": settings.db_path}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Heat Analytics API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


# Import routers after app creation to avoid circular imports
from backend.routers import upload, analysis, results, buildings, export

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(results.router, prefix="/api", tags=["Results"])
app.include_router(buildings.router, prefix="/api", tags=["Buildings"])
app.include_router(export.router, prefix="/api", tags=["Export"])
