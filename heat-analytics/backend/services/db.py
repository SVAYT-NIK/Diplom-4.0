"""
Database service for SQLAlchemy async operations.
"""
import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.sql import text

from backend.config.settings import settings
from backend.models.schemas import Base


logger = logging.getLogger(__name__)


# Create async engine
engine = create_async_engine(
    f"sqlite+aiosqlite:///{settings.db_path}",
    echo=settings.log_level == "DEBUG",
    future=True,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize database by creating all tables."""
    try:
        # Ensure parent directory exists
        db_path = Path(settings.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db() -> AsyncSession:
    """Get database session dependency."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Check database health by executing a simple query."""
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            await result.fetchone()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
