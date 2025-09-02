"""
Enhanced database models with pgvector support for semantic analysis
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()


class RedditPost(Base):
    """Enhanced model for Reddit posts with vector embeddings"""

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
    is_newcomer_related = Column(Boolean, default=False)

    # Language community analysis enhancements
    non_official_language_indicators = Column(Text)  # JSON of detected patterns
    code_switching_score = Column(Float)  # Mix of heritage language + eng/fra
    translation_patterns = Column(Boolean, default=False)  # Translated content detected
    cultural_health_references = Column(Text)  # Traditional medicine mentions

    # Vector embeddings for semantic search
    title_embedding = Column(Vector(384))  # sentence-transformers default size
    content_embedding = Column(Vector(384))
    combined_embedding = Column(Vector(384))  # title + content

    # Misinformation analysis
    misinformation_score = Column(Float)  # ML model confidence
    contains_health_keywords = Column(Boolean, default=False)
    keyword_count = Column(Integer, default=0)

    # Relationships
    comments = relationship("RedditComment", back_populates="post")
    annotations = relationship("PostAnnotation", back_populates="post")


class RedditComment(Base):
    """Enhanced model for Reddit comments with embeddings"""

    __tablename__ = "reddit_comments"

    id = Column(Integer, primary_key=True)
    comment_id = Column(String(50), unique=True, nullable=False)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    author = Column(String(100))
    body = Column(Text)
    created_utc = Column(DateTime)
    score = Column(Integer)
    parent_id = Column(String(50))
    language = Column(String(10))
    is_newcomer_related = Column(Boolean, default=False)

    # Vector embeddings
    content_embedding = Column(Vector(384))

    # Analysis fields
    misinformation_score = Column(Float)
    contains_health_keywords = Column(Boolean, default=False)

    # Relationships
    post = relationship("RedditPost", back_populates="comments")


class PostAnnotation(Base):
    """Model for human annotations with agreement tracking"""

    __tablename__ = "post_annotations"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    annotator = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    confidence = Column(Integer)
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Inter-rater reliability tracking
    is_consensus = Column(Boolean, default=False)
    agreement_score = Column(Float)  # How much annotators agree

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


class SimilarContent(Base):
    """Model for storing semantic similarity relationships"""

    __tablename__ = "similar_content"

    id = Column(Integer, primary_key=True)
    source_post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    target_post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    similarity_score = Column(Float)
    similarity_type = Column(String(50))  # 'content', 'title', 'semantic'
    created_at = Column(DateTime, default=datetime.utcnow)


class MisinformationCluster(Base):
    """Model for grouping similar misinformation themes"""

    __tablename__ = "misinformation_clusters"

    id = Column(Integer, primary_key=True)
    cluster_name = Column(String(200))
    cluster_description = Column(Text)
    centroid_embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Cluster metadata
    post_count = Column(Integer, default=0)
    avg_engagement = Column(Float)
    primary_language = Column(String(10))
    subreddit_distribution = Column(Text)  # JSON of subreddit counts


class ClusterMembership(Base):
    """Model for post-cluster relationships"""

    __tablename__ = "cluster_memberships"

    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey("reddit_posts.post_id"))
    cluster_id = Column(Integer, ForeignKey("misinformation_clusters.id"))
    distance_to_centroid = Column(Float)
    membership_confidence = Column(Float)


class UserStats(Base):
    """Enhanced model for tracking annotator statistics"""

    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)
    annotator = Column(String(100), unique=True, nullable=False)
    total_annotations = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)
    last_active = Column(DateTime)
    achievements = Column(Text, default="[]")

    # Inter-rater reliability metrics
    agreement_with_consensus = Column(Float, default=0.0)
    expertise_score = Column(Float, default=0.0)  # Based on accuracy over time

    # Community expertise enhancements
    community_expertise = Column(Text)  # JSON of expertise areas
    language_communities = Column(Text)  # Which communities they understand
    cultural_competency_score = Column(Float)  # How well they understand context


class NetworkMetrics(Base):
    """Enhanced model for network analysis results"""

    __tablename__ = "network_metrics"

    id = Column(Integer, primary_key=True)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    num_nodes = Column(Integer)
    num_edges = Column(Integer)
    density = Column(Float)
    num_communities = Column(Integer)
    largest_community_size = Column(Integer)

    # Advanced network metrics
    avg_clustering_coefficient = Column(Float)
    diameter = Column(Integer)
    assortativity = Column(Float)

    # Misinformation-specific metrics
    misinformation_centrality_correlation = Column(Float)
    information_flow_speed = Column(Float)

    metrics_json = Column(Text)


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


def create_database_with_vector_extension(database_url: str):
    """Create database with pgvector extension enabled"""
    engine = create_engine(database_url)

    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()

    # Create all tables
    Base.metadata.create_all(engine)
    return engine


def get_session(database_url: str):
    """Get database session with vector support"""
    engine = create_database_with_vector_extension(database_url)
    Session = sessionmaker(bind=engine)
    return Session()
