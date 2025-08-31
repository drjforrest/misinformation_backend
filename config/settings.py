"""
Configuration management for the Health Misinformation Detection Platform
"""

import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Main configuration class"""
    
    # Reddit API Settings
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'MisinformationResearch/1.0')
    
    # Database Settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/misinformation.db')
    
    # API Keys
    GOOGLE_TRANSLATE_API_KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY')
    
    # Gradio Settings
    GRADIO_SHARE = os.getenv('GRADIO_SHARE', 'False').lower() == 'true'
    GRADIO_PORT = int(os.getenv('GRADIO_PORT', 7860))
    
    # Data Collection Settings
    MAX_POSTS_PER_SUBREDDIT = int(os.getenv('MAX_POSTS_PER_SUBREDDIT', 1000))
    DATA_COLLECTION_INTERVAL_HOURS = int(os.getenv('DATA_COLLECTION_INTERVAL_HOURS', 24))
    
    # Analysis Settings
    MIN_COMMENT_LENGTH = int(os.getenv('MIN_COMMENT_LENGTH', 10))
    MAX_NETWORK_NODES = int(os.getenv('MAX_NETWORK_NODES', 5000))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/misinformation_analysis.log')

class ResearchConfig:
    """Research-specific configuration"""
    
    # Target Subreddits
    LGBTQ_SUBREDDITS = [
        'askgaybros',
        'gay_irl', 
        'gaybros',
        'lgbt',
        'ainbow'
    ]
    
    CANADIAN_SUBREDDITS = [
        'toronto',
        'vancouver', 
        'askTO',
        'canada',
        'vancouver4friends',
        'torontogaybros'
    ]
    
    NEWCOMER_SUBREDDITS = [
        'NewToCanada',
        'ImmigrationCanada',
        'immigrationlaw',
        'PersonalFinanceCanada'
    ]
    
    # Health Keywords
    PRIMARY_KEYWORDS = [
        'HIV', 'PrEP', 'ARVs', 'syphilis', 'doxy', 'PEP', 
        'chlamydia', 'gonorrhoea', 'gonorrhea'
    ]
    
    COLLOQUIAL_TERMS = [
        'the clap', 'burning', 'discharge', 'Truvada', 'Descovy',
        'undetectable', 'viral load', 'CD4'
    ]
    
    # Target Languages
    TARGET_LANGUAGES = ['en', 'tl', 'zh', 'pa', 'es']  # English, Tagalog, Chinese, Punjabi, Spanish
    
    # Newcomer Indicators
    NEWCOMER_PHRASES = [
        'new to Canada', 'just moved here', 'recent immigrant',
        'don\'t know the system', 'how does healthcare work',
        'no health card', 'walk-in clinic', 'without OHIP'
    ]
    
    # Public Health Guidelines Sources
    GUIDELINE_SOURCES = {
        'PHAC': 'https://www.canada.ca/en/public-health/',
        'CDC': 'https://www.cdc.gov/',
        'WHO': 'https://www.who.int/'
    }

# Validation settings for human annotators
class AnnotationConfig:
    """Configuration for the human annotation process"""
    
    ANNOTATION_CATEGORIES = [
        'Accurate',
        'Misinformation', 
        'Unclear/Mixed',
        'Off-topic'
    ]
    
    CONFIDENCE_LEVELS = [1, 2, 3, 4, 5]  # 1 = Not confident, 5 = Very confident
    
    # Gamification settings
    POSTS_PER_BATCH = 25
    LEADERBOARD_UPDATE_INTERVAL = 3600  # seconds
    ACHIEVEMENT_THRESHOLDS = {
        'posts_reviewed': [10, 50, 100, 500, 1000],
        'accuracy_score': [0.7, 0.8, 0.9, 0.95],
        'days_active': [1, 7, 30, 90]
    }
