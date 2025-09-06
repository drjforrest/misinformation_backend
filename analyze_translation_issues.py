#!/usr/bin/env python3
"""
Detailed analysis of translation issues and model limitations
"""

import json
from pathlib import Path


def analyze_translation_issues():
    """Analyze specific translation issues in detail"""
    print("🔍 Detailed Translation Issues Analysis")
    print("=" * 45)

    # Load keyword translations
    keywords_file = Path("data/health_keywords_translations.json")
    if not keywords_file.exists():
        print("❌ No keyword translations file found")
        return

    with open(keywords_file, "r") as f:
        keywords_data = json.load(f)

    # Identify specific issues
    identical_translations = {}
    empty_translations = {}

    for lang, translations in keywords_data.items():
        identical_translations[lang] = []
        empty_translations[lang] = []

        for eng_keyword, translated in translations.items():
            # Check for identical translations (same as English)
            if eng_keyword.lower() == translated.lower():
                identical_translations[lang].append((eng_keyword, translated))

            # Check for empty/meaningless translations
            if not translated or translated.strip() == "":
                empty_translations[lang].append((eng_keyword, translated))

    # Display identical translations
    print("🔄 Identical Translations (Same as English):")
    total_identical = 0
    for lang, translations in identical_translations.items():
        if translations:
            print(f"  {lang}:")
            for eng, trans in translations[:5]:  # Show first 5
                print(f"    • {eng} -> {trans}")
            if len(translations) > 5:
                print(f"    ... and {len(translations) - 5} more")
            total_identical += len(translations)

    if total_identical == 0:
        print("  ✅ No identical translations found")

    # Display empty translations
    print("\nEmptyEntries/Invalid Translations:")
    total_empty = 0
    for lang, translations in empty_translations.items():
        if translations:
            print(f"  {lang}:")
            for eng, trans in translations:
                print(f"    • {eng} -> '{trans}'")
            total_empty += len(translations)

    if total_empty == 0:
        print("  ✅ No empty translations found")

    # Analyze specific problematic cases
    print("\n🔍 Problematic Translation Analysis:")

    # Tagalog issues
    if "tl" in keywords_data:
        tl_translations = keywords_data["tl"]
        print(f"  Tagalog (tl):")
        problematic_tl = [
            ("PrEP", tl_translations.get("PrEP")),
            ("ARVs", tl_translations.get("ARVs")),
            ("doxy", tl_translations.get("doxy")),
            ("PEP", tl_translations.get("PEP")),
        ]
        for eng, trans in problematic_tl:
            if trans and eng.lower() == trans.lower():
                print(f"    ⚠️ '{eng}' translated as '{trans}' (identical)")
            elif not trans:
                print(f"    ⚠️ '{eng}' has no translation")
            else:
                print(f"    ✅ '{eng}' -> '{trans}'")

    # Spanish issues
    if "es" in keywords_data:
        es_translations = keywords_data["es"]
        print(f"  Spanish (es):")
        problematic_es = [
            ("PrEP", es_translations.get("PrEP")),
            ("doxy", es_translations.get("doxy")),
            ("PEP", es_translations.get("PEP")),
        ]
        for eng, trans in problematic_es:
            if trans and eng.lower() == trans.lower():
                print(f"    ⚠️ '{eng}' translated as '{trans}' (identical)")
            elif not trans:
                print(f"    ⚠️ '{eng}' has no translation")
            else:
                print(f"    ✅ '{eng}' -> '{trans}'")

    # French issues
    if "fr" in keywords_data:
        fr_translations = keywords_data["fr"]
        print(f"  French (fr):")
        problematic_fr = [
            ("doxy", fr_translations.get("doxy")),
            ("PEP", fr_translations.get("PEP")),
        ]
        for eng, trans in problematic_fr:
            if trans and eng.lower() == trans.lower():
                print(f"    ⚠️ '{eng}' translated as '{trans}' (identical)")
            elif not trans:
                print(f"    ⚠️ '{eng}' has no translation")
            else:
                print(f"    ✅ '{eng}' -> '{trans}'")

    # Summary
    print(f"\n📊 Summary:")
    print(f"  • Total languages analyzed: {len(keywords_data)}")
    print(f"  • Identical translations: {total_identical}")
    print(f"  • Empty translations: {total_empty}")

    # Recommendations based on findings
    print(f"\n💡 Recommendations:")
    if total_identical > 0:
        print(
            f"  • Review translation service configuration for language-specific handling"
        )
        print(
            f"  • Consider using specialized medical translation services for health terms"
        )
        print(f"  • Implement validation for translation quality")

    if "tl" in keywords_data and len(identical_translations.get("tl", [])) > 3:
        print(
            f"  • Tagalog translations need special attention - many terms are not properly translated"
        )

    if "es" in keywords_data and len(identical_translations.get("es", [])) > 2:
        print(f"  • Spanish translations for technical terms need improvement")

    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    analyze_translation_issues()
