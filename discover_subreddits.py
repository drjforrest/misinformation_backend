#!/usr/bin/env python3
"""
Subreddit Discovery Tool - Find new relevant subreddits for health research
"""

import praw
from config.settings import Config
import json
from pathlib import Path


class SubredditDiscovery:
    def __init__(self):
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT,
        )

    def search_health_subreddits(self, search_terms=None, limit=50):
        """Search for health-related subreddits"""
        if search_terms is None:
            search_terms = [
                "health",
                "medical",
                "doctor",
                "clinic",
                "hospital",
                "HIV",
                "PrEP",
                "STI",
                "STD",
                "sexual health",
                "gay health",
                "LGBTQ health",
                "immigrant health",
                "newcomer health",
                "refugee health",
            ]

        discovered_subreddits = {}

        for term in search_terms:
            try:
                # Search for subreddits
                subreddits = self.reddit.subreddits.search(term, limit=10)

                for subreddit in subreddits:
                    # Get basic info
                    if subreddit.display_name not in discovered_subreddits:
                        discovered_subreddits[subreddit.display_name] = {
                            "subscribers": subreddit.subscribers or 0,
                            "description": subreddit.public_description or "",
                            "search_terms": [term],
                        }
                    else:
                        # Add search term if already found
                        if (
                            term
                            not in discovered_subreddits[subreddit.display_name][
                                "search_terms"
                            ]
                        ):
                            discovered_subreddits[subreddit.display_name][
                                "search_terms"
                            ].append(term)

            except Exception as e:
                print(f"Error searching for '{term}': {e}")
                continue

        return discovered_subreddits

    def filter_relevant_subreddits(self, subreddits, min_subscribers=1000):
        """Filter subreddits based on relevance and size"""
        relevant = {}

        health_keywords = [
            "health",
            "medical",
            "doctor",
            "clinic",
            "hospital",
            "HIV",
            "PrEP",
            "ARV",
            "syphilis",
            "doxy",
            "PEP",
            "chlamydia",
            "gonorrhea",
            "STD",
            "STI",
            "sexual",
            "Truvada",
            "Descovy",
            "undetectable",
            "gay",
            "LGBTQ",
            "immigrant",
            "newcomer",
            "refugee",
        ]

        for name, info in subreddits.items():
            # Check minimum subscriber count
            if info["subscribers"] < min_subscribers:
                continue

            # Check if description contains health keywords
            desc = (info["description"] or "").lower()
            if any(keyword.lower() in desc for keyword in health_keywords):
                relevant[name] = info
            # Also check if search terms contain health keywords
            elif any(
                any(
                    keyword.lower() in search_term.lower()
                    for keyword in health_keywords
                )
                for search_term in info["search_terms"]
            ):
                relevant[name] = info

        return relevant

    def save_discovered_subreddits(
        self, subreddits, filename="data/discovered_subreddits.json"
    ):
        """Save discovered subreddits to file"""
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

        # Sort by subscriber count
        sorted_subreddits = dict(
            sorted(subreddits.items(), key=lambda x: x[1]["subscribers"], reverse=True)
        )

        with open(filename, "w") as f:
            json.dump(sorted_subreddits, f, indent=2)

        return filename

    def get_subreddit_sample_posts(self, subreddit_name, limit=5):
        """Get sample posts from a subreddit to assess relevance"""
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts = []

            for post in subreddit.hot(limit=limit):
                posts.append(
                    {
                        "title": post.title,
                        "score": post.score,
                        "url": f"https://reddit.com{post.permalink}",
                    }
                )

            return posts
        except Exception as e:
            print(f"Error getting sample posts from r/{subreddit_name}: {e}")
            return []


def main():
    print("🔍 Subreddit Discovery Tool")
    print("=" * 40)

    discovery = SubredditDiscovery()

    # Search for health-related subreddits
    print("Searching for health-related subreddits...")
    all_subreddits = discovery.search_health_subreddits()
    print(f"Found {len(all_subreddits)} potential subreddits")

    # Filter for relevance
    print("Filtering for relevant subreddits...")
    relevant_subreddits = discovery.filter_relevant_subreddits(
        all_subreddits, min_subscribers=500
    )
    print(f"Found {len(relevant_subreddits)} relevant subreddits")

    # Save results
    filename = discovery.save_discovered_subreddits(relevant_subreddits)
    print(f"Saved to {filename}")

    # Show top 10 discovered subreddits
    print("\n🏆 Top 10 Discovered Subreddits:")
    sorted_subreddits = sorted(
        relevant_subreddits.items(), key=lambda x: x[1]["subscribers"], reverse=True
    )

    for i, (name, info) in enumerate(sorted_subreddits[:10], 1):
        print(f"{i:2d}. r/{name}")
        print(f"    Subscribers: {info['subscribers']:,}")
        print(f"    Search terms: {', '.join(info['search_terms'])}")

        # Get sample posts for top 3
        if i <= 3:
            print("    Sample posts:")
            sample_posts = discovery.get_subreddit_sample_posts(name, limit=3)
            for post in sample_posts:
                print(f"      • {post['title'][:60]}... (↑{post['score']})")
        print()


if __name__ == "__main__":
    main()
