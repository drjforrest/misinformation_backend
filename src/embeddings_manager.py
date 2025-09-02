"""
Embeddings and semantic analysis module using pgvector
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger

from src.database_models_vector import (
    RedditPost,
    SimilarContent,
)
from config.settings import Config


class EmbeddingsManager:
    """Handles text embeddings and semantic similarity using pgvector"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embeddings model"""
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # Standard dimension for MiniLM
        logger.info(f"Initialized embeddings model: {model_name}")

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text string"""
        if not text or len(text.strip()) == 0:
            return np.zeros(self.embedding_dim)

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def generate_post_embeddings(self, session: Session, batch_size: int = 100):
        """Generate embeddings for all posts in the database"""

        # Get posts without embeddings
        posts = (
            session.query(RedditPost)
            .filter(RedditPost.combined_embedding.is_(None))
            .all()
        )

        logger.info(f"Generating embeddings for {len(posts)} posts...")

        for i in range(0, len(posts), batch_size):
            batch = posts[i : i + batch_size]

            for post in batch:
                # Generate embeddings for different text components
                title_embedding = self.generate_embedding(post.title)
                content_embedding = self.generate_embedding(post.selftext or "")

                # Combined embedding (title + content)
                combined_text = f"{post.title} {post.selftext or ''}"
                combined_embedding = self.generate_embedding(combined_text)

                # Update post with embeddings
                post.title_embedding = title_embedding.tolist()
                post.content_embedding = content_embedding.tolist()
                post.combined_embedding = combined_embedding.tolist()

            session.commit()
            logger.info(f"Processed {min(i+batch_size, len(posts))}/{len(posts)} posts")

    def find_similar_posts(
        self, session: Session, post_id: str, threshold: float = 0.7, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """Find semantically similar posts using vector similarity"""

        # Get the target post's embedding
        target_post = (
            session.query(RedditPost).filter(RedditPost.post_id == post_id).first()
        )

        if not target_post or not target_post.combined_embedding:
            return []

        # Use pgvector cosine similarity
        query = text(
            """
            SELECT post_id, 1 - (combined_embedding <=> :target_embedding) AS similarity
            FROM reddit_posts 
            WHERE post_id != :post_id 
              AND combined_embedding IS NOT NULL
              AND 1 - (combined_embedding <=> :target_embedding) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """
        )

        results = session.execute(
            query,
            {
                "target_embedding": target_post.combined_embedding,
                "post_id": post_id,
                "threshold": threshold,
                "limit": limit,
            },
        ).fetchall()

        return [(row.post_id, row.similarity) for row in results]

    def cluster_misinformation_posts(
        self, session: Session, misinformation_post_ids: List[str], n_clusters: int = 5
    ) -> Dict:
        """Cluster misinformation posts by semantic similarity"""

        from sklearn.cluster import KMeans

        # Get embeddings for misinformation posts
        posts = (
            session.query(RedditPost)
            .filter(
                RedditPost.post_id.in_(misinformation_post_ids),
                RedditPost.combined_embedding.is_not(None),
            )
            .all()
        )

        if len(posts) < n_clusters:
            logger.warning(f"Too few posts ({len(posts)}) for {n_clusters} clusters")
            return {}

        # Extract embeddings
        embeddings = np.array([post.combined_embedding for post in posts])
        post_ids = [post.post_id for post in posts]

        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Create cluster summaries
        clusters = {}
        for i in range(n_clusters):
            cluster_posts = [
                post_ids[j] for j, label in enumerate(cluster_labels) if label == i
            ]
            cluster_centroid = kmeans.cluster_centers_[i]

            # Get representative posts (closest to centroid)
            distances = np.linalg.norm(
                embeddings[cluster_labels == i] - cluster_centroid, axis=1
            )
            representative_idx = np.argmin(distances)
            representative_post_idx = [
                j for j, label in enumerate(cluster_labels) if label == i
            ][representative_idx]
            representative_post = posts[representative_post_idx]

            clusters[f"cluster_{i}"] = {
                "post_count": len(cluster_posts),
                "post_ids": cluster_posts,
                "centroid": cluster_centroid.tolist(),
                "representative_title": representative_post.title,
                "representative_content": (
                    representative_post.selftext[:200] + "..."
                    if representative_post.selftext
                    else ""
                ),
            }

        return clusters

    def detect_misinformation_propagation(
        self, session: Session, source_post_id: str, time_window_hours: int = 72
    ) -> List[Dict]:
        """Detect potential misinformation propagation through semantic similarity"""

        source_post = (
            session.query(RedditPost)
            .filter(RedditPost.post_id == source_post_id)
            .first()
        )

        if not source_post or not source_post.combined_embedding:
            return []

        # Find posts with high similarity that appeared after the source
        query = text(
            """
            SELECT 
                post_id,
                title,
                subreddit,
                author,
                created_utc,
                1 - (combined_embedding <=> :source_embedding) AS similarity
            FROM reddit_posts 
            WHERE post_id != :source_post_id 
              AND combined_embedding IS NOT NULL
              AND created_utc > :source_time
              AND created_utc < :end_time
              AND 1 - (combined_embedding <=> :source_embedding) > 0.8
            ORDER BY similarity DESC, created_utc ASC
        """
        )

        from datetime import timedelta

        end_time = source_post.created_utc + timedelta(hours=time_window_hours)

        results = session.execute(
            query,
            {
                "source_embedding": source_post.combined_embedding,
                "source_post_id": source_post_id,
                "source_time": source_post.created_utc,
                "end_time": end_time,
            },
        ).fetchall()

        propagation_events = []
        for row in results:
            propagation_events.append(
                {
                    "post_id": row.post_id,
                    "title": row.title,
                    "subreddit": row.subreddit,
                    "author": row.author,
                    "created_utc": row.created_utc,
                    "similarity": float(row.similarity),
                    "time_diff_hours": (
                        row.created_utc - source_post.created_utc
                    ).total_seconds()
                    / 3600,
                }
            )

        return propagation_events

    def search_by_semantic_query(
        self, session: Session, query_text: str, limit: int = 20, threshold: float = 0.6
    ) -> List[Dict]:
        """Search posts using semantic similarity to a text query"""

        # Generate embedding for search query
        query_embedding = self.generate_embedding(query_text)

        # Search using pgvector
        search_query = text(
            """
            SELECT 
                post_id,
                title,
                selftext,
                subreddit,
                author,
                language,
                is_newcomer_related,
                1 - (combined_embedding <=> :query_embedding) AS similarity
            FROM reddit_posts 
            WHERE combined_embedding IS NOT NULL
              AND 1 - (combined_embedding <=> :query_embedding) > :threshold
            ORDER BY similarity DESC
            LIMIT :limit
        """
        )

        results = session.execute(
            search_query,
            {
                "query_embedding": query_embedding.tolist(),
                "threshold": threshold,
                "limit": limit,
            },
        ).fetchall()

        search_results = []
        for row in results:
            search_results.append(
                {
                    "post_id": row.post_id,
                    "title": row.title,
                    "content_preview": (
                        (row.selftext or "")[:200] + "..." if row.selftext else ""
                    ),
                    "subreddit": row.subreddit,
                    "author": row.author,
                    "language": row.language,
                    "is_newcomer_related": row.is_newcomer_related,
                    "similarity": float(row.similarity),
                }
            )

        return search_results

    def update_similarity_relationships(self, session: Session):
        """Update the similar_content table with new similarity relationships"""

        # Clear existing relationships
        session.query(SimilarContent).delete()

        # Get all posts with embeddings
        posts = (
            session.query(RedditPost)
            .filter(RedditPost.combined_embedding.is_not(None))
            .all()
        )

        logger.info(f"Computing similarity relationships for {len(posts)} posts...")

        # Batch process similarity calculations
        for i, source_post in enumerate(posts):
            similar_posts = self.find_similar_posts(
                session, source_post.post_id, threshold=0.75, limit=5
            )

            for similar_post in similar_posts:
                similarity_record = SimilarContent(
                    source_post_id=source_post.post_id,
                    target_post_id=similar_post["post_id"],
                    similarity_score=similar_post["similarity"],
                    similarity_type="semantic",
                )
                session.add(similarity_record)

            if i % 50 == 0:
                session.commit()
                logger.info(f"Processed {i}/{len(posts)} posts")

        session.commit()
        logger.info("Similarity relationships updated")


if __name__ == "__main__":
    # Example usage
    from src.database_models_vector import get_session

    embeddings_manager = EmbeddingsManager()
    session = get_session(Config.DATABASE_URL)

    # Generate embeddings for all posts
    embeddings_manager.generate_post_embeddings(session)

    # Example semantic search
    results = embeddings_manager.search_by_semantic_query(
        session, "PrEP side effects and safety concerns", limit=10
    )

    print(f"Found {len(results)} semantically similar posts")
    for result in results[:3]:
        print(f"- {result['title']} (similarity: {result['similarity']:.3f})")
