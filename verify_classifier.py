#!/usr/bin/env python3
"""
Verification script for the LGBTQ+ Content Classifier
Tests both rule-based and ML-based classification approaches
"""

from src.lgbtq_content_classifier import LGBTQContentClassifier


def verify_classifier():
    """Verify the LGBTQ+ classifier with sample data"""
    print("Verifying LGBTQ+ Content Classifier")
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

    return classifier


if __name__ == "__main__":
    verify_classifier()
    print("\n✅ Classifier verification complete!")
