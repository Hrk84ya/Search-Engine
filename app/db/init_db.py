"""Database initialization — creates tables and pgvector extension."""

from sqlalchemy import text
from app.db.session import engine, Base
from app.core.logging import logger


async def init_database():
    """Create pgvector extension and all tables."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector extension ensured")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
