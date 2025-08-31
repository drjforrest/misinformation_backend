"""
Database models for storing Reddit posts, comments, and annotations
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class RedditPost(Base):
    """Model for Reddit posts"""
    __tablename__ = 'reddit_posts'
    
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
    
    # Relationships
    comments = relationship("RedditComment", back_populates="post")
    annotations = relationship("PostAnnotation", back_populates="post")

class RedditComment(Base):
    """Model for Reddit comments"""
    __tablename__ = 'reddit_comments'
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(String(50), unique=True, nullable=False)
    post_id = Column(String(50), ForeignKey('reddit_posts.post_id'))
    author = Column(String(100))
    body = Column(Text)
    created_utc = Column(DateTime)
    score = Column(Integer)
    parent_id = Column(String(50))  # For tracking reply chains
    language = Column(String(10))
    is_newcomer_related = Column(Boolean, default=False)
    
    # Relationships
    post = relationship("RedditPost", back_populates="comments")

class PostAnnotation(Base):
    """Model for human annotations of posts"""
    __tablename__ = 'post_annotations'
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String(50), ForeignKey('reddit_posts.post_id'))
    annotator = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Accurate, Misinformation, etc.
    confidence = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    post = relationship("RedditPost", back_populates="annotations")

class UserStats(Base):
    """Model for tracking annotator statistics"""
    __tablename__ = 'user_stats'
    
    id = Column(Integer, primary_key=True)
    annotator = Column(String(100), unique=True, nullable=False)
    total_annotations = Column(Integer, default=0)
    accuracy_score = Column(Float, default=0.0)
    last_active = Column(DateTime)
    achievements = Column(Text, default="[]")  # JSON string of achievements

class NetworkMetrics(Base):
    """Model for storing network analysis results"""
    __tablename__ = 'network_metrics'
    
    id = Column(Integer, primary_key=True)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    num_nodes = Column(Integer)
    num_edges = Column(Integer)
    density = Column(Float)
    num_communities = Column(Integer)
    largest_community_size = Column(Integer)
    metrics_json = Column(Text)  # Full metrics as JSON

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
