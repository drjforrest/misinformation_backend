# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a health misinformation detection and network analysis platform designed to identify and analyze health misinformation within immigrant communities on Reddit. The system combines social network analysis with human-validated machine learning to create an early warning system for public health agencies.

## Core Architecture

The platform follows a modular architecture with four main components:

1. **Data Collection Engine** (`src/reddit_scraper.py`): PRAW-based Reddit API integration that targets specific subreddits and health keywords
2. **Network Analysis Engine** (`src/network_analysis.py`): NetworkX-based social network mapping and centrality analysis
3. **Human Annotation Interface** (`gradio_app/annotation_interface.py`): Gamified Gradio interface for researchers to validate content
4. **Database Layer** (`src/database_models.py`): SQLAlchemy models for storing posts, comments, annotations, and network metrics

## Development Setup

### Prerequisites
- Python 3.12+ (per user requirements)
- Reddit API credentials
- Optional: PostgreSQL database (falls back to SQLite)

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with Reddit API credentials from https://www.reddit.com/prefs/apps
```

### Reddit API Setup
Create a script-type application at https://www.reddit.com/prefs/apps and add credentials to `.env`:
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`

## Common Commands

### Data Collection
```bash
# Quick demo with limited data
python main.py demo --limit 50

# Full data collection from all target subreddits
python main.py collect

# Proof of concept demonstration
python proof_of_concept.py
```

### Analysis
```bash
# Run network analysis on collected data
python main.py analyze --data-path data/raw_reddit_data_[timestamp].json

# Launch human annotation interface
python main.py annotate --data-path data/demo_data_[timestamp].json
```

## Target Data Sources

### Subreddits Monitored
- **LGBTQ+ Health**: `askgaybros`, `gay_irl`, `gaybros`, `lgbt`, `ainbow`
- **Canadian Cities**: `toronto`, `vancouver`, `askTO`, `canada`, `torontogaybros`
- **Newcomer Communities**: `NewToCanada`, `ImmigrationCanada`, `immigrationlaw`

### Health Keywords Tracked
- **Primary**: HIV, PrEP, ARVs, syphilis, doxy, PEP, chlamydia, gonorrhoea
- **Colloquial**: "the clap", "burning", Truvada, Descovy, "undetectable"
- **Target Languages**: English, Tagalog, Mandarin/Cantonese, Punjabi, Spanish

## Configuration System

Configuration is centralized in `config/settings.py` with three main classes:

- **Config**: Core application settings (API keys, database URLs, logging)
- **ResearchConfig**: Research-specific settings (target subreddits, keywords, languages)
- **AnnotationConfig**: Human annotation settings (categories, gamification)

Environment variables override defaults and are loaded from `.env` files.

## Data Flow Architecture

1. **Collection**: Reddit scraper filters posts by health keywords and extracts full comment threads
2. **Processing**: Language detection, newcomer identification, and network relationship extraction
3. **Storage**: Structured data saved as JSON with optional database persistence
4. **Analysis**: NetworkX builds interaction graphs and calculates centrality measures
5. **Annotation**: Gradified interface presents posts with public health context for human validation

## Network Analysis Components

The system uses directed graphs to model Reddit interactions:
- **Nodes**: Reddit users (excludes deleted accounts)
- **Edges**: Comment-to-post and reply-to-comment relationships with weights
- **Metrics**: Degree centrality, betweenness centrality, community detection
- **Visualization**: Interactive Plotly graphs with highlighted misinformation spreaders

## Human Annotation System

The Gradio interface provides:
- **Card-based Design**: Rapid post review with public health guideline context
- **Gamification**: Progress tracking, achievements, and inter-annotator competition
- **Quality Assurance**: Confidence scoring and consensus mechanisms
- **Database Integration**: SQLite backend for annotation storage and user statistics

## Key File Structure

```
src/
├── reddit_scraper.py      # PRAW-based data collection with keyword filtering
├── network_analysis.py    # NetworkX social network analysis
└── database_models.py     # SQLAlchemy models for data persistence

gradio_app/
└── annotation_interface.py # Gamified human validation interface

config/
└── settings.py           # Centralized configuration management

main.py                   # CLI interface with collect/analyze/annotate commands
proof_of_concept.py      # Quick demonstration script
```

## Database Schema

- **RedditPost**: Post metadata with language detection and newcomer flags
- **RedditComment**: Comment content with parent-child relationships
- **PostAnnotation**: Human validation labels with confidence scores
- **UserStats**: Annotator progress tracking for gamification
- **NetworkMetrics**: Stored network analysis results

## Research Ethics Compliance

All data handling follows strict ethical guidelines:
- Data anonymization and no personal information storage
- Reddit Terms of Service compliance
- Research Ethics Board approval required before deployment
- Community consent and benefit-sharing frameworks

## Development Notes

- The system is designed for academic research with plans for public health agency integration
- Multi-language support is built-in but requires Google Translate API for non-English content
- Rate limiting is implemented to respect Reddit API constraints
- All timestamps use UTC for consistency across analysis periods

## Testing and Validation

Use `proof_of_concept.py` for quick functionality verification. The demo workflow provides a complete end-to-end test of data collection, analysis, and annotation preparation.
