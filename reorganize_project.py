#!/usr/bin/env python3
"""
Project Reorganization Script
Separates demo/proof-of-concept files from production components
"""

import os
import shutil
from pathlib import Path
import json


def create_directories():
    """Create necessary directory structure"""
    directories = [
        "demo",
        "demo/sample_data",
        "logs",
        "data/production",  # Keep production data separate
        "docs/research",  # Research documentation
    ]

    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")


def move_demo_files():
    """Move demo and proof-of-concept files to demo directory"""
    demo_files = [
        "proof_of_concept.py",
        "demo_data_generator.py",
        "demo_visualizations.py",
        "demo_summary_report.txt",
    ]

    for file_name in demo_files:
        if os.path.exists(file_name):
            shutil.move(file_name, f"demo/{file_name}")
            print(f"📁 Moved {file_name} to demo/")
        else:
            print(f"⚠️  File not found: {file_name}")


def move_demo_data():
    """Move demo data files to demo/sample_data"""
    data_dir = Path("data")

    if data_dir.exists():
        for data_file in data_dir.glob("demo_*.json"):
            dest = f"demo/sample_data/{data_file.name}"
            shutil.move(str(data_file), dest)
            print(f"📁 Moved {data_file.name} to demo/sample_data/")

        for data_file in data_dir.glob("poc_*.json"):
            dest = f"demo/sample_data/{data_file.name}"
            shutil.move(str(data_file), dest)
            print(f"📁 Moved {data_file.name} to demo/sample_data/")


def update_main_imports():
    """Update import statements in main.py for demo files"""
    main_file = "main.py"

    if not os.path.exists(main_file):
        print(f"⚠️  {main_file} not found")
        return

    with open(main_file, "r") as f:
        content = f.read()

    # Update import path for proof_of_concept
    updated_content = content.replace(
        "from proof_of_concept import run_proof_of_concept",
        "from demo.proof_of_concept import run_proof_of_concept",
    )

    # Add import handling in case the old import is used elsewhere
    if "import proof_of_concept" in updated_content:
        updated_content = updated_content.replace(
            "import proof_of_concept", "from demo import proof_of_concept"
        )

    with open(main_file, "w") as f:
        f.write(updated_content)

    print("✅ Updated import paths in main.py")


def create_demo_init():
    """Create __init__.py in demo directory for proper imports"""
    init_content = '''"""
Demo and proof-of-concept components for the Health Misinformation Detection Platform

This directory contains demonstration scripts and sample data used for:
- Quick functionality testing (proof_of_concept.py)
- Sample data generation (demo_data_generator.py) 
- Visualization examples (demo_visualizations.py)

These components are useful for:
- Onboarding new researchers
- Testing system functionality
- Generating sample datasets for development
"""
'''

    with open("demo/__init__.py", "w") as f:
        f.write(init_content)

    print("✅ Created demo/__init__.py")


def create_project_summary():
    """Create a summary of the reorganized project structure"""
    structure = {
        "production_components": {
            "description": "Ready for real research data collection and analysis",
            "files": {
                "main.py": "Primary CLI interface with database integration",
                "start.py": "Automated setup and initialization script",
                "src/": {
                    "reddit_scraper.py": "Reddit API data collection with PRAW",
                    "database_models.py": "Complete research-grade database schema",
                    "data_persistence.py": "SQLAlchemy database persistence",
                    "network_analysis.py": "Social network analysis with NetworkX",
                    "database_setup.py": "Database initialization and management",
                    "embeddings_manager.py": "Semantic analysis capabilities",
                },
                "gradio_app/": {
                    "enhanced_annotation_interface.py": "Full research annotation system",
                    "annotation_interface.py": "Basic annotation interface (fallback)",
                },
                "config/settings.py": "Environment-based configuration",
                "alembic/": "Database migration management",
            },
        },
        "demo_components": {
            "description": "Testing, demonstration, and onboarding tools",
            "files": {
                "demo/proof_of_concept.py": "Quick functionality demonstration",
                "demo/demo_data_generator.py": "Synthetic data for testing",
                "demo/demo_visualizations.py": "Sample visualization examples",
                "demo/sample_data/": "Generated demo datasets",
            },
        },
        "ready_for_production": {
            "data_collection": "✅ Real Reddit API integration",
            "database_persistence": "✅ PostgreSQL with research schema",
            "network_analysis": "✅ Complete social network analysis",
            "human_annotation": "✅ Gamified research interface",
            "configuration": "✅ Environment-based settings",
            "migrations": "✅ Database versioning with Alembic",
        },
        "next_steps": [
            "Set up Reddit API credentials in .env",
            "Run 'python start.py' to initialize database",
            "Start real data collection with 'python main.py collect-db'",
            "Launch research annotation interface",
            "Begin systematic research data collection",
        ],
    }

    with open("PROJECT_STATUS.json", "w") as f:
        json.dump(structure, f, indent=2)

    print("✅ Created PROJECT_STATUS.json summary")


def main():
    """Execute the reorganization process"""
    print("🚀 Starting project reorganization...")
    print("=" * 50)

    # Check if we're in the right directory
    if not os.path.exists("src") or not os.path.exists("config"):
        print("❌ Error: Run this script from the project root directory")
        print("   Expected to find 'src/' and 'config/' directories")
        return

    try:
        # Step 1: Create directory structure
        print("\n📁 Creating directory structure...")
        create_directories()

        # Step 2: Move demo files
        print("\n📦 Moving demo files...")
        move_demo_files()
        move_demo_data()

        # Step 3: Update imports
        print("\n🔧 Updating imports...")
        update_main_imports()
        create_demo_init()

        # Step 4: Create documentation
        print("\n📋 Creating project documentation...")
        create_project_summary()

        print("\n" + "=" * 50)
        print("✅ PROJECT REORGANIZATION COMPLETE!")
        print("\n🎯 Your project is now organized with:")
        print("   📁 demo/ - Proof-of-concept and testing components")
        print("   🏭 src/ - Production-ready research infrastructure")
        print("   📊 gradio_app/ - Research annotation interfaces")
        print("   ⚙️  config/ - Configuration management")
        print("   🗄️  alembic/ - Database migrations")
        print("\n🚀 Ready for real data collection!")
        print("   Next: Run 'python start.py' to initialize your research database")

    except Exception as e:
        print(f"\n❌ Error during reorganization: {e}")
        print("Please check the error and try again.")


if __name__ == "__main__":
    main()
