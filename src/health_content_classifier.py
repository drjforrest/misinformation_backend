#!/usr/bin/env python3
"""
Health Content Classification ML Pipeline
Trains a real ML model to classify posts as health-related vs general discussion
"""

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
import pickle
import re
from typing import Tuple, Dict, List, Any
from pathlib import Path
import logging
from datetime import datetime

from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment
from config.settings import ResearchConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthContentClassifier:
    """
    ML Classifier for identifying health-related content in Reddit posts
    Uses real data and produces genuine classification results
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.model = None
        self.vectorizer = None
        self.pipeline = None
        self.health_keywords = (
            ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS
        )

    def load_training_data(self) -> pd.DataFrame:
        """Load posts and comments from database for training"""
        logger.info("Loading training data from database...")

        with self.db_manager.get_session() as session:
            # Load posts
            posts = session.query(RedditPost).all()
            post_data = []

            for post in posts:
                text = f"{post.title} {post.selftext or ''}"
                post_data.append(
                    {
                        "id": post.post_id,
                        "text": text,
                        "type": "post",
                        "subreddit": post.subreddit,
                        "author": post.author,
                        "score": post.score or 0,
                        "num_comments": post.num_comments or 0,
                    }
                )

            # Load comments
            comments = session.query(RedditComment).all()
            comment_data = []

            for comment in comments:
                if (
                    comment.body and len(comment.body.strip()) > 20
                ):  # Filter very short comments
                    comment_data.append(
                        {
                            "id": comment.comment_id,
                            "text": comment.body,
                            "type": "comment",
                            "subreddit": (
                                comment.post.subreddit if comment.post else "unknown"
                            ),
                            "author": comment.author,
                            "score": comment.score or 0,
                            "num_comments": 0,
                        }
                    )

        # Combine posts and comments
        all_data = post_data + comment_data
        df = pd.DataFrame(all_data)

        logger.info(f"Loaded {len(post_data)} posts and {len(comment_data)} comments")
        return df

    def create_health_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create training labels using rule-based approach
        This creates initial labels that we can refine with human annotation later
        """
        logger.info("Creating health content labels...")

        def is_health_related(text: str) -> bool:
            if not text:
                return False

            text_lower = text.lower()

            # Direct keyword matching
            for keyword in self.health_keywords:
                if keyword.lower() in text_lower:
                    return True

            # Health-related patterns
            health_patterns = [
                r"\b(std|sti)\b",
                r"\bhiv\b",
                r"\bprep\b",
                r"\bpep\b",
                r"\btesting\b.*\b(hiv|std|sti)\b",
                r"\b(clinic|doctor|physician)\b",
                r"\bhealth\b.*\b(insurance|care|system)\b",
                r"\b(symptom|diagnosis|treatment)\b",
                r"\b(vaccine|vaccination)\b",
                r"\bsexual\b.*\bhealth\b",
                r"\bunprotected\b.*\bsex\b",
            ]

            for pattern in health_patterns:
                if re.search(pattern, text_lower):
                    return True

            return False

        df["is_health_related"] = df["text"].apply(is_health_related)

        health_count = df["is_health_related"].sum()
        total_count = len(df)

        logger.info(
            f"Labeled {health_count} health-related items out of {total_count} total ({health_count/total_count*100:.1f}%)"
        )

        return df

    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for ML"""
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
            "",
            text,
        )

        # Remove Reddit-specific markup
        text = re.sub(r"/u/[A-Za-z0-9_-]+", "", text)
        text = re.sub(r"/r/[A-Za-z0-9_-]+", "", text)
        text = re.sub(r"\[deleted\]", "", text)
        text = re.sub(r"\[removed\]", "", text)

        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def train_model(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Train the health content classification model"""
        logger.info("Training health content classifier...")

        # Preprocess text
        df["processed_text"] = df["text"].apply(self.preprocess_text)

        # Remove empty texts
        df = df[df["processed_text"].str.len() > 10]

        # Prepare features and labels
        X = df["processed_text"]
        y = df["is_health_related"]

        # Check class distribution
        class_dist = y.value_counts()
        logger.info(
            f"Class distribution: Health={class_dist.get(True, 0)}, General={class_dist.get(False, 0)}"
        )

        if len(class_dist) < 2:
            raise ValueError(
                "Need both health-related and general content for training"
            )

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Create ML pipeline
        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=5000,
                        ngram_range=(1, 2),
                        stop_words="english",
                        min_df=2,
                        max_df=0.8,
                    ),
                ),
                (
                    "classifier",
                    LogisticRegression(random_state=42, class_weight="balanced"),
                ),
            ]
        )

        # Train the model
        self.pipeline.fit(X_train, y_train)

        # Evaluate
        train_score = self.pipeline.score(X_train, y_train)
        test_score = self.pipeline.score(X_test, y_test)

        y_pred = self.pipeline.predict(X_test)

        # Generate comprehensive evaluation
        results = {
            "train_accuracy": train_score,
            "test_accuracy": test_score,
            "classification_report": classification_report(
                y_test, y_pred, output_dict=True
            ),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "feature_count": self.pipeline.named_steps["tfidf"]
            .get_feature_names_out()
            .shape[0],
            "class_distribution": {
                "health_related": int(class_dist.get(True, 0)),
                "general": int(class_dist.get(False, 0)),
            },
        }

        logger.info(f"Training completed - Test Accuracy: {test_score:.3f}")
        logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")

        return results

    def predict_health_content(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict whether texts are health-related"""
        if not self.pipeline:
            raise ValueError("Model not trained yet. Call train_model() first.")

        processed_texts = [self.preprocess_text(text) for text in texts]
        predictions = self.pipeline.predict(processed_texts)
        probabilities = self.pipeline.predict_proba(processed_texts)

        results = []
        for i, (text, pred, prob) in enumerate(zip(texts, predictions, probabilities)):
            results.append(
                {
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "is_health_related": bool(pred),
                    "confidence": float(max(prob)),
                    "health_probability": float(prob[1]) if len(prob) > 1 else 0.0,
                    "general_probability": float(prob[0]) if len(prob) > 1 else 1.0,
                }
            )

        return results

    def get_top_health_features(self, n: int = 20) -> List[Tuple[str, float]]:
        """Get the most important features for health classification"""
        if not self.pipeline:
            return []

        feature_names = self.pipeline.named_steps["tfidf"].get_feature_names_out()
        coefficients = self.pipeline.named_steps["classifier"].coef_[0]

        # Get top positive coefficients (health-related features)
        feature_importance = list(zip(feature_names, coefficients))
        feature_importance.sort(key=lambda x: x[1], reverse=True)

        return feature_importance[:n]

    def save_model(self, filepath: str = "models/health_classifier.pkl"):
        """Save the trained model"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "pipeline": self.pipeline,
            "trained_at": datetime.now().isoformat(),
            "health_keywords": self.health_keywords,
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str = "models/health_classifier.pkl"):
        """Load a trained model"""
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.pipeline = model_data["pipeline"]
        self.health_keywords = model_data["health_keywords"]

        logger.info(f"Model loaded from {filepath}")


