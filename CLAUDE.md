# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Health Misinformation Detection & Network Analysis Platform that detects and analyzes health misinformation within immigrant communities on Reddit. The platform combines social network analysis with human-validated machine learning, multilingual content processing, and semantic embeddings using PostgreSQL with pgvector.

## Key Commands

### Database Setup
```bash
# Initialize PostgreSQL database with pgvector support
./init_database.sh

# Run database migrations
alembic upgrade head

# Generate new migration after model changes
alembic revision --autogenerate -m "Description of changes"
```

### Data Collection
```bash
# Basic data collection (file-based)
python main.py demo --limit 50

# Full production data collection to database
python main.py collect-db

# Multilingual data collection with translation
python main.py multilingual-collect-db

# Test automated collection pipeline
python scripts/automated_collection.py
```

### Analysis and Visualization
```bash
# Run network analysis on collected data
python main.py analyze --data-path data/raw_reddit_data_[timestamp].json

# Launch annotation interface
python main.py annotate --data-path data/demo_data_[timestamp].json

# Launch analytics dashboard
python launch_dashboard.py

# Launch research-grade analytics interface
python launch_research_analytics.py
```

### Development and Testing
```bash
# Run translation service tests
python test_translation.py

# Quick proof of concept demo
python proof_of_concept.py

# Real data research demo
python real_data_research_demo.py
```

## Architecture Overview

### Core Components

**Data Collection Layer (`src/`)**
- `reddit_scraper.py` - Basic Reddit API integration
- `multilingual_scraper.py` - Advanced multilingual data collection with translation
- `translation_service.py` - Google Translate integration with caching

**Database Layer**
- `database_models.py` - SQLAlchemy models for posts, comments, annotations
- `database_models_vector.py` - pgvector-enabled models for semantic embeddings
- `data_persistence.py` - Database operations and persistence management
- `embeddings_manager.py` - Semantic embedding generation and storage

**Analysis Layer**
- `network_analysis.py` - NetworkX-based social network analysis
- `research_visualizations.py` - Data visualization and research outputs
- `analytics_dashboard.py` - Real-time analytics dashboard

**Interface Layer**
- `gradio_app/enhanced_annotation_interface.py` - Full-featured research annotation UI
- `gradio_app/analytics_dashboard_interface.py` - Analytics dashboard interface
- `gradio_app/research_analytics_interface.py` - Research-grade investigational tools

### Database Schema

The platform uses PostgreSQL with pgvector extension for semantic similarity search. Key models:
- `RedditPost` - Reddit posts with embeddings and ML analysis fields
- `RedditComment` - Comments with threading and analysis
- `HumanAnnotation` - Research annotations for training data
- `NetworkNode/NetworkEdge` - Social network graph storage

### Configuration Management

All configuration is handled through `config/settings.py` using environment variables:
- Reddit API credentials
- Database connection strings
- Translation service API keys
- Collection parameters and limits

## Key Features

**Multilingual Processing**
- Automatic language detection
- Translation caching to avoid API costs  
- Support for English, Tagalog, Mandarin, Cantonese, Punjabi, Spanish

**Semantic Analysis**
- pgvector integration for embedding storage
- Sentence transformers for semantic similarity
- Health keyword detection and classification

**Research Pipeline**
- Human annotation interface for training data
- Network analysis of information spread
- Real-time analytics dashboard
- Research-grade investigational tools with advanced search, pattern analysis, and intervention planning
- Automated data collection with cron support

## Development Notes

### Database Migrations
- Always run `alembic upgrade head` after pulling changes
- Generate migrations with descriptive messages
- Test migrations on a copy of production data first

### Reddit API Usage
- Respects rate limits automatically
- Uses file-based storage by default for development
- Database persistence available for production use
- Requires Reddit API credentials in `.env` file

### Data Ethics
- All data is anonymized
- No personal information is stored
- Compliance with Reddit Terms of Service
- Research Ethics Board approval required for deployment

### Testing Strategy
- Use demo modes with limited data for development
- Translation service has built-in caching to avoid API costs
- Database operations are logged for debugging
- Proof-of-concept scripts available for quick validation