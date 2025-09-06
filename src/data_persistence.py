"""
Data persistence module for Reddit health misinformation research platform
Handles database operations with proper duplicate detection and upsert logic
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from config.settings import Config
from src.database_models import Base, PostAnnotation, RedditComment, RedditPost


class DataPersistenceManager:
    """Handles all database persistence operations with duplicate management"""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database connection"""
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Ensure tables exist
        Base.metadata.create_all(self.engine)

        logger.info(f"Initialized database persistence: {self.database_url}")

    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()

    def post_exists(self, post_id: str) -> bool:
        """Check if a post already exists in the database"""
        with self.get_session() as session:
            return (
                session.query(RedditPost).filter(RedditPost.post_id == post_id).first()
                is not None
            )

    def comment_exists(self, comment_id: str) -> bool:
        """Check if a comment already exists in the database"""
        with self.get_session() as session:
            return (
                session.query(RedditComment)
                .filter(RedditComment.comment_id == comment_id)
                .first()
                is not None
            )

    def get_existing_post_ids(self, post_ids: List[str]) -> List[str]:
        """Get list of post IDs that already exist in database"""
        with self.get_session() as session:
            existing = (
                session.query(RedditPost.post_id)
                .filter(RedditPost.post_id.in_(post_ids))
                .all()
            )
            return [row[0] for row in existing]

    def save_post(self, post_data: Dict) -> Tuple[bool, str]:
        """
        Save a single post to database with upsert logic

        Returns:
            Tuple of (success: bool, message: str)
        """
        with self.get_session() as session:
            try:
                # Check if post exists
                existing_post = (
                    session.query(RedditPost)
                    .filter(RedditPost.post_id == post_data["post_id"])
                    .first()
                )

                if existing_post:
                    # Update existing post (in case of score changes, etc.)
                    for key, value in post_data.items():
                        if hasattr(existing_post, key) and key != "post_id":
                            setattr(existing_post, key, value)

                    session.commit()
                    return True, f"Updated existing post {post_data['post_id']}"

                else:
                    # Create new post
                    # Convert datetime if it's a string
                    if isinstance(post_data.get("created_utc"), str):
                        post_data["created_utc"] = datetime.fromisoformat(
                            post_data["created_utc"].replace("Z", "+00:00")
                        )

                    # Remove comments from post_data for separate handling
                    comments_data = post_data.pop("comments", [])

                    # Remove any tracking fields (starting with underscore) that aren't database fields
                    clean_post_data = {
                        k: v for k, v in post_data.items() if not k.startswith("_")
                    }

                    # Handle special fields that need JSON serialization
                    if "lgbtq_contexts" in clean_post_data:
                        clean_post_data["lgbtq_contexts_json"] = json.dumps(
                            clean_post_data.pop("lgbtq_contexts")
                        )

                    # Create post object
                    post = RedditPost(**clean_post_data)
                    session.add(post)
                    session.flush()  # Get the post ID

                    # Save comments separately
                    comment_count = 0
                    for comment_data in comments_data:
                        success, _ = self.save_comment(comment_data, session=session)
                        if success:
                            comment_count += 1

                    session.commit()
                    return (
                        True,
                        f"Saved new post {post_data['post_id']} with {comment_count} comments",
                    )

            except IntegrityError as e:
                session.rollback()
                logger.warning(
                    f"Integrity error saving post {post_data.get('post_id')}: {e}"
                )
                return False, f"Duplicate post {post_data.get('post_id')}"

            except Exception as e:
                session.rollback()
                logger.error(f"Error saving post {post_data.get('post_id')}: {e}")
                return False, f"Error: {str(e)}"

    def save_comment(
        self, comment_data: Dict, session: Optional[Session] = None
    ) -> Tuple[bool, str]:
        """
        Save a single comment to database with upsert logic

        Returns:
            Tuple of (success: bool, message: str)
        """
        should_close_session = session is None
        if session is None:
            session = self.get_session()

        try:
            # Check if comment exists
            existing_comment = (
                session.query(RedditComment)
                .filter(RedditComment.comment_id == comment_data["comment_id"])
                .first()
            )

            if existing_comment:
                # Update existing comment
                for key, value in comment_data.items():
                    if hasattr(existing_comment, key) and key != "comment_id":
                        setattr(existing_comment, key, value)

                if should_close_session:
                    session.commit()
                return True, f"Updated comment {comment_data['comment_id']}"

            else:
                # Create new comment
                # Convert datetime if it's a string
                if isinstance(comment_data.get("created_utc"), str):
                    comment_data["created_utc"] = datetime.fromisoformat(
                        comment_data["created_utc"].replace("Z", "+00:00")
                    )

                comment = RedditComment(**comment_data)
                session.add(comment)

                if should_close_session:
                    session.commit()
                return True, f"Saved new comment {comment_data['comment_id']}"

        except IntegrityError as e:
            session.rollback()
            logger.warning(
                f"Integrity error saving comment {comment_data.get('comment_id')}: {e}"
            )
            return False, f"Duplicate comment {comment_data.get('comment_id')}"

        except Exception as e:
            session.rollback()
            logger.error(f"Error saving comment {comment_data.get('comment_id')}: {e}")
            return False, f"Error: {str(e)}"

        finally:
            if should_close_session:
                session.close()

    def bulk_save_posts(self, posts_data: List[Dict]) -> Dict[str, int]:
        """
        Save multiple posts to database with duplicate handling

        Returns:
            Dictionary with statistics: {'saved': count, 'updated': count, 'skipped': count, 'errors': count}
        """
        stats = {"saved": 0, "updated": 0, "skipped": 0, "errors": 0}

        # Get existing post IDs to avoid unnecessary processing
        post_ids = [post["post_id"] for post in posts_data]
        existing_ids = set(self.get_existing_post_ids(post_ids))

        logger.info(
            f"Processing {len(posts_data)} posts, {len(existing_ids)} already exist"
        )

        for post_data in posts_data:
            post_id = post_data["post_id"]

            try:
                success, message = self.save_post(post_data)

                if success:
                    if post_id in existing_ids:
                        stats["updated"] += 1
                    else:
                        stats["saved"] += 1

                    if stats["saved"] % 50 == 0:  # Progress logging
                        logger.info(
                            f"Progress: {stats['saved']} saved, {stats['updated']} updated"
                        )
                else:
                    stats["errors"] += 1
                    logger.warning(f"Failed to save post {post_id}: {message}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"Exception saving post {post_id}: {e}")

        logger.info(f"Bulk save complete: {stats}")
        return stats

    def load_and_save_json_data(self, json_file_path: str) -> Dict[str, int]:
        """
        Load Reddit data from JSON file and save to database

        Args:
            json_file_path: Path to JSON file containing Reddit data

        Returns:
            Dictionary with save statistics
        """
        try:
            with open(json_file_path, "r") as f:
                posts_data = json.load(f)

            logger.info(f"Loaded {len(posts_data)} posts from {json_file_path}")
            return self.bulk_save_posts(posts_data)

        except Exception as e:
            logger.error(f"Error loading data from {json_file_path}: {e}")
            return {"saved": 0, "updated": 0, "skipped": 0, "errors": 1}

    def get_collection_stats(self) -> Dict[str, int]:
        """Get current database collection statistics"""
        with self.get_session() as session:
            try:
                post_count = session.query(RedditPost).count()
                comment_count = session.query(RedditComment).count()
                annotation_count = session.query(PostAnnotation).count()

                # Get date ranges
                first_post = (
                    session.query(RedditPost.created_utc)
                    .order_by(RedditPost.created_utc.asc())
                    .first()
                )
                latest_post = (
                    session.query(RedditPost.created_utc)
                    .order_by(RedditPost.created_utc.desc())
                    .first()
                )

                # Subreddit breakdown
                subreddit_stats = session.execute(
                    text(
                        """
                    SELECT subreddit, COUNT(*) as count 
                    FROM reddit_posts 
                    GROUP BY subreddit 
                    ORDER BY count DESC
                """
                    )
                ).fetchall()

                return {
                    "total_posts": post_count,
                    "total_comments": comment_count,
                    "total_annotations": annotation_count,
                    "first_post_date": first_post[0] if first_post else None,
                    "latest_post_date": latest_post[0] if latest_post else None,
                    "subreddit_breakdown": dict(subreddit_stats),
                }

            except Exception as e:
                logger.error(f"Error getting collection stats: {e}")
                return {"error": str(e)}

    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Remove posts older than specified days (for data retention)

        Returns:
            Number of posts removed
        """
        with self.get_session() as session:
            try:
                cutoff_date = datetime.now() - timedelta(days=days_to_keep)

                # Delete old posts and their comments (cascading)
                deleted_count = (
                    session.query(RedditPost)
                    .filter(RedditPost.created_utc < cutoff_date)
                    .delete()
                )

                session.commit()
                logger.info(
                    f"Cleaned up {deleted_count} posts older than {days_to_keep} days"
                )
                return deleted_count

            except Exception as e:
                session.rollback()
                logger.error(f"Error during cleanup: {e}")
                return 0
