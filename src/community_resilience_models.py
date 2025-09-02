"""
Database models for Community Resilience & Social Capital Analysis
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    JSON,
)
from datetime import datetime

from src.database_models import Base


class CommunityResilienceMetric(Base):
    """Model for tracking community resilience metrics over time"""

    __tablename__ = "community_resilience_metrics"

    id = Column(Integer, primary_key=True)
    subreddit = Column(String(100), nullable=False)
    measurement_date = Column(DateTime, default=datetime.utcnow)

    # Core resilience metrics
    total_posts = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    response_rate = Column(Float, default=0.0)  # Comments per post

    # Support dynamics
    support_posts = Column(Integer, default=0)
    help_seeking_posts = Column(Integer, default=0)
    knowledge_sharing_posts = Column(Integer, default=0)
    cultural_bridge_posts = Column(Integer, default=0)

    # Calculated scores
    peer_support_ratio = Column(Float, default=0.0)
    community_engagement_score = Column(Float, default=0.0)
    resilience_level = Column(String(20))  # Very High, High, Moderate, Developing

    # Metadata
    calculation_method = Column(String(50), default="automated")
    notes = Column(Text)


class KnowledgeBroker(Base):
    """Model for tracking community knowledge brokers"""

    __tablename__ = "knowledge_brokers"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    subreddit = Column(String(100), nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)

    # Broker metrics
    broker_score = Column(Float, default=0.0)
    knowledge_shares = Column(Integer, default=0)
    support_given = Column(Integer, default=0)
    communities_active = Column(Integer, default=0)
    total_activity = Column(Integer, default=0)
    average_community_score = Column(Float, default=0.0)

    # Influence metrics
    centrality_score = Column(Float, default=0.0)
    betweenness_score = Column(Float, default=0.0)
    response_rate_to_posts = Column(Float, default=0.0)

    # Qualitative assessment
    broker_type = Column(
        String(50)
    )  # e.g., "medical_expert", "peer_supporter", "cultural_bridge"
    expertise_areas = Column(JSON)  # List of health topics
    cultural_communities = Column(JSON)  # List of cultural groups served


class SupportInteraction(Base):
    """Model for tracking peer support interactions"""

    __tablename__ = "support_interactions"

    id = Column(Integer, primary_key=True)

    # Basic interaction info
    help_seeker = Column(String(100), nullable=False)
    helper = Column(String(100), nullable=False)
    subreddit = Column(String(100), nullable=False)
    interaction_date = Column(DateTime, default=datetime.utcnow)

    # Post/comment references
    original_post_id = Column(String(50))
    response_comment_id = Column(String(50))

    # Interaction characteristics
    interaction_type = Column(
        String(50)
    )  # question_answer, emotional_support, resource_sharing
    help_topic = Column(String(100))  # HIV, PrEP, testing, etc.
    cultural_context = Column(Boolean, default=False)
    language_used = Column(String(10))

    # Quality indicators
    helpful_response = Column(Boolean)  # Based on keyword analysis
    follow_up_occurred = Column(Boolean, default=False)
    community_upvotes = Column(Integer, default=0)

    # Analysis metadata
    detection_method = Column(String(50), default="automated")
    confidence_score = Column(Float, default=0.0)


class CulturalAdaptation(Base):
    """Model for tracking cultural adaptation of health information"""

    __tablename__ = "cultural_adaptations"

    id = Column(Integer, primary_key=True)

    # Content reference
    post_id = Column(String(50))
    comment_id = Column(String(50))
    subreddit = Column(String(100), nullable=False)
    author = Column(String(100), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)

    # Cultural indicators
    source_culture_references = Column(JSON)  # Cultural terms detected
    health_topic = Column(String(100))
    adaptation_type = Column(
        String(50)
    )  # bridge_explanation, cultural_context, traditional_modern

    # Language and translation
    original_language = Column(String(10))
    contains_translation = Column(Boolean, default=False)
    cultural_bridge_keywords = Column(JSON)

    # Community response
    engagement_score = Column(Float, default=0.0)  # Based on responses/upvotes
    helpful_to_community = Column(Boolean)

    # Analysis
    cultural_competency_score = Column(Float, default=0.0)
    bridges_gap = Column(Boolean, default=False)  # Helps bridge cultural health gaps


class CommunityHealthTopic(Base):
    """Model for tracking health topics and community knowledge patterns"""

    __tablename__ = "community_health_topics"

    id = Column(Integer, primary_key=True)

    # Topic identification
    health_topic = Column(String(100), nullable=False)
    subreddit = Column(String(100), nullable=False)
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)

    # Topic metrics
    total_mentions = Column(Integer, default=0)
    help_seeking_mentions = Column(Integer, default=0)
    knowledge_sharing_mentions = Column(Integer, default=0)
    misinformation_risk_level = Column(String(20))  # low, medium, high

    # Community response patterns
    average_response_quality = Column(Float, default=0.0)
    knowledge_broker_involvement = Column(Boolean, default=False)
    cultural_adaptation_present = Column(Boolean, default=False)

    # Resource gaps
    needs_better_resources = Column(Boolean, default=False)
    resource_gap_description = Column(Text)
    intervention_opportunity = Column(Text)

    # Language diversity
    languages_discussed = Column(JSON)  # Languages this topic appears in
    cross_cultural_discussion = Column(Boolean, default=False)


# Helper functions for analysis


def calculate_resilience_score(metrics: CommunityResilienceMetric) -> float:
    """Calculate overall resilience score from individual metrics"""
    if not metrics.total_posts:
        return 0.0

    factors = [
        min(
            metrics.response_rate / 200, 1.0
        ),  # Normalize response rate (200% = optimal)
        min(
            metrics.peer_support_ratio / 30, 1.0
        ),  # Normalize support ratio (30% = optimal)
        min(metrics.help_seeking_posts / metrics.total_posts, 0.3)
        / 0.3,  # Normalize help-seeking
        min(metrics.knowledge_sharing_posts / metrics.total_posts, 0.2)
        / 0.2,  # Normalize knowledge sharing
    ]

    return sum(factors) / len(factors) * 100


def categorize_resilience_level(score: float) -> str:
    """Categorize resilience level based on score"""
    if score >= 80:
        return "Very High"
    elif score >= 60:
        return "High"
    elif score >= 40:
        return "Moderate"
    else:
        return "Developing"
