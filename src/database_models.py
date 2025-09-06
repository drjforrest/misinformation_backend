"""
Database models for storing Reddit posts, comments, and annotations
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class RedditPost(Base):
    """Model for Reddit posts"""

    __tablename__ = "reddit_posts"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), unique=True, nullable=False)
    subreddit = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    selftext = Column(Text)
    author = Column(String(100))
    created_utc = Column(DateTime)
    score = Column(Integer)
    upvote_ratio = Column(Float)
    num_comments = Column(Integer)
    url = Column(Text)
    language = Column(String(10))
    english_translation = Column(Text)  # Translation of title+selftext if non-English
    is_newcomer_related = Column(Boolean, default=False)
    full_text = Column(Text)  # Combined title and selftext for analysis

    # ML and Analysis columns from existing database
    title_embedding = Column(Text)  # Vector embeddings (stored as text)
    content_embedding = Column(Text)  # Vector embeddings (stored as text)
    combined_embedding = Column(Text)  # Vector embeddings (stored as text)
    misinformation_score = Column(Float)  # AI-generated misinformation score
    contains_health_keywords = Column(Boolean)  # Health keyword detection
    keyword_count = Column(Integer)  # Number of health keywords found

    # LGBTQ+ classification columns
    contains_lgbtq_keywords = Column(Boolean, default=False)  # LGBTQ+ keyword detection
    lgbtq_keyword_count = Column(Integer, default=0)  # Number of LGBTQ+ keywords found
    lgbtq_context = Column(String(50))  # Primary LGBTQ+ context (gay, bi, msm, etc.)
    lgbtq_contexts_json = Column(Text)  # JSON of all detected contexts
    lgbtq_relevance_score = Column(Float)  # ML classifier confidence score

    # Language community analysis enhancements
    non_official_language_indicators = Column(Text)  # JSON of detected patterns
    code_switching_score = Column(Float)  # Mix of heritage language + eng/fra
    translation_patterns = Column(Boolean, default=False)  # Translated content detected
    cultural_health_references = Column(Text)  # Traditional medicine mentions

    # Relationships
    comments = relationship("RedditComment", back_populates="post")
    annotations = relationship("PostAnnotation", back_populates="post")


class RedditComment(Base):
    """Model for Reddit comments"""

    __tablename__ = "reddit_comments"

    id = Column(Integer, primary_key=True)
    comment_id = Column(String(50), unique=True, nullable=False)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    author = Column(String(100))
    body = Column(Text)
    created_utc = Column(DateTime)
    score = Column(Integer)
    parent_id = Column(String(50))  # For tracking reply chains
    language = Column(String(10))
    english_translation = Column(Text)  # Translation of comment body if non-English
    translation_confidence = Column(Float)  # Translation confidence score
    is_newcomer_related = Column(Boolean, default=False)

    # Relationships
    post = relationship("RedditPost", back_populates="comments")


class PostAnnotation(Base):
    """Model for human annotations of posts"""

    __tablename__ = "post_annotations"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    annotator = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Accurate, Misinformation, etc.
    confidence = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Severity classification enhancements
    severity_level = Column(Integer)  # 1-5 your spectrum
    misinformation_type = Column(String(50))  # misconception/harmful/malicious
    target_community = Column(
        String(100)
    )  # Which non-official language community affected
    intervention_priority = Column(String(20))  # low/medium/high/urgent

    # Relationships
    post = relationship("RedditPost", back_populates="annotations")
    severity = relationship("MisinformationSeverity", back_populates="annotation")


class UserStats(Base):
    """Model for tracking annotator statistics"""

    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    annotator = Column(String(100), unique=True, nullable=False)
    total_annotations = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)
    last_active = Column(DateTime)
    achievements = Column(Text, default="[]")  # JSON string of achievements

    # Community expertise enhancements
    community_expertise = Column(Text)  # JSON of expertise areas
    language_communities = Column(Text)  # Which communities they understand
    cultural_competency_score = Column(Float)  # How well they understand context


class NetworkMetrics(Base):
    """Model for storing network analysis results"""

    __tablename__ = "network_metrics"

    id = Column(Integer, primary_key=True)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    num_nodes = Column(Integer)
    num_edges = Column(Integer)
    density = Column(Float)
    num_communities = Column(Integer)
    largest_community_size = Column(Integer)
    metrics_json = Column(Text)  # Full metrics as JSON


class CanadianUserProxy(Base):
    """Model for Canadian user identification through proxy indicators"""

    __tablename__ = "canadian_user_proxies"

    id = Column(Integer, primary_key=True)
    study_user_id = Column(String(100), unique=True)  # Your hashed ID
    original_username_hash = Column(String(64))  # For emergency unblinding
    canadian_probability = Column(Float)  # 0-1 confidence score

    # Proxy indicators
    healthcare_references = Column(Integer, default=0)  # OHIP, MSP mentions
    canadian_spelling_score = Column(Float, default=0.0)  # colour, centre
    timezone_pattern = Column(String(50))  # EST/PST posting patterns
    subreddit_patterns = Column(Text)  # JSON of Canadian subreddit participation
    cultural_markers = Column(Text)  # JSON of Canadian cultural references

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    interactions_as_source = relationship(
        "UserInteraction",
        foreign_keys="[UserInteraction.source_user_id]",
        back_populates="source_user",
    )
    interactions_as_target = relationship(
        "UserInteraction",
        foreign_keys="[UserInteraction.target_user_id]",
        back_populates="target_user",
    )


class MisinformationSeverity(Base):
    """Model for misinformation severity classification"""

    __tablename__ = "misinformation_severity"

    id = Column(Integer, primary_key=True)
    annotation_id = Column(Integer, ForeignKey("post_annotations.id"))

    # Your severity spectrum
    severity_level = Column(Integer)  # 1-5 scale
    harm_potential = Column(String(50))  # low/medium/high/critical
    urgency_score = Column(Integer)  # How quickly needs correction

    # Categorization
    misinformation_type = Column(String(50))  # misconception/harmful/malicious
    health_topic = Column(String(100))  # PrEP/STI_testing/HIV_treatment
    target_population = Column(String(100))  # newcomers/youth/MSM/general

    # Intervention recommendations
    suggested_response = Column(String(50))  # educate/correct/urgent_intervention
    resource_needed = Column(Text)  # What kind of correction/resource

    # Relationships
    annotation = relationship("PostAnnotation", back_populates="severity")
    interventions = relationship("InterventionResponse", back_populates="severity")


class UserInteraction(Base):
    """Model for user interaction network (for Social Network Analysis)"""

    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True)
    source_user_id = Column(
        String(100), ForeignKey("canadian_user_proxies.study_user_id")
    )
    target_user_id = Column(
        String(100), ForeignKey("canadian_user_proxies.study_user_id")
    )

    interaction_type = Column(String(50))  # reply/mention/thread_participation
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    comment_id = Column(String(50), ForeignKey("reddit_comments.comment_id"))

    interaction_timestamp = Column(DateTime)
    subreddit_context = Column(String(100))

    # Network analysis fields
    interaction_weight = Column(Float, default=1.0)  # Frequency/importance
    is_misinformation_related = Column(Boolean, default=False)

    # Relationships
    source_user = relationship(
        "CanadianUserProxy",
        foreign_keys=[source_user_id],
        back_populates="interactions_as_source",
    )
    target_user = relationship(
        "CanadianUserProxy",
        foreign_keys=[target_user_id],
        back_populates="interactions_as_target",
    )
    post = relationship("RedditPost")
    comment = relationship("RedditComment")


class InterventionResponse(Base):
    """Model for intervention tracking"""

    __tablename__ = "intervention_responses"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    severity_id = Column(Integer, ForeignKey("misinformation_severity.id"))

    # Generated response
    response_type = Column(String(50))  # fact_check/resource_link/community_alert
    generated_content = Column(Text)  # Auto-generated correction
    resource_links = Column(Text)  # JSON of relevant Canadian resources

    # Effectiveness tracking
    was_deployed = Column(Boolean, default=False)
    deployment_timestamp = Column(DateTime)
    effectiveness_score = Column(Float)  # If measurable

    # Relationships
    post = relationship("RedditPost")
    severity = relationship("MisinformationSeverity", back_populates="interventions")


def create_database(database_url: str):
    """Create database and tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str):
    """Get database session"""
    engine = create_database(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
