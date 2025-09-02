#!/usr/bin/env python3
"""
Diagnostic script to test Reddit scraping and understand filtering issues
"""

import praw
from config.settings import Config, ResearchConfig


def test_reddit_connection():
    """Test Reddit API connection"""
    try:
        reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT,
        )

        # Test connection by getting user info
        print("✅ Reddit API connected successfully")
        print(f"   User agent: {Config.REDDIT_USER_AGENT}")
        return reddit

    except Exception as e:
        print(f"❌ Reddit API connection failed: {e}")
        return None


def test_subreddit_access(reddit, subreddit_name="askgaybros"):
    """Test subreddit access and see what posts are available"""
    try:
        subreddit = reddit.subreddit(subreddit_name)
        print(f"\n🔍 Testing r/{subreddit_name} access...")

        # Get basic subreddit info
        print(f"   Subreddit: {subreddit.display_name}")
        print(f"   Subscribers: {subreddit.subscribers}")

        # Sample recent posts
        posts_checked = 0
        posts_with_keywords = 0
        sample_posts = []

        print("\n📊 Sampling recent posts...")

        for post in subreddit.new(limit=50):  # Check 50 recent posts
            posts_checked += 1
            post_text = f"{post.title} {post.selftext}".lower()

            # Check if it contains any health keywords
            keywords = ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS
            found_keywords = [kw for kw in keywords if kw.lower() in post_text]

            if found_keywords:
                posts_with_keywords += 1
                sample_posts.append(
                    {
                        "title": (
                            post.title[:100] + "..."
                            if len(post.title) > 100
                            else post.title
                        ),
                        "keywords_found": found_keywords,
                        "score": post.score,
                        "comments": post.num_comments,
                        "age_hours": (post.created_utc),
                        "author": str(post.author) if post.author else "[deleted]",
                    }
                )

        print(f"   📋 Checked {posts_checked} posts")
        print(
            f"   🎯 Found {posts_with_keywords} posts with health keywords ({posts_with_keywords/posts_checked*100:.1f}%)"
        )

        if sample_posts:
            print("\n✨ Sample posts with health content:")
            for i, post in enumerate(sample_posts[:5], 1):
                print(f"   {i}. \"{post['title']}\"")
                print(f"      Keywords: {post['keywords_found']}")
                print(f"      Score: {post['score']}, Comments: {post['comments']}")
                print(f"      Author: {post['author']}")
                print()

        return sample_posts

    except Exception as e:
        print(f"❌ Error accessing r/{subreddit_name}: {e}")
        return []


def test_keyword_expansion():
    """Test broader keyword matching"""
    print("\n🔍 Testing keyword expansion...")

    # Broader health-related terms
    broader_keywords = [
        "health",
        "medical",
        "doctor",
        "clinic",
        "hospital",
        "medication",
        "treatment",
        "therapy",
        "vaccine",
        "test",
        "testing",
        "symptoms",
        "diagnosis",
        "disease",
        "infection",
        "medicine",
        "prescription",
        "sexual health",
        "std",
        "sti",
        "safe sex",
        "protection",
        "condom",
    ]

    print(
        "Current specific keywords:",
        len(ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS),
    )
    print("Potential broader keywords:", len(broader_keywords))
    print("Broader keywords:", broader_keywords[:10], "...")

    return broader_keywords


def test_specific_posts(reddit):
    """Look for posts that might contain health discussions but not exact keywords"""
    print("\n🎯 Testing posts that might discuss health without exact keywords...")

    # Search for posts with broader health terms
    broader_terms = ["health", "doctor", "clinic", "medical", "std", "sti", "test"]

    try:
        subreddit = reddit.subreddit("askgaybros")
        found_posts = []

        for post in subreddit.new(limit=100):
            post_text = f"{post.title} {post.selftext}".lower()

            # Check for broader health terms
            found_broad_terms = [term for term in broader_terms if term in post_text]

            if found_broad_terms and len(post_text) > 50:  # Skip very short posts
                found_posts.append(
                    {
                        "title": post.title,
                        "broad_terms": found_broad_terms,
                        "text_preview": (
                            post_text[:200] + "..."
                            if len(post_text) > 200
                            else post_text
                        ),
                    }
                )

        print(f"   Found {len(found_posts)} posts with broader health terms")

        # Show examples
        for i, post in enumerate(found_posts[:3], 1):
            print(f"\n   Example {i}:")
            print(f"   Title: {post['title']}")
            print(f"   Terms found: {post['broad_terms']}")
            print(f"   Preview: {post['text_preview']}")

        return found_posts

    except Exception as e:
        print(f"❌ Error in broader search: {e}")
        return []


def main():
    print("🔬 Reddit Scraping Diagnostic Tool")
    print("=" * 50)

    # Test Reddit connection
    reddit = test_reddit_connection()
    if not reddit:
        return

    # Test subreddit access and keyword matching
    sample_posts = test_subreddit_access(reddit, "askgaybros")

    # Test broader keyword matching
    broader_keywords = test_keyword_expansion()

    # Test broader health discussions
    broader_posts = test_specific_posts(reddit)

    # Summary and recommendations
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)

    if sample_posts:
        print(f"✅ Found {len(sample_posts)} posts with specific health keywords")
        print("   Recommendation: Current keyword filtering is working")
    else:
        print("❌ No posts found with specific health keywords")
        print("   Issue: Keywords may be too specific or posts are rare")

    if broader_posts:
        print(f"✅ Found {len(broader_posts)} posts with broader health terms")
        print("   Recommendation: Consider expanding keyword list")

    # Suggest fixes
    print("\n🔧 SUGGESTED FIXES:")

    if not sample_posts and broader_posts:
        print("1. Expand keywords to include broader health terms:")
        print("   - Add 'health', 'doctor', 'clinic', 'medical', 'std', 'sti'")

    print("2. Try different subreddits that might have more health discussions:")
    print("   - r/gay_irl, r/gaybros, r/lgbt")

    print("3. Consider collecting from hot/top posts instead of just new posts")

    print("4. Lower the keyword threshold - collect posts with any health discussion")

    print("\n🎯 To fix the scraping, run:")
    print("   python fix_scraping.py")


if __name__ == "__main__":
    main()
