#!/usr/bin/env python3
"""
Update progress tracking with latest collection data
"""

import json
from pathlib import Path
from track_progress import ScrapingProgressTracker


def update_progress_from_latest_collection():
    """Update progress tracking with data from the latest collection"""
    # Find the most recent collection report
    data_dir = Path("data")
    collection_reports = list(data_dir.glob("multilingual_collection_report_*.json"))

    if not collection_reports:
        print("No collection reports found")
        return

    # Get the most recent report
    latest_report = sorted(collection_reports, reverse=True)[0]
    print(f"Updating progress from: {latest_report.name}")

    # Load the report
    with open(latest_report, "r") as f:
        report_data = json.load(f)

    # Initialize tracker
    tracker = ScrapingProgressTracker()

    # Extract data from report
    posts_added = report_data["total_posts"]
    health_posts = report_data["health_keyword_posts"]
    languages = report_data["language_distribution"]

    # Extract subreddit data
    subreddits = {}
    for subreddit, stats in report_data["subreddit_stats"].items():
        subreddits[subreddit] = stats["post_count"]

    # Update progress
    tracker.update_progress(
        posts_added=posts_added, subreddits=subreddits, languages=languages
    )

    # Log session
    session_info = {
        "posts_collected": posts_added,
        "health_posts": health_posts,
        "languages_detected": len(languages),
        "report_file": latest_report.name,
    }
    tracker.log_session(session_info)

    # Save progress
    tracker.save_progress()

    print(f"✅ Updated progress tracking:")
    print(f"  • Added {posts_added} posts")
    print(f"  • Detected {len(languages)} languages")
    print(f"  • Covered {len(subreddits)} subreddits")


if __name__ == "__main__":
    update_progress_from_latest_collection()
