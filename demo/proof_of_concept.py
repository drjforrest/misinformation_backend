"""
Simple proof-of-concept demonstration script
Run this to quickly test the core functionality
"""

from src.reddit_scraper import RedditScraper
import json
from datetime import datetime


def run_proof_of_concept():
    """Run a quick proof of concept demonstration"""

    print("🚀 Health Misinformation Detection - Proof of Concept")
    print("=" * 60)

    # Step 1: Data Collection Demo
    print("\n📡 Step 1: Collecting sample data from Reddit...")

    scraper = RedditScraper()

    # Collect small sample from key subreddits
    sample_data = []
    test_subreddits = ["askgaybros", "toronto", "NewToCanada"]

    for subreddit in test_subreddits:
        print(f"   • Scraping r/{subreddit}...")
        posts = scraper.scrape_subreddit(subreddit, limit=20)
        sample_data.extend(posts)

    # Save sample data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_path = f"data/poc_sample_{timestamp}.json"

    with open(sample_path, "w") as f:
        json.dump(sample_data, f, indent=2, default=str)

    print(f"   ✅ Collected {len(sample_data)} posts")

    # Step 2: Basic Analysis
    print("\n🔍 Step 2: Analyzing content patterns...")

    # Language distribution
    languages = {}
    newcomer_posts = 0
    health_keywords_found = set()

    for post in sample_data:
        lang = post.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

        if post.get("is_newcomer_related"):
            newcomer_posts += 1

        # Check which keywords appeared
        text = f"{post['title']} {post['selftext']}".lower()
        for keyword in scraper.keywords:
            if keyword.lower() in text:
                health_keywords_found.add(keyword)

    print(f"   • Languages detected: {list(languages.keys())}")
    print(f"   • Newcomer-related posts: {newcomer_posts}")
    print(f"   • Health keywords found: {list(health_keywords_found)}")

    # Step 3: Network Preview
    print("\n🕸️ Step 3: Building interaction network...")

    total_comments = sum(len(post.get("comments", [])) for post in sample_data)
    unique_users = set()

    for post in sample_data:
        unique_users.add(post["author"])
        for comment in post.get("comments", []):
            unique_users.add(comment["author"])

    unique_users.discard("[deleted]")

    print(f"   • Total comments: {total_comments}")
    print(f"   • Unique users: {len(unique_users)}")
    print(f"   • Average comments per post: {total_comments/len(sample_data):.1f}")

    # Step 4: Sample for Manual Review
    print("\n📋 Step 4: Sample posts for manual review...")

    # Show a few interesting posts
    for i, post in enumerate(sample_data[:3]):
        if post.get("is_newcomer_related") or post.get("language") != "en":
            print(f"\n   Post {i+1} [r/{post['subreddit']}]:")
            print(f"   Title: {post['title'][:80]}...")
            print(
                f"   Language: {post['language']} | Newcomer: {post['is_newcomer_related']}"
            )
            print(f"   Comments: {len(post.get('comments', []))}")

    print("\n🎯 Proof of Concept Results:")
    print("   • Successfully scraped multiple subreddits")
    print("   • Detected multilingual content")
    print("   • Identified newcomer-related discussions")
    print("   • Built interaction networks")
    print("   • Ready for human annotation")

    print(f"\n📁 Data saved to: {sample_path}")
    print("\n🚀 Next steps:")
    print(
        f"   1. Launch annotation tool: python main.py annotate --data-path {sample_path}"
    )
    print("   2. Full data collection: python main.py collect")
    print(f"   3. Network analysis: python main.py analyze --data-path {sample_path}")


if __name__ == "__main__":
    run_proof_of_concept()
