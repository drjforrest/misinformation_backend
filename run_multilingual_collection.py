#!/usr/bin/env python3
"""
Run multilingual data collection without user input
"""

from collect_multilingual_data import MultilingualHealthCollector


def main():
    """Run multilingual data collection with small sample"""
    print("🌐 Running Multilingual Health Data Collection (Sample)")
    print("=" * 55)

    # Create collector
    collector = MultilingualHealthCollector()

    # Collect small sample (5 posts per subreddit)
    try:
        results = collector.collect_targeted_multilingual_data(posts_per_subreddit=5)

        print("\n✅ Collection completed successfully!")
        print(
            f"📊 Collected {results['total_posts']} posts from {len(results['language_distribution'])} languages"
        )
        print(f"🌍 Languages found: {list(results['language_distribution'].keys())}")

        # Show some results
        if results["subreddit_stats"]:
            print("\n🏆 Top performing subreddits:")
            for subreddit, stats in list(results["subreddit_stats"].items())[:3]:
                print(
                    f"  • r/{subreddit}: {stats['post_count']} posts, {stats['languages_found']} languages"
                )

        print(
            "\n🌐 You can now refresh the analytics dashboard to see the new multilingual data!"
        )
        print("🌐 Dashboard URL: http://127.0.0.1:7862")

    except Exception as e:
        print(f"❌ Collection failed: {e}")
    finally:
        collector.close()


if __name__ == "__main__":
    main()
