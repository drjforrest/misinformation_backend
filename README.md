# Health Misinformation Detection & Network Analysis Platform

This platform detects and analyzes health misinformation within immigrant communities on Reddit, combining social network analysis with human-validated machine learning.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Reddit API credentials
   ```

3. **Run demo:**
   ```bash
   python main.py demo --limit 50
   ```

4. **Launch annotation tool:**
   ```bash
   python main.py annotate --data-path data/demo_data_[timestamp].json
   ```

## Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps
2. Create a new application (script type)
3. Copy client ID and secret to your `.env` file
4. Set user agent to something descriptive

## Project Structure

```
misinformation_gay_mens_Health/
├── main.py                     # Main CLI interface
├── requirements.txt            # Python dependencies
├── PRODUCT_REQUIREMENTS.md     # Project documentation
├── config/
│   └── settings.py            # Configuration management
├── src/
│   ├── reddit_scraper.py      # Data collection
│   └── network_analysis.py    # Network analysis
├── gradio_app/
│   └── annotation_interface.py # Human annotation UI
├── data/                      # Data storage
├── notebooks/                 # Jupyter notebooks for exploration
└── logs/                      # Application logs
```

## Usage Examples

### Data Collection
```bash
# Collect data from all target subreddits
python main.py collect

# Quick demo collection
python main.py demo --limit 100
```

### Network Analysis
```bash
# Analyze collected data
python main.py analyze --data-path data/raw_reddit_data_[timestamp].json
```

### Human Annotation
```bash
# Launch annotation interface
python main.py annotate --data-path data/raw_reddit_data_[timestamp].json
```

## Target Communities

**Subreddits Monitored:**
- LGBTQ+ health: r/askgaybros, r/gay_irl, r/gaybros
- Canadian cities: r/toronto, r/vancouver, r/askTO
- Newcomer communities: r/NewToCanada, r/ImmigrationCanada

**Health Keywords:**
- Primary: HIV, PrEP, ARVs, syphilis, doxy, PEP, chlamydia, gonorrhoea
- Colloquial: "the clap", "burning", Truvada, Descovy

**Target Languages:**
- English, Tagalog, Mandarin/Cantonese, Punjabi, Spanish

## Research Ethics

This project follows strict ethical guidelines:
- All data is anonymized
- No personal information is stored
- Compliance with Reddit Terms of Service
- Research Ethics Board approval required before deployment

## Contributing

This is an academic research project. For questions about the methodology or collaboration opportunities, please contact the research team.

## License

This project is intended for academic research purposes. Please cite appropriately if using any components in your research.