def train_health_classifier():
    """Main function to train the health content classifier"""
    logger.info("🤖 Starting Health Content Classifier Training")
    logger.info("=" * 50)

    classifier = HealthContentClassifier()

    # Load data
    df = classifier.load_training_data()

    if len(df) == 0:
        logger.error("No data found in database. Run data collection first.")
        return

    # Create labels
    df = classifier.create_health_labels(df)

    # Train model
    results = classifier.train_model(df)

    # Save model
    classifier.save_model()

    # Display results
    print("\n🎯 Training Results:")
    print(f"Training Accuracy: {results['train_accuracy']:.3f}")
    print(f"Test Accuracy: {results['test_accuracy']:.3f}")
    print(f"Training Samples: {results['training_samples']}")
    print(f"Test Samples: {results['test_samples']}")
    print(f"Features Used: {results['feature_count']}")

    print("\nClass Distribution:")
    print(f"  Health-related: {results['class_distribution']['health_related']}")
    print(f"  General: {results['class_distribution']['general']}")

    print("\nTop Health-Related Features:")
    top_features = classifier.get_top_health_features(15)
    for feature, importance in top_features:
        print(f"  {feature}: {importance:.3f}")

    # Test on some examples
    print("\n🧪 Testing on Sample Texts:")
    test_texts = [
        "Just started PrEP and wondering about side effects",
        "Anyone know good restaurants in Toronto?",
        "Got tested for HIV yesterday, waiting for results",
        "Planning a trip to Vancouver next month",
        "Doctor says I should get vaccinated for HPV",
    ]

    predictions = classifier.predict_health_content(test_texts)
    for pred in predictions:
        health_status = "HEALTH" if pred["is_health_related"] else "GENERAL"
        print(f"  [{health_status}] ({pred['confidence']:.2f}) {pred['text']}")

    print("\n✅ Model training complete! Saved to models/health_classifier.pkl")
    return classifier


if __name__ == "__main__":
    train_health_classifier()
