#!/usr/bin/env python3
"""
Test script for the new LGBTQ+ Content Classifier
Demonstrates the functionality of the LGBTQ+ classifier on general population subreddits
"""

from config.settings import ResearchConfig
from src.lgbtq_content_classifier import LGBTQContentClassifier


def test_lgbtq_classifier():
    """Test the LGBTQ+ classifier with sample data"""
    print("Testing LGBTQ+ Content Classifier")
    print("=" * 50)

    # Initialize classifier
    classifier = LGBTQContentClassifier()

    # Test with sample texts that might appear in general population subreddits
    test_texts = [
        "Just came out to my family as gay, feeling nervous about their reaction",
        "Anyone know good restaurants in Toronto for date night?",
        "My boyfriend and I are planning our wedding next year",
        "Looking for advice on dating apps for bisexual people",
        "What's the best way to invest in crypto?",
        "As a trans woman, I'm having trouble finding the right healthcare provider",
        "The pride parade in Vancouver was amazing this year",
        "Men who have sex with men should get tested regularly for STIs",
        "How do I support my gay friend who's going through a tough time?",
        "Planning a trip to Montreal with my partner",
        "The new LGBTQ+ rights legislation is a step forward",
        "Anyone else here attracted to both men and women?",
        "My son came out as gay and I want to be supportive",
        "What's the weather like in Calgary this time of year?",
        "Transgender healthcare access is still limited in many places",
    ]

    print("\nTesting Classifier on Sample Texts:")
    print("-" * 40)

    # First test with rule-based keyword detection
    print("Testing with rule-based keyword detection:")
    lgbtq_count = 0
    for i, text in enumerate(test_texts):
        is_lgbtq = classifier.contains_lgbtq_keywords(text)
        context = classifier.identify_context(text)
        primary_context = classifier._get_primary_context(context)

        status = "LGBTQ+" if is_lgbtq else "GENERAL"
        context_str = f" ({primary_context})" if primary_context != "unknown" else ""

        print(
            f"{i + 1:2d}. [{status}{context_str}] {text[:80]}{'...' if len(text) > 80 else ''}"
        )

        if is_lgbtq:
            lgbtq_count += 1

    print("\nRule-based Summary:")
    print(f"   Total texts: {len(test_texts)}")
    print(f"   LGBTQ+-related: {lgbtq_count}")
    print(f"   General: {len(test_texts) - lgbtq_count}")
    print(f"   Percentage LGBTQ+: {(lgbtq_count / len(test_texts) * 100):.1f}%")

    # Try to train and test with ML model
    print("\n" + "=" * 50)
    print("Testing with ML model (if trained):")

    try:
        # Try to load existing model
        classifier.load_model()
        print("Loaded existing ML model")

        predictions = classifier.predict_lgbtq_content(test_texts)

        ml_lgbtq_count = 0
        for i, pred in enumerate(predictions):
            status = "LGBTQ+" if pred["is_lgbtq_related"] else "GENERAL"
            context = (
                f" ({pred['primary_context']})"
                if pred["primary_context"] != "unknown"
                else ""
            )
            confidence = f"{pred['confidence']:.2f}"

            print(
                f"{i + 1:2d}. [{status}{context}] ({confidence}) {pred['text'][:80]}{'...' if len(pred['text']) > 80 else ''}"
            )

            if pred["is_lgbtq_related"]:
                ml_lgbtq_count += 1

        print("\nML Model Summary:")
        print(f"   Total texts: {len(test_texts)}")
        print(f"   LGBTQ+-related: {ml_lgbtq_count}")
        print(f"   General: {len(test_texts) - ml_lgbtq_count}")
        print(f"   Percentage LGBTQ+: {(ml_lgbtq_count / len(test_texts) * 100):.1f}%")

    except Exception as e:
        print(f"No trained ML model available: {e}")
        print("To train the ML model:")
        print("   1. Collect training data: python src/lgbtq_scraper.py")
        print("   2. Train the model: python src/lgbtq_content_classifier.py")

    return classifier


def test_lgbtq_keywords():
    """Test the LGBTQ+ keyword detection"""
    print("\nTesting LGBTQ+ Keyword Detection")
    print("=" * 40)

    classifier = LGBTQContentClassifier()

    test_texts = [
        "I'm gay and looking for relationship advice",
        "The pride flag has rainbow colors",
        "Transgender rights are human rights",
        "Bi people exist and are valid",
        "Lesbian relationships are beautiful",
        "This post has no LGBTQ content",
        "Regular conversation about weather",
    ]

    print("Keyword Detection Results:")
    for text in test_texts:
        has_keywords = classifier.contains_lgbtq_keywords(text)
        status = "LGBTQ+" if has_keywords else "General"
        print(f"   {status}: {text[:60]}{'...' if len(text) > 60 else ''}")


def demonstrate_training_data_collection():
    """Demonstrate how to collect training data from general population subreddits"""
    print("\nTraining Data Collection Strategy")
    print("=" * 40)

    print("Target Subreddits for LGBTQ+ Content Collection:")
    for i, sub in enumerate(ResearchConfig.GENERAL_POPULATION_SUBREDDITS[:10], 1):
        print(f"   {i:2d}. r/{sub}")

    print("\nLGBTQ+ Keywords for Detection:")
    for i, keyword in enumerate(ResearchConfig.LGBTQ_KEYWORDS[:15], 1):
        print(f"   {i:2d}. {keyword}")

    print("\nCollection Strategy:")
    print("   1. Scrape posts from general population subreddits")
    print("   2. Filter posts containing LGBTQ+ keywords")
    print("   3. Use ML classifier to identify context-aware content")
    print("   4. Train model on labeled data")
    print("   5. Deploy for automated classification")


if __name__ == "__main__":
    # Run all tests
    classifier = test_lgbtq_classifier()
    test_lgbtq_keywords()
    demonstrate_training_data_collection()

    print("\nLGBTQ+ Classifier Testing Complete!")
    print("\nTo use in production:")
    print("   1. Run: python src/lgbtq_scraper.py")
    print("   2. Train: python src/lgbtq_content_classifier.py")
    print("   3. Analyze: Use analytics dashboard with LGBTQ+ features")
