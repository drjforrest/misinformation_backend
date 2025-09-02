#!/usr/bin/env python3
"""
Enhanced systematic data collection script
"""

from fix_scraping import create_enhanced_scraper
from src.data_persistence import DataPersistenceManager
import json
from datetime import datetime


def main():
    print("🌟 Enhanced Systematic Data Collection")
    print("=" * 50)

    # Target subreddits with expected health discussions
    target_subreddits = [
        "askgaybros",  # High activity, health questions
        "gaybros",  # Community discussions
        "lgbt",  # General LGBTQ+ health
        "toronto",  # Canadian city with health discussions
        "NewToCanada",  # Newcomer health questions
    ]

    # Create enhanced scraper
    EnhancedScraper = create_enhanced_scraper()
    scraper = EnhancedScraper(enable_database=True)
    db_manager = DataPersistenceManager()

    all_posts = []

    for subreddit in target_subreddits:
        print(f"\n📡 Collecting from r/{subreddit}...")
        posts = scraper.scrape_subreddit_enhanced(subreddit, limit=50)

        if posts:
            all_posts.extend(posts)
            stats = db_manager.bulk_save_posts(posts)
            print(f"   💾 Saved to database: {stats}")

        # Rate limiting
        import time

        time.sleep(3)

    # Save combined data
    if all_posts:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/systematic_collection_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(all_posts, f, indent=2, default=str)

        print("\n🎉 COLLECTION COMPLETE!")
        print(f"   📊 Total posts collected: {len(all_posts)}")
        print(f"   📁 Saved to: {filename}")
        print("\n🎯 Next steps:")
        print(f"   📊 Visualize: python main.py visualize --data-path {filename}")
        print(
            f"   👥 Annotate: python main.py annotate-enhanced --data-path {filename}"
        )


if __name__ == "__main__":
    main()
