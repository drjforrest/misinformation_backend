#!/usr/bin/env python3
"""
Validate findings and test potential improvements
"""

from src.translation_service import get_translation_service


def test_improvements():
    """Test potential improvements to translation quality"""
    print("🧪 Testing Translation Improvements")
    print("=" * 40)

    service = get_translation_service()

    # Test specific problematic terms
    test_cases = [
        # Tagalog issues
        ("PrEP", "tl", "Prep"),  # Currently identical
        ("ARVs", "tl", "ARVS"),  # Currently identical
        ("doxy", "tl", "Doxy"),  # Currently identical
        # Spanish issues
        ("doxy", "es", "doxy"),  # Currently identical
        # French issues
        ("doxy", "fr", "doxy"),  # Currently identical
        # Terms that worked well
        ("HIV", "tl", "HIV"),  # Should stay the same
        ("HIV", "es", "VIH"),  # Worked well
    ]

    print("🔍 Testing specific translation cases:")
    for term, lang, current_translation in test_cases:
        # Try direct translation
        result = service.translate_text(term, target_lang=lang, source_lang="en")
        new_translation = result.get("translation", "")

        status = (
            "✅"
            if new_translation.lower() != term.lower()
            and new_translation != current_translation
            else "⚠️"
        )
        print(
            f"  {status} {term} ({lang}): '{current_translation}' -> '{new_translation}'"
        )

    # Test with different backends if available
    print(f"\n🔄 Testing different translation backends:")

    # Test a few terms with different backends
    test_terms = ["PrEP", "ARVs", "doxy"]
    test_languages = ["tl", "es", "fr"]

    for term in test_terms:
        for lang in test_languages:
            result = service.translate_text(term, target_lang=lang, source_lang="en")
            translation = result.get("translation", "")
            backend = result.get("backend_used", "unknown")
            confidence = result.get("confidence", 0.0)

            if translation.lower() == term.lower():
                print(
                    f"  ⚠️ {term}->{lang}: '{translation}' (backend: {backend}, confidence: {confidence})"
                )

    service.close()

    # Recommendations for improvement
    print(f"\n💡 Improvement Recommendations:")
    print(f"  1. Create language-specific health term dictionaries")
    print(f"  2. Implement manual validation for technical terms")
    print(f"  3. Consider using specialized medical translation APIs")
    print(f"  4. Add fallback mechanisms for poor quality translations")
    print(f"  5. Implement confidence threshold filtering")

    print(f"\n✅ Testing complete!")


if __name__ == "__main__":
    test_improvements()
