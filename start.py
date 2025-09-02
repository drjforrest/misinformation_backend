#!/usr/bin/env python3

"""
Quick start script for Health Misinformation Research Platform
Handles all initialization and setup automatically
"""

import os
import sys
import subprocess


def check_python_version():
    """Ensure Python 3.8+ is being used"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")


def check_virtual_environment():
    """Check if running in virtual environment"""
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("⚠️  Not running in a virtual environment")
        print("💡 Recommended: python -m venv venv && source venv/bin/activate")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != "y":
            sys.exit(1)
    else:
        print("✅ Virtual environment detected")


def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=True,
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try: pip install -r requirements.txt")
        sys.exit(1)


def setup_environment():
    """Set up environment variables"""
    if not os.path.exists(".env"):
        print("📄 Creating .env file from template...")

        if os.path.exists(".env.example"):
            import shutil

            shutil.copy(".env.example", ".env")
            print("✅ .env created - please update with your API credentials")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file exists")

    return True


def initialize_database():
    """Initialize PostgreSQL database with pgvector"""
    print("🗄️  Initializing database...")

    try:
        # Import and run database setup
        from src.database_setup import DatabaseManager

        db_manager = DatabaseManager()
        success = db_manager.initialize_database()

        if success:
            print("✅ Database initialized successfully")
            return True
        else:
            print("❌ Database initialization failed")
            return False

    except ImportError as e:
        print(f"❌ Failed to import database setup: {e}")
        print("💡 Make sure dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False


def run_demo():
    """Run a quick demonstration"""
    print("🎯 Running proof of concept...")

    try:
        subprocess.run([sys.executable, "proof_of_concept.py"], check=True)
        print("✅ Proof of concept completed!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Demo failed: {e}")
        print("💡 You may need to set up Reddit API credentials first")


def main():
    """Main initialization workflow"""
    print("🚀 Health Misinformation Research Platform - Quick Start")
    print("=" * 60)

    # Check system requirements
    check_python_version()
    check_virtual_environment()

    # Set up project
    if not setup_environment():
        sys.exit(1)

    install_dependencies()

    # Database setup
    db_success = initialize_database()

    if db_success:
        print("\n🎉 Setup Complete!")
        print("=" * 40)
        print("📋 Next steps:")
        print("   1. Update .env with your Reddit API credentials")
        print("   2. Run: python proof_of_concept.py")
        print("   3. Or: python main.py demo --limit 50")
        print(
            "   4. Launch annotation tool: python main.py annotate --data-path [data_file]"
        )
        print("")
        print("🔗 Useful commands:")
        print("   • Test database: python src/database_setup.py --test")
        print("   • Reset database: python src/database_setup.py --reset")
        print("   • Run migrations: alembic upgrade head")

        # Ask if they want to run demo
        if os.getenv("REDDIT_CLIENT_ID"):
            response = input("\n🎯 Run proof of concept demo now? (y/N): ")
            if response.lower() == "y":
                run_demo()
        else:
            print("\n💡 Set up Reddit API credentials in .env to run demos")

    else:
        print("\n❌ Setup incomplete - database initialization failed")
        print("💡 Check the logs above for specific error messages")
        sys.exit(1)


if __name__ == "__main__":
    main()
