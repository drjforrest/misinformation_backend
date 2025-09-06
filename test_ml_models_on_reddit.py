#!/usr/bin/env python3
"""
Test script for ML models on Reddit data
Samples posts from Reddit and tests both the health content classifier and LGBTQ+ content classifier
"""

import json
import time
from datetime import datetime
from typing import List, Dict

from src.reddit_scraper import RedditScraper
from src.health_content_classifier import HealthContentClassifier
from src.lgbtq_content_classifier import LGBTQContentClassifier
from src.data_persistence import DataPersistenceManager


def test_models_on_reddit_data():
    """Test both ML models on sampled Reddit data"""
    print("🧪 Testing ML Models on Reddit Data")
    print("=" * 50)

    # Initialize scrapers and classifiers
    scraper = RedditScraper()
    health_classifier = HealthContentClassifier()
    lgbtq_classifier = LGBTQContentClassifier()

    # Try to load trained models
    try:
        health_classifier.load_model()
        print("✅ Loaded health content classifier model")
    except FileNotFoundError:
        print("⚠️  Health content classifier model not found. Will train one.")
        # We'll train it later with collected data
        health_classifier = None

    try:
        lgbtq_classifier.load_model()
        print("✅ Loaded LGBTQ+ content classifier model")
    except FileNotFoundError:
        print("⚠️  LGBTQ+ content classifier model not found. Will train one.")
        # We'll train it later with collected data
        lgbtq_classifier = None

    # Target subreddits for testing
    # Mix of LGBTQ+-focused and general population subreddits
    target_subreddits = [
        # LGBTQ+-focused subreddits
        "askgaybros",
        "gaybros",
        "lgbt",
        "ainbow",
        "torontogaybros",
        # General population subreddits where health discussions happen
        "toronto",
        "NewToCanada",
        "relationship_advice",
        "TooAfraidToAsk",
        "NoStupidQuestions",
        "CasualConversation",
        "PersonalFinanceCanada",
    ]

    print(f"\n📡 Sampling from {len(target_subreddits)} subreddits...")

    # Collect sample data
    all_posts = []
    for subreddit in target_subreddits:
        print(f"\n🔍 Collecting from r/{subreddit}...")
        posts = scraper.scrape_subreddit(subreddit, limit=30)

        if posts:
            all_posts.extend(posts)
            print(f"   Collected {len(posts)} posts")
        else:
            print(f"   No posts found")

        # Rate limiting
        time.sleep(2)

    print(f"\n📊 Total collected: {len(all_posts)} posts")

    # Save raw data for later analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_data_path = f"data/model_test_raw_data_{timestamp}.json"
    with open(raw_data_path, "w") as f:
        json.dump(all_posts, f, indent=2, default=str)
    print(f"💾 Raw data saved to: {raw_data_path}")

    # Process posts for model testing
    test_texts = []
    post_metadata = []

    for post in all_posts:
        text = f"{post['title']} {post['selftext'] or ''}"
        if len(text.strip()) > 10:  # Filter very short posts
            test_texts.append(text)
            post_metadata.append(
                {
                    "post_id": post["post_id"],
                    "subreddit": post["subreddit"],
                    "title": post["title"],
                    "author": post["author"],
                    "score": post["score"],
                    "language": post["language"],
                    "is_newcomer_related": post["is_newcomer_related"],
                }
            )

    print(f"\n📝 Prepared {len(test_texts)} texts for model testing")

    # Test health content classifier
    if health_classifier:
        print("\n" + "=" * 50)
        print("🏥 Health Content Classifier Results")
        print("=" * 50)

        health_predictions = health_classifier.predict_health_content(test_texts)

        # Count health-related posts
        health_count = sum(
            1 for pred in health_predictions if pred["is_health_related"]
        )
        health_percentage = (
            (health_count / len(health_predictions)) * 100 if health_predictions else 0
        )

        print(
            f"Health-related posts: {health_count}/{len(health_predictions)} ({health_percentage:.1f}%)"
        )

        # Show sample results
        print("\nSample predictions (health-related):")
        health_samples = [
            pred for pred in health_predictions if pred["is_health_related"]
        ]
        for i, pred in enumerate(health_samples[:5]):
            print(f"  {i+1}. [{pred['confidence']:.2f}] {pred['text'][:100]}...")

        print("\nSample predictions (general):")
        general_samples = [
            pred for pred in health_predictions if not pred["is_health_related"]
        ]
        for i, pred in enumerate(general_samples[:5]):
            print(f"  {i+1}. [{pred['confidence']:.2f}] {pred['text'][:100]}...")
    else:
        print("\n⚠️  Health content classifier not available for testing")
        health_predictions = None

    # Test LGBTQ+ content classifier
    if lgbtq_classifier:
        print("\n" + "=" * 50)
        print("🏳️‍🌈 LGBTQ+ Content Classifier Results")
        print("=" * 50)

        lgbtq_predictions = lgbtq_classifier.predict_lgbtq_content(test_texts)

        # Count LGBTQ+-related posts
        lgbtq_count = sum(1 for pred in lgbtq_predictions if pred["is_lgbtq_related"])
        lgbtq_percentage = (
            (lgbtq_count / len(lgbtq_predictions)) * 100 if lgbtq_predictions else 0
        )

        print(
            f"LGBTQ+-related posts: {lgbtq_count}/{len(lgbtq_predictions)} ({lgbtq_percentage:.1f}%)"
        )

        # Show sample results by context
        contexts = {}
        for pred in lgbtq_predictions:
            if pred["is_lgbtq_related"]:
                context = pred["primary_context"]
                if context not in contexts:
                    contexts[context] = []
                contexts[context].append(pred)

        for context, preds in contexts.items():
            print(f"\n{context.upper()} context samples:")
            for i, pred in enumerate(preds[:3]):
                print(f"  {i+1}. [{pred['confidence']:.2f}] {pred['text'][:100]}...")
    else:
        print("\n⚠️  LGBTQ+ content classifier not available for testing")
        lgbtq_predictions = None

    # Save results
    results = {
        "test_timestamp": timestamp,
        "total_posts": len(all_posts),
        "test_texts_count": len(test_texts),
        "target_subreddits": target_subreddits,
        "health_classifier_available": health_classifier is not None,
        "lgbtq_classifier_available": lgbtq_classifier is not None,
        "health_predictions": health_predictions,
        "lgbtq_predictions": lgbtq_predictions,
        "post_metadata": post_metadata,
    }

    results_path = f"data/model_test_results_{timestamp}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Full results saved to: {results_path}")

    # Summary
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    print(f"Total posts collected: {len(all_posts)}")
    print(f"Posts processed for testing: {len(test_texts)}")
    print(f"Health classifier available: {'Yes' if health_classifier else 'No'}")
    print(f"LGBTQ+ classifier available: {'Yes' if lgbtq_classifier else 'No'}")

    if health_predictions:
        health_count = sum(
            1 for pred in health_predictions if pred["is_health_related"]
        )
        print(
            f"Health-related posts detected: {health_count}/{len(health_predictions)} ({(health_count/len(health_predictions)*100):.1f}%)"
        )

    if lgbtq_predictions:
        lgbtq_count = sum(1 for pred in lgbtq_predictions if pred["is_lgbtq_related"])
        print(
            f"LGBTQ+-related posts detected: {lgbtq_count}/{len(lgbtq_predictions)} ({(lgbtq_count/len(lgbtq_predictions)*100):.1f}%)"
        )

    print(f"\nNext steps:")
    print(f"1. Review results in: {results_path}")
    print(f"2. Train models with collected data if needed")
    print(f"3. Adjust classification thresholds based on results")

    return results


def train_models_with_collected_data():
    """Train both models with the newly collected data"""
    print("\n🤖 Training Models with Collected Data")
    print("=" * 50)

    # For now, we'll need to save the collected data to database first
    # Then train models using the database data
    print("To train models with collected data:")
    print("1. Run data collection with database persistence:")
    print("   python main.py collect-db")
    print("2. Train health content classifier:")
    print("   python src/health_content_classifier.py")
    print("3. Train LGBTQ+ content classifier:")
    print("   python src/lgbtq_content_classifier.py")


if __name__ == "__main__":
    # Run the test
    results = test_models_on_reddit_data()

    # Show training instructions
    train_models_with_collected_data()
