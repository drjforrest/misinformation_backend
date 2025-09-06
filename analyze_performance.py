#!/usr/bin/env python3
"""
Analyze model performance metrics from recent data collection
"""

import json
from pathlib import Path


def analyze_performance():
    """Analyze the performance metrics from our recent collection"""
    print("📊 Analyzing Model Performance Metrics")
    print("=" * 50)

    # Load the collection report
    report_file = Path("data/multilingual_collection_report_20250904_163526.json")

    if not report_file.exists():
        print("❌ No collection report found")
        return

    with open(report_file, "r") as f:
        data = json.load(f)

    # Overall statistics
    total_posts = data["total_posts"]
    health_posts = data["health_keyword_posts"]
    languages = data["language_distribution"]
    translation_stats = data["translation_stats"]

    print(f"📈 Overall Collection Statistics:")
    print(f"  • Total posts collected: {total_posts}")
    print(
        f"  • Health-related posts: {health_posts} ({health_posts/total_posts*100:.1f}%)"
    )
    print(f"  • Languages detected: {len(languages)}")

    print(f"\n🌍 Language Distribution:")
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {lang}: {count} posts ({count/total_posts*100:.1f}%)")

    # Translation performance
    total_translations = sum(translation_stats.values())
    if total_translations > 0:
        success_rate = translation_stats["success"] / total_translations * 100
        print(f"\n🔄 Translation Performance:")
        print(f"  • Success rate: {success_rate:.1f}%")
        print(f"  • Successful translations: {translation_stats['success']}")
        print(f"  • Failed translations: {translation_stats['failed']}")
        print(f"  • Cached translations: {translation_stats['cached']}")

    # Per-subreddit analysis
    print(f"\n🏆 Top Performing Subreddits:")
    subreddit_stats = data["subreddit_stats"]
    top_subreddits = sorted(
        subreddit_stats.items(),
        key=lambda x: (x[1]["translations"], x[1]["post_count"]),
        reverse=True,
    )[:5]

    for subreddit, stats in top_subreddits:
        print(
            f"  • r/{subreddit}: {stats['post_count']} posts, {stats['translations']} translations"
        )

    # Language-specific translation quality
    print(f"\nQuality Analysis by Language:")
    language_quality = {}

    for subreddit, stats in subreddit_stats.items():
        for lang, count in stats["languages"].items():
            if lang not in language_quality:
                language_quality[lang] = {
                    "posts": 0,
                    "translations": 0,
                    "confidence_sum": 0,
                    "confidence_count": 0,
                }

            language_quality[lang]["posts"] += count
            language_quality[lang]["translations"] += stats["translations"]

            if "avg_confidence" in stats and stats["avg_confidence"] > 0:
                language_quality[lang]["confidence_sum"] += (
                    stats["avg_confidence"] * count
                )
                language_quality[lang]["confidence_count"] += count

    for lang, quality in language_quality.items():
        if quality["confidence_count"] > 0:
            avg_confidence = quality["confidence_sum"] / quality["confidence_count"]
            print(
                f"  • {lang}: {quality['posts']} posts, avg confidence: {avg_confidence:.2f}"
            )
        else:
            print(f"  • {lang}: {quality['posts']} posts")

    print(f"\n✅ Analysis complete!")


if __name__ == "__main__":
    analyze_performance()
