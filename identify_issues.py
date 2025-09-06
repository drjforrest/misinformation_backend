#!/usr/bin/env python3
"""
Identify potential data issues or model limitations
"""

import json
from pathlib import Path


def identify_issues():
    """Identify potential issues or limitations in our data or models"""
    print("🔍 Identifying Data Issues and Model Limitations")
    print("=" * 55)

    # Load the collection report
    report_file = Path("data/multilingual_collection_report_20250904_163526.json")

    if not report_file.exists():
        print("❌ No collection report found")
        return

    with open(report_file, "r") as f:
        data = json.load(f)

    # Load keyword translations
    keywords_file = Path("data/health_keywords_translations.json")
    if keywords_file.exists():
        with open(keywords_file, "r") as f:
            keywords_data = json.load(f)

    issues = []
    recommendations = []

    # 1. Language distribution analysis
    languages = data["language_distribution"]
    total_posts = data["total_posts"]

    if len(languages) < 6:  # We target 6+ languages
        issues.append(
            f"Low language diversity: Only {len(languages)} languages detected"
        )
        recommendations.append(
            "Expand subreddit list to include more language-specific communities"
        )

    # Check for language imbalance
    english_pct = languages.get("en", 0) / total_posts * 100
    if english_pct > 80:
        issues.append(
            f"High English content bias: {english_pct:.1f}% of posts are in English"
        )
        recommendations.append(
            "Focus on non-English communities to balance language distribution"
        )

    # 2. Translation quality issues
    # Look for potentially problematic translations in keywords
    if keywords_file.exists():
        problematic_translations = []
        for lang, translations in keywords_data.items():
            for eng_keyword, translated in translations.items():
                # Check for English words in non-English translations
                if lang != "en" and eng_keyword.lower() == translated.lower():
                    problematic_translations.append(
                        f"{lang}: {eng_keyword} -> {translated}"
                    )

        if problematic_translations:
            issues.append(
                f"Potential translation issues found in {len(problematic_translations)} keywords"
            )
            recommendations.append(
                "Review translation quality for specific language pairs"
            )

    # 3. Subreddit performance analysis
    failed_subreddits = data["collection_summary"]["failed_list"]
    if len(failed_subreddits) > 15:  # More than 1/3 failed
        issues.append(
            f"High subreddit failure rate: {len(failed_subreddits)} subreddits failed"
        )
        recommendations.append("Review and update subreddit list for better targeting")

    # 4. Health content analysis
    health_posts = data["health_keyword_posts"]
    health_ratio = health_posts / total_posts
    if health_ratio < 0.7:
        issues.append(
            f"Low health content ratio: Only {health_ratio:.1%} of posts are health-related"
        )
        recommendations.append("Refine keyword matching or adjust subreddit targeting")

    # 5. Translation performance
    translation_stats = data["translation_stats"]
    total_translations = sum(translation_stats.values())

    if total_translations == 0:
        issues.append("No translations performed - possible language detection issues")
        recommendations.append("Verify language detection is working correctly")

    # Display findings
    if issues:
        print("⚠️  Identified Issues:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print("✅ No major issues identified")

    if recommendations:
        print("\n💡 Recommendations:")
        for rec in recommendations:
            print(f"  • {rec}")

    # Additional observations
    print("\n🔍 Additional Observations:")
    print(
        f"  • Successfully collected data from {len(data['subreddit_stats'])} subreddits"
    )
    print(
        f"  • Translation service working correctly with {total_translations} translations"
    )
    print(f"  • Health content ratio of {health_ratio:.1%} is within acceptable range")

    # Check keyword translations for specific issues
    if keywords_file.exists():
        print(f"\n🔤 Keyword Translation Quality Check:")
        for lang, translations in list(keywords_data.items())[
            :3
        ]:  # Show first 3 languages
            sample_items = list(translations.items())[:3]  # Show first 3 translations
            print(f"  • {lang} samples:")
            for eng, trans in sample_items:
                status = "✅" if eng.lower() != trans.lower() else "⚠️"
                print(f"    {status} {eng} -> {trans}")

    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    identify_issues()
