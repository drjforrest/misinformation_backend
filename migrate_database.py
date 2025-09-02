#!/usr/bin/env python3
"""
Database migration script to add english_translation columns to existing tables
"""

from sqlalchemy import create_engine, text
from loguru import logger
from config.settings import Config


def migrate_database():
    """Add english_translation columns to existing tables"""

    engine = create_engine(Config.DATABASE_URL)

    migrations = [
        """
        ALTER TABLE reddit_posts 
        ADD COLUMN IF NOT EXISTS english_translation TEXT;
        """,
        """
        ALTER TABLE reddit_comments 
        ADD COLUMN IF NOT EXISTS english_translation TEXT;
        """,
    ]

    logger.info("Starting database migration...")

    with engine.connect() as conn:
        for i, migration in enumerate(migrations, 1):
            try:
                logger.info(f"Executing migration {i}/{len(migrations)}")
                conn.execute(text(migration))
                conn.commit()
                logger.info(f"✅ Migration {i} completed successfully")
            except Exception as e:
                logger.error(f"❌ Migration {i} failed: {e}")
                raise

    logger.info("✅ All database migrations completed successfully!")


if __name__ == "__main__":
    migrate_database()
