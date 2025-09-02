#!/usr/bin/env python3
"""
Simple test script for translation functionality
"""

import os
import sys

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from langdetect import detect
from src.translation_service import get_translation_service


def test_basic_translation():
    """Test basic translation capabilities"""
    print("🌐 Testing Basic Translation")
    print("=" * 40)

    # Test language detection with langdetect
    test_texts = [
        ("Hello, I need health information", "en"),
        ("Hola, necesito información de salud", "es"),
        ("你好，我需要健康信息", "zh"),
        ("Kamusta, kailangan ko ng health information", "tl"),
    ]

    print("1. Testing language detection:")
    for text, expected in test_texts:
        try:
            detected = detect(text)
            status = "✅" if detected.startswith(expected) else "⚠️"
            print(f"   {status} '{text[:30]}...' -> {detected} (expected: {expected})")
        except Exception as e:
            print(f"   ❌ Error detecting language for '{text[:30]}...': {e}")

    print()

    # Test Translation Service
    print("2. Testing Translation Service:")
    translation_service = get_translation_service()

    for text, lang in test_texts[:3]:  # Test first three to avoid rate limiting
        if lang == "en":  # Skip English
            continue
        try:
            result = translation_service.translate_text(text, target_lang="en", source_lang=lang)
            if not result.get("error"):
                print(f"   ✅ '{text}' -> '{result['translation']}'")
                print(f"      Backend: {result['backend_used']}, Confidence: {result['confidence']}")
            else:
                print(f"   ❌ Translation failed: {result['error']}")
        except Exception as e:
            print(f"   ❌ Translation failed: {e}")

        print()

    print("✅ Basic translation test complete")


def test_health_keyword_translation():
    """Test translating health keywords"""
    print("\n🔑 Testing Health Keywords Translation")
    print("=" * 45)

    translation_service = get_translation_service()

    # Sample health keywords
    keywords = ["HIV", "PrEP", "testing", "symptoms", "medication", "treatment"]
    target_languages = ["es", "zh-CN", "tl", "fr"]  # Spanish, Chinese, Tagalog, French

    for keyword in keywords[:3]:  # Test first few keywords
        print(f"\nTranslating '{keyword}':")
        for lang in target_languages:
            try:
                result = translation_service.translate_text(keyword, target_lang=lang, source_lang="en")
                if not result.get("error"):
                    print(f"   {lang}: {result['translation']} (backend: {result['backend_used']})")
                else:
                    print(f"   {lang}: ❌ Error - {result['error']}")
            except Exception as e:
                print(f"   {lang}: ❌ Error - {e}")

    print("\n✅ Health keywords translation test complete")


if __name__ == "__main__":
    test_basic_translation()
    test_health_keyword_translation()
