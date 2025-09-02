#!/usr/bin/env python3
"""
Fix Reddit scraping to capture more health-related discussions
"""

from config.settings import Config, ResearchConfig
from src.reddit_scraper import RedditScraper
from src.data_persistence import DataPersistenceManager
import json
from datetime import datetime


def create_enhanced_scraper():
    """Create a scraper with enhanced keyword matching"""

    # Expand keywords to include broader health terms
    enhanced_keywords = (
        ResearchConfig.PRIMARY_KEYWORDS
        + ResearchConfig.COLLOQUIAL_TERMS
        + [
            # Broader health terms
            "health",
            "medical",
            "doctor",
            "clinic",
            "hospital",
            "medication",
            "std",
            "sti",
            "test",
            "testing",
            "symptoms",
            "treatment",
            "therapy",
            "sexual health",
            "safe sex",
            "protection",
            "condom",
            "screening",
            # Specific health concerns common in LGBTQ+ communities
            "monkeypox",
            "mpox",
            "hepatitis",
            "herpes",
            "warts",
            "hpv",
            "vaccination",
            "vaccine",
            "immunization",
            # Mental health (important for comprehensive health research)
            "mental health",
            "depression",
            "anxiety",
            "therapy",
            "counseling",
            "suicide",
            "self harm",
            "stress",
            # Healthcare access terms (especially relevant for newcomers)
            "insurance",
            "ohip",
            "msp",
            "healthcare",
            "coverage",
            "prescription",
            "pharmacy",
            "walk-in",
            "emergency room",
            "urgent care",
            # Canadian health system terms
            "health card",
            "family doctor",
            "gp",
            "specialist",
            "referral",
        ]
    )

    class EnhancedRedditScraper(RedditScraper):
        def __init__(self, enable_database: bool = False):
            super().__init__(enable_database)
            # Override keywords with enhanced list
            self.keywords = enhanced_keywords
            print(f"✅ Enhanced scraper initialized with {len(self.keywords)} keywords")
            print(
                f"   Original keywords: {len(ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS)}"
            )
            print(
                f"   Added keywords: {len(enhanced_keywords) - len(ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS)}"
            )

        def contains_health_keywords(self, text: str) -> bool:
            """Enhanced keyword matching with better logic"""
            if not text:
                return False

            text_lower = text.lower()

            # Check for any keyword match
            for keyword in self.keywords:
                if keyword.lower() in text_lower:
                    return True

            # Additional pattern matching for health-related discussions
            health_patterns = [
                "went to the doctor",
                "saw a doctor",
                "got tested",
                "test results",
                "health concern",
                "medical advice",
                "should i see",
                "anyone else experienced",
                "symptoms",
                "diagnosed with",
                "taking medication",
                "prescription",
            ]

            for pattern in health_patterns:
                if pattern in text_lower:
                    return True

            return False

        def scrape_subreddit_enhanced(
            self,
            subreddit_name: str,
            limit: int = None,
            search_hot: bool = True,
            search_top: bool = True,
        ) -> list:
            """Enhanced scraping that checks new, hot, and top posts"""
            if limit is None:
                limit = Config.MAX_POSTS_PER_SUBREDDIT

            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []
            skipped_existing = 0

            print(f"🔍 Enhanced scraping r/{subreddit_name}...")

            # Collect from multiple sources
            sources = [("new", subreddit.new(limit=limit))]
            if search_hot:
                sources.append(("hot", subreddit.hot(limit=limit // 2)))
            if search_top:
                sources.append(
                    ("top_week", subreddit.top(time_filter="week", limit=limit // 2))
                )

            seen_post_ids = set()

            for source_name, post_iterator in sources:
                print(f"   Checking {source_name} posts...")
                source_count = 0

                try:
                    for post in post_iterator:
                        # Skip if already processed
                        if post.id in seen_post_ids:
                            continue
                        seen_post_ids.add(post.id)

                        # Skip if already exists in database
                        if self.enable_database and self.db_manager.post_exists(
                            post.id
                        ):
                            skipped_existing += 1
                            continue

                        # Check if post contains health keywords
                        post_text = f"{post.title} {post.selftext}"
                        if not self.contains_health_keywords(post_text):
                            continue

                        # Detect language
                        language = self.detect_language(post_text)

                        # Check for newcomer indicators
                        is_newcomer = self.is_newcomer_related(post_text)

                        post_data = {
                            "post_id": post.id,
                            "subreddit": subreddit_name,
                            "title": post.title,
                            "selftext": post.selftext,
                            "author": str(post.author) if post.author else "[deleted]",
                            "created_utc": datetime.fromtimestamp(post.created_utc),
                            "score": post.score,
                            "upvote_ratio": post.upvote_ratio,
                            "num_comments": post.num_comments,
                            "url": f"https://reddit.com{post.permalink}",
                            "language": language,
                            "is_newcomer_related": is_newcomer,
                            "full_text": post_text,
                        }

                        # Add source tracking for JSON files (but not database)
                        post_data["_source"] = (
                            source_name  # Use underscore prefix for tracking
                        )

                        # Extract comments (with limits for efficiency)
                        try:
                            comments = self.extract_comments_limited(
                                post, max_comments=10
                            )
                            post_data["comments"] = comments
                        except Exception as e:
                            print(
                                f"   Warning: Could not extract comments for {post.id}: {e}"
                            )
                            post_data["comments"] = []

                        posts_data.append(post_data)
                        source_count += 1

                        # Respect rate limits
                        import time

                        time.sleep(0.1)

                        if len(posts_data) >= limit:
                            break

                    print(f"     Found {source_count} posts from {source_name}")

                except Exception as e:
                    print(f"   Warning: Error accessing {source_name} posts: {e}")
                    continue

            print(
                f"✅ Collected {len(posts_data)} relevant posts from r/{subreddit_name}"
            )
            if skipped_existing > 0:
                print(f"   Skipped {skipped_existing} posts already in database")

            return posts_data

        def extract_comments_limited(self, post, max_comments: int = 10) -> list:
            """Extract comments with limits for efficiency"""
            comments_data = []

            try:
                post.comments.replace_more(limit=2)  # Reduce API calls
                comment_count = 0

                for comment in post.comments.list():
                    if comment_count >= max_comments:
                        break

                    if (
                        hasattr(comment, "body")
                        and len(comment.body) >= Config.MIN_COMMENT_LENGTH
                    ):
                        comment_data = {
                            "comment_id": comment.id,
                            "author": (
                                str(comment.author) if comment.author else "[deleted]"
                            ),
                            "body": comment.body[:1000],  # Limit comment length
                            "created_utc": datetime.fromtimestamp(comment.created_utc),
                            "score": comment.score,
                            "parent_id": comment.parent_id,
                            "language": self.detect_language(comment.body),
                            "is_newcomer_related": self.is_newcomer_related(
                                comment.body
                            ),
                        }
                        comments_data.append(comment_data)
                        comment_count += 1

            except Exception as e:
                print(f"   Error extracting comments: {e}")

            return comments_data

    return EnhancedRedditScraper


def test_enhanced_scraping():
    """Test the enhanced scraping approach"""
    print("🚀 Testing Enhanced Reddit Scraping")
    print("=" * 40)

    # Create enhanced scraper
    EnhancedScraper = create_enhanced_scraper()
    scraper = EnhancedScraper(enable_database=True)

    # Test on askgaybros first
    posts = scraper.scrape_subreddit_enhanced("askgaybros", limit=20)

    if posts:
        print(f"\n✅ SUCCESS: Collected {len(posts)} posts!")

        # Show sample
        print("\n📋 Sample collected posts:")
        for i, post in enumerate(posts[:5], 1):
            print(f"{i}. \"{post['title']}\"")
            print(f"   Author: {post['author']}, Score: {post['score']}")
            print(f"   Comments: {len(post['comments'])}, Language: {post['language']}")
            print(f"   Newcomer related: {post['is_newcomer_related']}")
            print(f"   Source: {post.get('_source', 'unknown')}")
            print()

        # Save to database
        db_manager = DataPersistenceManager()
        stats = db_manager.bulk_save_posts(posts)
        print(f"💾 Database save stats: {stats}")

        # Also save as JSON backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/enhanced_data_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(posts, f, indent=2, default=str)
        print(f"📁 Also saved to: {filename}")

        return posts
    else:
        print("❌ No posts found. There might be an issue.")
        return []


def main():
    print("🔧 Reddit Scraping Fix")
    print("=" * 30)

    # Test enhanced scraping
    posts = test_enhanced_scraping()

    if posts:
        print("\n🎯 Next steps:")
        print(
            "1. Generate visualizations: python main.py visualize --data-path data/enhanced_data_*.json"
        )
        print(
            "2. Launch annotation tool: python main.py annotate-enhanced --data-path data/enhanced_data_*.json"
        )
        print("3. Collect from more subreddits: python enhanced_collection.py")

        # Create enhanced collection script
        create_enhanced_collection_script()
    else:
        print("\n❌ Enhancement didn't work. Need to investigate further.")


def create_enhanced_collection_script():
    """Create a script for systematic enhanced data collection"""

    script_content = '''#!/usr/bin/env python3
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
        'askgaybros',    # High activity, health questions
        'gaybros',       # Community discussions  
        'lgbt',          # General LGBTQ+ health
        'toronto',       # Canadian city with health discussions
        'NewToCanada',   # Newcomer health questions
    ]
    
    # Create enhanced scraper
    EnhancedScraper = create_enhanced_scraper()
    scraper = EnhancedScraper(enable_database=True)
    db_manager = DataPersistenceManager()
    
    all_posts = []
    
    for subreddit in target_subreddits:
        print(f"\\n📡 Collecting from r/{subreddit}...")
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
        with open(filename, 'w') as f:
            json.dump(all_posts, f, indent=2, default=str)
        
        print(f"\\n🎉 COLLECTION COMPLETE!")
        print(f"   📊 Total posts collected: {len(all_posts)}")
        print(f"   📁 Saved to: {filename}")
        print(f"\\n🎯 Next steps:")
        print(f"   📊 Visualize: python main.py visualize --data-path {filename}")
        print(f"   👥 Annotate: python main.py annotate-enhanced --data-path {filename}")

if __name__ == "__main__":
    main()
'''

    with open("enhanced_collection.py", "w") as f:
        f.write(script_content)

    print("✅ Created enhanced_collection.py for systematic data collection")


if __name__ == "__main__":
    main()
