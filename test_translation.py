#!/usr/bin/env python3
"""
Test translation service to verify ML models are working correctly
"""

from src.translation_service import get_translation_service


def test_translation_service():
    """Test the translation service with sample texts"""
    print("🌐 Testing Translation Service")
    print("=" * 40)

    service = get_translation_service()

    # Test language detection
    test_texts = [
        "Hello, I'm new to Canada and need health information",
        "Hola, soy nuevo en Canadá y necesito información de salud",
        "你好，我是加拿大新移民，需要健康信息",
        "Kamusta, bago ako sa Canada at kailangan ko ng health information",
    ]

    for text in test_texts:
        lang = service.detect_language(text)
        translation = service.translate_text(text, target_lang="en")
        print(f"Text: {text}")
        print(f"Language: {lang}")
        print(f"Translation: {translation['translation']}")
        print(f"Backend: {translation['backend_used']}")
        print()

    # Test keyword translation
    print("🔑 Testing health keyword translations...")
    translations = service.translate_health_keywords()

    print(f"✅ Translated keywords to {len(translations)} languages")
    for lang, trans in translations.items():
        print(f"{lang}: {len(trans)} keywords")

    service.close()


if __name__ == "__main__":
    test_translation_service()
