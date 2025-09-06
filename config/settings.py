"""
Configuration management for the Health Misinformation Detection Platform
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Main configuration class"""

    # Reddit API Settings
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "MisinformationResearch/1.0")

    # Database Settings
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/misinformation.db")

    # API Keys
    GOOGLE_TRANSLATE_API_KEY = os.getenv("GOOGLE_TRANSLATE_API_KEY")

    # Gradio Settings
    GRADIO_SHARE = os.getenv("GRADIO_SHARE", "False").lower() == "true"
    GRADIO_PORT = int(os.getenv("GRADIO_PORT", 7860))

    # Data Collection Settings
    MAX_POSTS_PER_SUBREDDIT = int(os.getenv("MAX_POSTS_PER_SUBREDDIT", 1000))
    DATA_COLLECTION_INTERVAL_HOURS = int(
        os.getenv("DATA_COLLECTION_INTERVAL_HOURS", 24)
    )

    # Analysis Settings
    MIN_COMMENT_LENGTH = int(os.getenv("MIN_COMMENT_LENGTH", 10))
    MAX_NETWORK_NODES = int(os.getenv("MAX_NETWORK_NODES", 5000))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/misinformation_analysis.log")


class ResearchConfig:
    """Research-specific configuration"""

    # Target Subreddits
    LGBTQ_SUBREDDITS = ["askgaybros", "gay_irl", "gaybros", "lgbt", "ainbow"]

    CANADIAN_SUBREDDITS = [
        "toronto",
        "vancouver",
        "askTO",
        "canada",
        "vancouver4friends",
        "torontogaybros",
    ]

    NEWCOMER_SUBREDDITS = [
        "NewToCanada",
        "ImmigrationCanada",
        "immigrationlaw",
        "PersonalFinanceCanada",
    ]

    # General Population Subreddits (for LGBTQ+ content in broader communities)
    GENERAL_POPULATION_SUBREDDITS = [
        "FilipinoCanadian",
        "PhillipinoCanadian",  # Alternative spelling
        "AsianCanadian",
        "SouthAsianCanadian",
        "ChineseCanadian",
        "IndianCanadian",
        "VietnameseCanadian",
        "KoreanCanadian",
        "JapaneseCanadian",
        "SikhCanadian",
        "HinduCanadian",
        "MuslimCanadian",
        "JewishCanadian",
        "BlackCanadian",
        "IndigenousCanadian",
        "ImmigrantCanada",
        "NewcomersCanada",
        "CanadaImmigration",
        "CanadianExpats",
        "AskACanadian",
        "CanadaPolitics",
        "CanadaPublicServants",
        "Ontario",
        "BritishColumbia",
        "Alberta",
        "Quebec",
        "NovaScotia",
        "NewBrunswick",
        "Manitoba",
        "Saskatchewan",
        "Newfoundland",
        "NorthwestTerritories",
        "Yukon",
        "Nunavut",
    ]

    # Health Keywords
    PRIMARY_KEYWORDS = [
        "HIV",
        "PrEP",
        "ARVs",
        "syphilis",
        "doxy",
        "PEP",
        "chlamydia",
        "gonorrhoea",
        "gonorrhea",
    ]

    COLLOQUIAL_TERMS = [
        "the clap",
        "burning",
        "discharge",
        "Truvada",
        "Descovy",
        "undetectable",
        "viral load",
        "CD4",
    ]

    # LGBTQ+ Keywords for general population content classification
    LGBTQ_KEYWORDS = [
        "gay",
        "lesbian",
        "bisexual",
        "bi",
        "transgender",
        "trans",
        "queer",
        "lgbt",
        "lgbtq",
        "lgbtq+",
        "lgbtqia+",
        "asexual",
        "ace",
        "pansexual",
        "nonbinary",
        "genderqueer",
        "coming out",
        "out of the closet",
        "dating",
        "relationship",
        "partner",
        "boyfriend",
        "girlfriend",
        "husband",
        "wife",
        "marriage",
        "wedding",
        "pride",
        "rainbow",
        "homophobia",
        "transphobia",
        "biphobia",
        "discrimination",
        "equality",
        "rights",
        "conversion therapy",
        "bullying",
        "harassment",
        "hate crime",
        "marriage equality",
        "sexual orientation",
        "gender identity",
        "sexual preference",
        "attracted to",
        "interested in",
        "dating men",
        "dating women",
        "same-sex",
        "same gender",
        "gay rights",
        "trans rights",
        "pride month",
        "rainbow flag",
        "equal sign",
        "progress pride",
        "philly pride",
        "drag queen",
        "drag king",
        "bear",
        "twink",
        "otter",
        "leather",
        "kink",
        "bdsm",
        "polyamory",
        "open relationship",
        "throuple",
        "chosen family",
        "mental health",
        "anxiety",
        "depression",
        "suicide prevention",
        "therapy",
        "coming out support",
        "gender dysphoria",
        "transition",
        "hormones",
        "surgery",
    ]

    # Identity-specific terms for context awareness
    GAY_TERMS = [
        "gay man",
        "gay men",
        "gay guy",
        "gay guys",
        "gay male",
        "gay males",
        "gay community",
        "gay culture",
        "gay lifestyle",
        "gay scene",
        "gay bar",
        "gay club",
        "gay dating",
        "gay relationship",
        "gay sex",
        "gay hookup",
        "gay porn",
        "gay pride",
    ]

    BI_TERMS = [
        "bisexual",
        "bi man",
        "bi woman",
        "bi people",
        "bi community",
        "bi dating",
        "bi relationship",
        "bi curious",
        "bi pride",
        "attracted to men and women",
        "attracted to both",
    ]

    MSM_TERMS = [
        "men who have sex with men",
        "msm",
        "gay sex",
        "male-male",
        "anal sex",
        "bareback",
        "condom",
        "lube",
        "poppers",
        "cruising",
        "bathhouse",
        "gay sauna",
        "gay hookup",
        "gay dating app",
        "grindr",
        "scruff",
        "squirt.org",
    ]

    # Target Languages
    TARGET_LANGUAGES = [
        "en",
        "tl",
        "zh",
        "pa",
        "es",
    ]  # English, Tagalog, Chinese, Punjabi, Spanish

    # Newcomer Indicators
    NEWCOMER_PHRASES = [
        "new to Canada",
        "just moved here",
        "recent immigrant",
        "don't know the system",
        "how does healthcare work",
        "no health card",
        "walk-in clinic",
        "without OHIP",
    ]

    # Public Health Guidelines Sources
    GUIDELINE_SOURCES = {
        "PHAC": "https://www.canada.ca/en/public-health/",
        "CDC": "https://www.cdc.gov/",
        "WHO": "https://www.who.int/",
    }


# Validation settings for human annotators
class AnnotationConfig:
    """Configuration for the human annotation process"""

    ANNOTATION_CATEGORIES = ["Accurate", "Misinformation", "Unclear/Mixed", "Off-topic"]

    CONFIDENCE_LEVELS = [1, 2, 3, 4, 5]  # 1 = Not confident, 5 = Very confident

    # Gamification settings
    POSTS_PER_BATCH = 25
    LEADERBOARD_UPDATE_INTERVAL = 3600  # seconds
    ACHIEVEMENT_THRESHOLDS = {
        "posts_reviewed": [10, 50, 100, 500, 1000],
        "accuracy_score": [0.7, 0.8, 0.9, 0.95],
        "days_active": [1, 7, 30, 90],
    }
