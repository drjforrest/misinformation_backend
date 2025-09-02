# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Community Resilience & Social Capital Analysis Platform that studies supportive digital health ecosystems within immigrant communities on Reddit. The platform combines social network analysis, community resilience measurement, and health information quality assessment to understand how communities support each other's health and wellbeing, multilingual content processing, and semantic embeddings using PostgreSQL with pgvector.

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

# Run automated collection (default behavior)
python scripts/automated_collection.py

# Run with specific options
python scripts/automated_collection.py --collect          # Explicit collection
python scripts/automated_collection.py --health-check     # Health check only
python scripts/automated_collection.py --report 7         # Generate 7-day aggregate report
python scripts/automated_collection.py --report 30        # Generate monthly report
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

# Launch community resilience analysis interface
python launch_community_resilience.py

# Launch research annotation interface (with expertise tracking)
python launch_research_annotation.py
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
- `health_info_quality.py` - Community-shared health information quality assessment
- `research_expertise_tracker.py` - Research team expertise development tracking

**Interface Layer**
- `gradio_app/enhanced_annotation_interface.py` - Full-featured research annotation UI
- `gradio_app/analytics_dashboard_interface.py` - Analytics dashboard interface
- `gradio_app/research_analytics_interface.py` - Research-grade investigational tools
- `gradio_app/community_resilience_interface.py` - Community resilience & social capital analysis

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
- Community resilience measurement and analysis
- Peer support pattern identification
- Knowledge broker discovery and analysis
- Health information quality assessment
- Cultural adaptation of health information analysis
- Network analysis of supportive relationships
- Research team expertise development tracking
- Real-time analytics dashboard
- Automated data collection with cron support

**Research Expertise Domains Tracked**
- **Peer Support Analysis** - Identifying mutual aid networks and support patterns
- **Knowledge Broker Identification** - Finding community knowledge leaders and influencers  
- **Cultural Bridging Analysis** - Understanding cross-cultural health information adaptation
- **Health Information Quality Assessment** - Evaluating helpfulness of community-shared health info
- **LGBTQ+ Health Communities** - Specialized analysis of gay men's health communities
- **Newcomer Community Resilience** - Immigrant/refugee health community dynamics
- **Multilingual Analysis** - Cross-language community resilience patterns
- **Network Analysis** - Technical social network analysis and visualization
- **Qualitative Analysis** - Deep qualitative analysis of community interactions
- **Community-Based Participatory Research** - Engaging communities as research partners

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