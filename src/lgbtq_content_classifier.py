#!/usr/bin/env python3
"""
LGBTQ+ Content Classification ML Pipeline
Classifies Reddit posts as LGBTQ+-related with context awareness for gay, bi, and MSM users
"""

import logging
import pickle
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.data_persistence import DataPersistenceManager
from src.database_models import RedditComment, RedditPost

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LGBTQContentClassifier:
    """
    ML Classifier for identifying LGBTQ+-related content in Reddit posts
    with context awareness for gay, bi, and MSM users
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.model = None
        self.vectorizer = None
        self.pipeline = None

        # LGBTQ+ keywords and identity terms
        self.lgbtq_keywords = self._get_lgbtq_keywords()
        self.identity_terms = self._get_identity_terms()
        self.context_indicators = self._get_context_indicators()

    def _get_lgbtq_keywords(self) -> List[str]:
        """Get comprehensive LGBTQ+ related keywords"""
        return [
            # Core identity terms
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
            # Relationship and dating
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
            # Community and culture
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
            # Issues and topics
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
            # Health and wellness (LGBTQ+ context)
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
            # Pop culture and media
            "rupaul",
            "pose",
            "queer eye",
            "broad city",
            "orange is the new black",
            "moonlight",
            "call me by your name",
            "book of mormon",
            "hedwig",
            "wicked",
            # Slang and colloquial terms
            "queen",
            "fag",
            "faggot",
            "homo",
            "fruit",
            "cocksucker",
            "beard",
            "fruit loop",
            "light in the loafers",
            "friend of dorothy",
            "mary",
            "nelly",
            "flaming",
        ]

    def _get_identity_terms(self) -> Dict[str, List[str]]:
        """Get identity-specific terms for context awareness"""
        return {
            "gay": [
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
            ],
            "bi": [
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
            ],
            "msm": [
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
            ],
            "lesbian": [
                "lesbian",
                "gay woman",
                "sapphic",
                "wlw",
                "women loving women",
                "lesbian relationship",
                "lesbian dating",
                "lesbian pride",
            ],
            "trans": [
                "transgender",
                "trans man",
                "trans woman",
                "transgender woman",
                "transgender man",
                "mtf",
                "ftm",
                "transition",
                "transitioning",
                "gender dysphoria",
                "hormone therapy",
                "hrt",
                "gender affirmation",
            ],
        }

    def _get_context_indicators(self) -> List[str]:
        """Get terms that indicate LGBTQ+ context even without direct identity terms"""
        return [
            "sexual orientation",
            "gender identity",
            "sexual preference",
            "attracted to",
            "interested in",
            "dating men",
            "dating women",
            "same-sex",
            "same gender",
            "lgbt issues",
            "queer issues",
            "gay rights",
            "trans rights",
            "marriage equality",
            "pride month",
            "rainbow flag",
            "equal sign",
            "progress pride",
            "philly pride",
        ]

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
                if comment.body and len(comment.body.strip()) > 20:
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

    def create_lgbtq_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create training labels using rule-based approach for LGBTQ+ content
        """
        logger.info("Creating LGBTQ+ content labels...")

        def is_lgbtq_related(text: str) -> bool:
            if not text:
                return False

            text_lower = text.lower()

            # Direct keyword matching
            for keyword in self.lgbtq_keywords:
                if keyword.lower() in text_lower:
                    return True

            # Context indicators
            for indicator in self.context_indicators:
                if indicator.lower() in text_lower:
                    return True

            # Identity-specific patterns
            for identity, terms in self.identity_terms.items():
                for term in terms:
                    if term.lower() in text_lower:
                        return True

            # Advanced patterns for context awareness
            lgbtq_patterns = [
                r"\b(gay|bi|trans|queer|lesbian)\b.*\b(man|men|woman|women|people|community)\b",
                r"\b(attracted to|dating|interested in)\b.*\b(both|men|women|same sex)\b",
                r"\b(coming out|out of the closet)\b.*\b(as|to my)\b",
                r"\b(my|his|her)\b.*\b(boyfriend|girlfriend|partner)\b.*\b(is|was)\b",
                r"\b(pride|rainbow|lgbt)\b.*\b(month|flag|parade|event)\b",
                r"\b(gay|bi|trans)\b.*\b(rights|equality|marriage|law)\b",
            ]

            for pattern in lgbtq_patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True

            return False

        df["is_lgbtq_related"] = df["text"].apply(is_lgbtq_related)

        lgbtq_count = df["is_lgbtq_related"].sum()
        total_count = len(df)

        logger.info(
            f"Labeled {lgbtq_count} LGBTQ+-related items out of {total_count} total ({lgbtq_count / total_count * 100:.1f}%)"
        )

        return df

    def identify_context(self, text: str) -> Dict[str, bool]:
        """Identify specific LGBTQ+ contexts in the text"""
        if not text:
            return {}

        text_lower = text.lower()
        contexts = {}

        # Check each identity context
        for identity, terms in self.identity_terms.items():
            contexts[identity] = any(term.lower() in text_lower for term in terms)

        # Additional context detection
        contexts["general_lgbtq"] = any(
            keyword.lower() in text_lower for keyword in self.lgbtq_keywords
        )
        contexts["health_related"] = any(
            term in text_lower
            for term in ["health", "mental", "therapy", "doctor", "clinic"]
        )
        contexts["dating"] = any(
            term in text_lower
            for term in ["dating", "relationship", "partner", "boyfriend", "girlfriend"]
        )
        contexts["coming_out"] = any(
            term in text_lower
            for term in ["coming out", "out of the closet", "told my family"]
        )

        return contexts

    def contains_lgbtq_keywords(self, text: str) -> bool:
        """Check if text contains LGBTQ+-related keywords (for testing)"""
        if not text:
            return False

        text_lower = text.lower()

        # Direct keyword matching
        for keyword in self.lgbtq_keywords:
            if keyword.lower() in text_lower:
                return True

        # Context indicators
        for indicator in self.context_indicators:
            if indicator.lower() in text_lower:
                return True

        # Identity-specific patterns
        for identity, terms in self.identity_terms.items():
            for term in terms:
                if term.lower() in text_lower:
                    return True

        # Advanced patterns for context awareness
        lgbtq_patterns = [
            r"\b(gay|bi|trans|queer|lesbian)\b.*\b(man|men|woman|women|people|community)\b",
            r"\b(attracted to|dating|interested in)\b.*\b(both|men|women|same sex)\b",
            r"\b(coming out|out of the closet)\b.*\b(as|to my)\b",
            r"\b(my|his|her)\b.*\b(boyfriend|girlfriend|partner)\b.*\b(is|was)\b",
            r"\b(pride|rainbow|lgbt)\b.*\b(month|flag|parade|event)\b",
            r"\b(gay|bi|trans)\b.*\b(rights|equality|marriage|law)\b",
        ]

        for pattern in lgbtq_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

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
        """Train the LGBTQ+ content classification model"""
        logger.info("Training LGBTQ+ content classifier...")

        # Preprocess text
        df["processed_text"] = df["text"].apply(self.preprocess_text)

        # Remove empty texts
        df = df[df["processed_text"].str.len() > 10]

        # Prepare features and labels
        X = df["processed_text"]
        y = df["is_lgbtq_related"]

        # Check class distribution
        class_dist = y.value_counts()
        logger.info(
            f"Class distribution: LGBTQ+={class_dist.get(True, 0)}, General={class_dist.get(False, 0)}"
        )

        if len(class_dist) < 2:
            raise ValueError(
                "Need both LGBTQ+-related and general content for training"
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
                "lgbtq_related": int(class_dist.get(True, 0)),
                "general": int(class_dist.get(False, 0)),
            },
        }

        logger.info(f"Training completed - Test Accuracy: {test_score:.3f}")
        logger.info(f"Classification Report:\n{classification_report(y_test, y_pred)}")

        return results

    def predict_lgbtq_content(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Predict whether texts are LGBTQ+-related with context awareness"""
        if not self.pipeline:
            raise ValueError("Model not trained yet. Call train_model() first.")

        processed_texts = [self.preprocess_text(text) for text in texts]
        predictions = self.pipeline.predict(processed_texts)
        probabilities = self.pipeline.predict_proba(processed_texts)

        results = []
        for i, (text, pred, prob) in enumerate(zip(texts, predictions, probabilities)):
            # Get context information
            contexts = self.identify_context(text)

            results.append(
                {
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "is_lgbtq_related": bool(pred),
                    "confidence": float(max(prob)),
                    "lgbtq_probability": float(prob[1]) if len(prob) > 1 else 0.0,
                    "general_probability": float(prob[0]) if len(prob) > 1 else 1.0,
                    "contexts": contexts,
                    "primary_context": self._get_primary_context(contexts),
                }
            )

        return results

    def _get_primary_context(self, contexts: Dict[str, bool]) -> str:
        """Determine the primary LGBTQ+ context from detected contexts"""
        # Priority order for contexts
        priority_order = ["gay", "bi", "msm", "lesbian", "trans", "general_lgbtq"]

        for context in priority_order:
            if contexts.get(context, False):
                return context

        return "general_lgbtq" if contexts.get("general_lgbtq", False) else "unknown"

    def get_top_lgbtq_features(self, n: int = 20) -> List[Tuple[str, float]]:
        """Get the most important features for LGBTQ+ classification"""
        if not self.pipeline:
            return []

        feature_names = self.pipeline.named_steps["tfidf"].get_feature_names_out()
        coefficients = self.pipeline.named_steps["classifier"].coef_[0]

        # Get top positive coefficients (LGBTQ+-related features)
        feature_importance = list(zip(feature_names, coefficients))
        feature_importance.sort(key=lambda x: x[1], reverse=True)

        return feature_importance[:n]

    def save_model(self, filepath: str = "models/lgbtq_classifier.pkl"):
        """Save the trained model"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            "pipeline": self.pipeline,
            "trained_at": datetime.now().isoformat(),
            "lgbtq_keywords": self.lgbtq_keywords,
            "identity_terms": self.identity_terms,
            "context_indicators": self.context_indicators,
        }

        with open(filepath, "wb") as f:
            pickle.dump(model_data, f)

        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str = "models/lgbtq_classifier.pkl"):
        """Load a trained model"""
        with open(filepath, "rb") as f:
            model_data = pickle.load(f)

        self.pipeline = model_data["pipeline"]
        self.lgbtq_keywords = model_data["lgbtq_keywords"]
        self.identity_terms = model_data["identity_terms"]
        self.context_indicators = model_data["context_indicators"]

        logger.info(f"Model loaded from {filepath}")


