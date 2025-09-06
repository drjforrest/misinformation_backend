#!/usr/bin/env python3
"""
Simple scraping progress tracker using file-based logging
"""

import json
import os
from datetime import datetime
from pathlib import Path


class ScrapingProgressTracker:
    def __init__(self, log_file="data/scraping_progress.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.progress_data = self._load_progress()

    def _load_progress(self):
        """Load existing progress data"""
        if self.log_file.exists():
            try:
                with open(self.log_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Could not load progress file: {e}")
                return self._get_default_progress()
        return self._get_default_progress()

    def _get_default_progress(self):
        """Get default progress structure"""
        return {
            "total_posts": 0,
            "total_comments": 0,
            "subreddits": {},
            "languages": {},
            "sessions": [],
            "last_updated": None,
        }

    def update_progress(
        self, posts_added=0, comments_added=0, subreddits=None, languages=None
    ):
        """Update progress tracking"""
        self.progress_data["total_posts"] += posts_added
        self.progress_data["total_comments"] += comments_added
        self.progress_data["last_updated"] = datetime.now().isoformat()

        # Update subreddit tracking
        if subreddits:
            for subreddit, count in subreddits.items():
                if subreddit in self.progress_data["subreddits"]:
                    self.progress_data["subreddits"][subreddit] += count
                else:
                    self.progress_data["subreddits"][subreddit] = count

        # Update language tracking
        if languages:
            for language, count in languages.items():
                if language in self.progress_data["languages"]:
                    self.progress_data["languages"][language] += count
                else:
                    self.progress_data["languages"][language] = count

    def log_session(self, session_info):
        """Log a scraping session"""
        session_info["timestamp"] = datetime.now().isoformat()
        self.progress_data["sessions"].append(session_info)

        # Keep only last 50 sessions to prevent file bloat
        if len(self.progress_data["sessions"]) > 50:
            self.progress_data["sessions"] = self.progress_data["sessions"][-50:]

    def save_progress(self):
        """Save progress to file"""
        try:
            with open(self.log_file, "w") as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception as e:
            print(f"Could not save progress file: {e}")

    def get_summary(self):
        """Get progress summary"""
        return {
            "total_posts": self.progress_data["total_posts"],
            "total_comments": self.progress_data["total_comments"],
            "subreddits_count": len(self.progress_data["subreddits"]),
            "languages_count": len(self.progress_data["languages"]),
            "last_updated": self.progress_data["last_updated"],
            "recent_sessions": (
                self.progress_data["sessions"][-5:]
                if self.progress_data["sessions"]
                else []
            ),
        }

    def get_top_subreddits(self, limit=10):
        """Get top subreddits by post count"""
        sorted_subreddits = sorted(
            self.progress_data["subreddits"].items(), key=lambda x: x[1], reverse=True
        )
        return sorted_subreddits[:limit]

    def get_language_distribution(self):
        """Get language distribution"""
        return dict(
            sorted(
                self.progress_data["languages"].items(),
                key=lambda x: x[1],
                reverse=True,
            )
        )


def main():
    tracker = ScrapingProgressTracker()
    summary = tracker.get_summary()

    print("📊 Current Scraping Progress")
    print("=" * 50)
    print(f"Total Posts: {summary['total_posts']:,}")
    print(f"Total Comments: {summary['total_comments']:,}")
    print(f"Subreddits Covered: {summary['subreddits_count']}")
    print(f"Languages Detected: {summary['languages_count']}")
    print(f"Last Updated: {summary['last_updated'] or 'Never'}")

    print("\n📈 Top Subreddits:")
    top_subreddits = tracker.get_top_subreddits()
    if top_subreddits:
        for subreddit, count in top_subreddits:
            print(f"  r/{subreddit}: {count:,} posts")
    else:
        print("  No subreddit data available")

    print("\n🌍 Language Distribution:")
    language_dist = tracker.get_language_distribution()
    if language_dist:
        for lang, count in list(language_dist.items())[:10]:
            print(f"  {lang}: {count:,} posts")
    else:
        print("  No language data available")

    print("\n📅 Recent Sessions:")
    if summary["recent_sessions"]:
        for session in summary["recent_sessions"]:
            timestamp = session.get("timestamp", "Unknown")
            posts = session.get("posts_collected", 0)
            print(f"  {timestamp}: {posts} posts")
    else:
        print("  No session data available")


if __name__ == "__main__":
    main()
