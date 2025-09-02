"""
Database management utilities for the Health Misinformation Platform
"""

import os
import subprocess
import sys
from loguru import logger
from sqlalchemy import create_engine, text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config.settings import Config


class DatabaseManager:
    """Handles database setup, migrations, and maintenance"""

    def __init__(self):
        self.db_url = Config.DATABASE_URL
        self.db_name = self.extract_db_name(self.db_url)

    def extract_db_name(self, db_url: str) -> str:
        """Extract database name from URL"""
        return db_url.split("/")[-1] if "/" in db_url else "misinformation_research"

    def check_postgresql_installed(self) -> bool:
        """Check if PostgreSQL is installed and accessible"""
        try:
            subprocess.run(["psql", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def check_pgvector_installed(self) -> bool:
        """Check if pgvector extension is available"""
        try:
            # Try to connect to postgres database to test
            engine = create_engine(self.db_url.replace(f"/{self.db_name}", "/postgres"))
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM pg_available_extensions WHERE name = 'vector'")
                )
                return result.rowcount > 0
        except Exception as e:
            logger.warning(f"Could not check pgvector availability: {e}")
            return False

    def create_database(self) -> bool:
        """Create the database if it doesn't exist"""
        try:
            # Connect to postgres database to create our target database
            connection_params = {
                "host": "localhost",
                "port": 5432,
                "user": os.getenv("USER", "postgres"),
                "database": "postgres",
            }

            conn = psycopg2.connect(**connection_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (self.db_name,),
            )

            if cursor.fetchone():
                logger.info(f"Database '{self.db_name}' already exists")
                return True

            # Create database
            cursor.execute(f'CREATE DATABASE "{self.db_name}"')
            logger.info(f"Created database '{self.db_name}'")

            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False

    def enable_pgvector(self) -> bool:
        """Enable pgvector extension in the database"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension enabled")
                return True
        except Exception as e:
            logger.error(f"Failed to enable pgvector: {e}")
            return False

    def test_pgvector(self) -> bool:
        """Test pgvector functionality"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                # Test basic vector operations
                result = conn.execute(text("SELECT '[1,2,3]'::vector"))
                vector_result = result.fetchone()

                # Test similarity
                result = conn.execute(
                    text("SELECT '[1,2,3]'::vector <=> '[1,2,4]'::vector AS distance")
                )
                distance_result = result.fetchone()

                logger.info(
                    f"pgvector test successful - distance: {distance_result[0]}"
                )
                return True

        except Exception as e:
            logger.error(f"pgvector test failed: {e}")
            return False

    def run_migrations(self) -> bool:
        """Run Alembic migrations"""
        try:
            # Generate migration if none exist
            result = subprocess.run(
                [
                    "alembic",
                    "revision",
                    "--autogenerate",
                    "-m",
                    "Initial schema with pgvector support",
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0 and "No changes detected" not in result.stdout:
                logger.warning(f"Migration generation: {result.stdout}")

            # Run migrations
            result = subprocess.run(
                ["alembic", "upgrade", "head"], capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info("Database migrations completed successfully")
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False

    def initialize_database(self) -> bool:
        """Complete database initialization process"""
        logger.info("Starting database initialization...")

        # Check prerequisites
        if not self.check_postgresql_installed():
            logger.error("PostgreSQL not installed. Run: brew install postgresql")
            return False

        # Create database
        if not self.create_database():
            return False

        # Enable pgvector
        if not self.enable_pgvector():
            logger.warning("pgvector not enabled - semantic search will be limited")

        # Test pgvector
        if self.test_pgvector():
            logger.info("✅ pgvector is working correctly!")

        # Run migrations
        if not self.run_migrations():
            return False

        logger.info("🎉 Database initialization complete!")
        logger.info(f"Connection string: {self.db_url}")

        return True


def main():
    """CLI entry point for database initialization"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(
            """
Database Initialization Tool

Usage:
    python src/database_setup.py                 # Initialize database
    python src/database_setup.py --test         # Test existing setup
    python src/database_setup.py --reset        # Reset database (careful!)

This tool will:
1. Create PostgreSQL database
2. Enable pgvector extension  
3. Run Alembic migrations
4. Test vector functionality
        """
        )
        return

    db_manager = DatabaseManager()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        logger.info("Testing database setup...")
        if db_manager.test_pgvector():
            logger.info("✅ Database and pgvector working correctly!")
        else:
            logger.error("❌ Database test failed")
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        logger.warning("⚠️  This will delete all data!")
        response = input("Are you sure? Type 'yes' to confirm: ")
        if response.lower() != "yes":
            logger.info("Reset cancelled")
            return

        # Drop and recreate database
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                user=os.getenv("USER", "postgres"),
                database="postgres",
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute(f'DROP DATABASE IF EXISTS "{db_manager.db_name}"')
            cursor.close()
            conn.close()
            logger.info("Database dropped")
        except Exception as e:
            logger.error(f"Failed to drop database: {e}")

    # Initialize database
    success = db_manager.initialize_database()

    if success:
        logger.info("🚀 Ready to collect data! Try:")
        logger.info("   python proof_of_concept.py")
        logger.info("   python main.py demo --limit 50")
    else:
        logger.error("❌ Database initialization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