def train_lgbtq_classifier():
    """Main function to train the LGBTQ+ content classifier"""
    logger.info("🏳️‍🌈 Starting LGBTQ+ Content Classifier Training")
    logger.info("=" * 50)

    classifier = LGBTQContentClassifier()

    # Load data
    df = classifier.load_training_data()

    if len(df) == 0:
        logger.error("No data found in database. Run data collection first.")
        return

    # Create labels
    df = classifier.create_lgbtq_labels(df)

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
    print(f"  LGBTQ+-related: {results['class_distribution']['lgbtq_related']}")
    print(f"  General: {results['class_distribution']['general']}")

    print("\nTop LGBTQ+-Related Features:")
    top_features = classifier.get_top_lgbtq_features(15)
    for feature, importance in top_features:
        print(f"  {feature}: {importance:.3f}")

    # Test on some examples
    print("\n🧪 Testing on Sample Texts:")
    test_texts = [
        "Just came out to my family as gay, feeling nervous",
        "Anyone know good restaurants in Toronto?",
        "My boyfriend and I are planning our wedding",
        "Looking for advice on dating apps for bi people",
        "What's the best way to invest in crypto?",
    ]

    predictions = classifier.predict_lgbtq_content(test_texts)
    for pred in predictions:
        lgbtq_status = "LGBTQ+" if pred["is_lgbtq_related"] else "GENERAL"
        context = (
            f" ({pred['primary_context']})"
            if pred["primary_context"] != "unknown"
            else ""
        )
        print(f"  [{lgbtq_status}{context}] ({pred['confidence']:.2f}) {pred['text']}")

    print("\n✅ Model training complete! Saved to models/lgbtq_classifier.pkl")
    return classifier


if __name__ == "__main__":
    train_lgbtq_classifier()
