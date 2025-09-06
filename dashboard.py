#!/usr/bin/env python3
"""
Scraping Dashboard - Overview of data collection progress and tasks
"""

from track_progress import ScrapingProgressTracker
from task_manager import ScrapingTaskManager


def main():
    print("📊 Scraping Dashboard")
    print("=" * 60)

    # Get progress data
    tracker = ScrapingProgressTracker()
    progress_summary = tracker.get_summary()

    # Get task data
    task_manager = ScrapingTaskManager()

    # Display data overview
    print(f"📈 DATA COLLECTION OVERVIEW")
    print(f"  Total Posts: {progress_summary['total_posts']:,}")
    print(f"  Total Comments: {progress_summary['total_comments']:,}")
    print(f"  Subreddits Covered: {progress_summary['subreddits_count']}")
    print(f"  Languages Detected: {progress_summary['languages_count']}")
    print(f"  Last Updated: {progress_summary['last_updated'] or 'Never'}")

    # Display language distribution
    print(f"\n🌍 LANGUAGE DISTRIBUTION")
    language_dist = tracker.get_language_distribution()
    if language_dist:
        for lang, count in language_dist.items():
            percentage = (
                (count / progress_summary["total_posts"]) * 100
                if progress_summary["total_posts"] > 0
                else 0
            )
            print(f"  {lang}: {count:,} posts ({percentage:.1f}%)")
    else:
        print("  No language data available")

    # Display recent activity
    print(f"\n📅 RECENT ACTIVITY")
    if progress_summary["recent_sessions"]:
        for session in progress_summary["recent_sessions"]:
            timestamp = session.get("timestamp", "Unknown")
            posts = session.get("posts_collected", 0)
            print(f"  {timestamp}: {posts} posts collected")
    else:
        print("  No recent activity")

    # Display task status
    print(f"\n📋 TASK STATUS")
    completed_tasks = task_manager.get_completed_tasks()
    pending_tasks = task_manager.get_pending_tasks()
    overdue_tasks = task_manager.get_overdue_tasks()

    print(f"  Completed: {len(completed_tasks)}")
    print(f"  Pending: {len(pending_tasks)}")
    print(f"  Overdue: {len(overdue_tasks)}")

    # Show next priorities
    print(f"\n🎯 NEXT PRIORITIES")
    print("  1. Run enhanced data collection (enhanced_data_collection)")
    print("  2. Review translation quality for technical terms")
    print("  3. Expand Spanish language content collection")
    print("  4. Improve Tagalog translation quality")

    # Show quick actions
    print(f"\n⚡ QUICK ACTIONS")
    print("  python run_multilingual_collection.py  # Run multilingual collection")
    print("  python enhanced_collection.py          # Run enhanced collection")
    print("  python launch_dashboard.py             # Launch analytics dashboard")
    print("  python launch_research_annotation.py   # Launch annotation tool")


if __name__ == "__main__":
    main()
