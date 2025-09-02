#!/usr/bin/env python3
"""
Automated Reddit Data Collection Script
Designed for scheduled execution via cron jobs

This script handles:
- Full data collection pipeline
- Database persistence with duplicate handling
- Comprehensive error handling and recovery
- Detailed logging for monitoring
- Rate limiting and respectful API usage
"""

import json
import os
import sys
import time
import traceback
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict
import glob

from loguru import logger

from config.settings import Config
from src.data_persistence import DataPersistenceManager
from src.reddit_scraper import RedditScraper

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AutomatedCollector:
    """Automated data collection with comprehensive error handling"""

    def __init__(self):
        """Initialize the automated collector"""
        self.setup_logging()
        self.scraper = RedditScraper(enable_database=True)
        self.db_manager = DataPersistenceManager()

        logger.info("=== Automated Reddit Collection Started ===")
        logger.info(f"Target subreddits: {len(self.scraper.target_subreddits)}")
        logger.info(f"Health keywords: {len(self.scraper.keywords)}")

    def setup_logging(self):
        """Configure logging for automated execution"""
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Remove default logger
        logger.remove()

        # Add file logger with rotation
        logger.add(
            "logs/automated_collection.log",
            rotation="1 week",
            retention="2 months",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

        # Add console logger for cron job output
        logger.add(
            sys.stdout, level="INFO", format="{time:HH:mm:ss} | {level} | {message}"
        )

    def validate_environment(self) -> bool:
        """Validate that all required environment variables and dependencies are available"""
        try:
            # Check Reddit API credentials
            if not Config.REDDIT_CLIENT_ID:
                logger.error("REDDIT_CLIENT_ID not set in environment")
                return False

            if not Config.REDDIT_CLIENT_SECRET:
                logger.error("REDDIT_CLIENT_SECRET not set in environment")
                return False

            # Test Reddit API connection
            try:
                # Simple API test
                test_subreddit = self.scraper.reddit.subreddit("test")
                test_subreddit.display_name  # This will fail if auth is broken
                logger.info("✅ Reddit API authentication successful")
            except Exception as e:
                logger.error(f"❌ Reddit API authentication failed: {e}")
                return False

            # Test database connection
            try:
                stats = self.db_manager.get_collection_stats()
                if "error" in stats:
                    logger.error(f"❌ Database connection failed: {stats['error']}")
                    return False
                logger.info("✅ Database connection successful")
            except Exception as e:
                logger.error(f"❌ Database connection failed: {e}")
                return False

            return True

        except Exception as e:
            logger.error(f"Environment validation failed: {e}")
            return False

    def run_collection_cycle(self) -> Dict[str, any]:
        """
        Run a single data collection cycle

        Returns:
            Dictionary with collection results and statistics
        """
        cycle_start = datetime.now()
        results = {
            "start_time": cycle_start,
            "success": False,
            "posts_collected": 0,
            "posts_saved": 0,
            "posts_updated": 0,
            "errors": 0,
            "subreddit_results": {},
            "duration_seconds": 0,
        }

        try:
            logger.info("Starting data collection cycle...")

            # Get pre-collection database stats
            pre_stats = self.db_manager.get_collection_stats()
            logger.info(
                f"Database contains {pre_stats.get('total_posts', 0)} posts before collection"
            )

            # Collect data from all subreddits
            total_collected = 0
            total_db_saves = 0
            total_db_updates = 0
            total_errors = 0

            for subreddit in self.scraper.target_subreddits:
                logger.info(f"📊 Collecting from r/{subreddit}")

                try:
                    # Collect posts from this subreddit
                    posts = self.scraper.scrape_subreddit(
                        subreddit,
                        limit=Config.MAX_POSTS_PER_SUBREDDIT,
                        skip_existing=True,
                    )

                    subreddit_stats = {
                        "posts_collected": len(posts),
                        "posts_saved": 0,
                        "posts_updated": 0,
                        "errors": 0,
                    }

                    total_collected += len(posts)

                    # Save to database if we got posts
                    if posts:
                        db_stats = self.db_manager.bulk_save_posts(posts)
                        subreddit_stats.update(db_stats)

                        total_db_saves += db_stats.get("saved", 0)
                        total_db_updates += db_stats.get("updated", 0)
                        total_errors += db_stats.get("errors", 0)

                        logger.info(
                            f"r/{subreddit}: {len(posts)} posts → DB: {db_stats}"
                        )
                    else:
                        logger.info(f"r/{subreddit}: No new health-related posts found")

                    results["subreddit_results"][subreddit] = subreddit_stats

                    # Rate limiting between subreddits
                    time.sleep(2)

                except Exception as e:
                    logger.error(f"Error processing r/{subreddit}: {e}")
                    results["subreddit_results"][subreddit] = {"error": str(e)}
                    total_errors += 1

            # Update results
            results.update(
                {
                    "posts_collected": total_collected,
                    "posts_saved": total_db_saves,
                    "posts_updated": total_db_updates,
                    "errors": total_errors,
                    "success": total_errors == 0 or total_collected > 0,
                }
            )

            # Get post-collection database stats
            post_stats = self.db_manager.get_collection_stats()

            results["final_database_stats"] = post_stats

            cycle_end = datetime.now()
            results["duration_seconds"] = (cycle_end - cycle_start).total_seconds()

            logger.info(
                f"🎯 Collection cycle complete in {results['duration_seconds']:.1f}s"
            )
            logger.info(f"   📈 Collected: {total_collected} posts")
            logger.info(
                f"   💾 Database: {total_db_saves} saved, {total_db_updates} updated"
            )
            logger.info(f"   📊 Total in DB: {post_stats.get('total_posts', 0)} posts")

            if total_errors > 0:
                logger.warning(f"   ⚠️  {total_errors} errors occurred")

            return results

        except Exception as e:
            logger.error(f"Critical error in collection cycle: {e}")
            logger.error(traceback.format_exc())
            results["error"] = str(e)
            results["duration_seconds"] = (datetime.now() - cycle_start).total_seconds()
            return results

    def save_collection_report(self, results: Dict) -> str:
        """Save detailed collection report to file"""
        try:
            os.makedirs("data/reports", exist_ok=True)

            timestamp = results["start_time"].strftime("%Y%m%d_%H%M%S")
            report_path = f"data/reports/collection_report_{timestamp}.json"

            # Make datetime objects JSON serializable
            serializable_results = json.loads(json.dumps(results, default=str))

            with open(report_path, "w") as f:
                json.dump(serializable_results, f, indent=2)

            logger.info(f"📋 Collection report saved: {report_path}")

            # Also create a human-readable summary report
            summary_path = self.save_summary_report(results, timestamp)
            if summary_path:
                logger.info(f"📄 Summary report saved: {summary_path}")

            return report_path

        except Exception as e:
            logger.error(f"Failed to save collection report: {e}")
            return ""

    def save_summary_report(self, results: Dict, timestamp: str) -> str:
        """Save human-readable summary report"""
        try:
            summary_path = f"data/reports/collection_summary_{timestamp}.md"

            # Calculate success rate
            total_subreddits = len(self.scraper.target_subreddits)
            successful_subreddits = sum(
                1
                for r in results["subreddit_results"].values()
                if isinstance(r, dict) and "error" not in r
            )
            success_rate = (
                (successful_subreddits / total_subreddits * 100)
                if total_subreddits > 0
                else 0
            )

            # Generate summary content
            summary_content = f"""# Automated Collection Report
Generated: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Collection Summary

**Overall Status:** {'✅ SUCCESS' if results['success'] else '❌ FAILED'}
**Duration:** {results['duration_seconds']:.1f} seconds
**Success Rate:** {success_rate:.1f}% ({successful_subreddits}/{total_subreddits} subreddits)

### Key Metrics
- **Posts Collected:** {results['posts_collected']:,}
- **Posts Saved to DB:** {results['posts_saved']:,}
- **Posts Updated:** {results['posts_updated']:,}
- **Errors:** {results['errors']}

### Database Status
"""

            if "final_database_stats" in results:
                db_stats = results["final_database_stats"]
                summary_content += f"""- **Total Posts in Database:** {db_stats.get('total_posts', 0):,}
- **Health-Related Posts:** {db_stats.get('health_posts', 0):,}
- **Multilingual Posts:** {db_stats.get('multilingual_posts', 0):,}
- **Latest Post:** {db_stats.get('latest_post_date', 'N/A')}
"""

            summary_content += """
## 🎯 Subreddit Results

| Subreddit | Status | Posts Collected | DB Saved | DB Updated |
|-----------|--------|-----------------|----------|------------|
"""

            for subreddit, stats in results["subreddit_results"].items():
                if isinstance(stats, dict) and "error" not in stats:
                    status = "✅"
                    collected = stats.get("posts_collected", 0)
                    saved = stats.get("posts_saved", 0)
                    updated = stats.get("posts_updated", 0)
                else:
                    status = "❌"
                    collected = saved = updated = 0

                summary_content += f"| r/{subreddit} | {status} | {collected} | {saved} | {updated} |\n"

            if results["errors"] > 0:
                summary_content += f"""
## ⚠️ Issues Encountered

**Total Errors:** {results['errors']}

"""
                for subreddit, stats in results["subreddit_results"].items():
                    if isinstance(stats, dict) and "error" in stats:
                        summary_content += f"- **r/{subreddit}:** {stats['error']}\n"

            # Health and recommendations
            summary_content += f"""
## 🔍 Health Check

**Collection Health:** {'✅ Good' if self.check_collection_health() else '⚠️ Needs Attention'}

## 📋 Next Steps

"""
            if results["posts_collected"] == 0:
                summary_content += "- 🔍 **Investigation needed:** No posts collected - check API credentials and subreddit availability\n"
            elif results["errors"] > results["posts_collected"]:
                summary_content += (
                    "- ⚠️ **High error rate:** Review error logs and API rate limiting\n"
                )
            else:
                summary_content += "- ✅ **Collection performing well:** Continue regular automated collection\n"

            if results["posts_collected"] > 100:
                summary_content += "- 📊 **Data ready for analysis:** Consider running community resilience analysis\n"

            summary_content += f"""
---
*Report generated by Community Resilience Analysis Platform*  
*For more details, see: collection_report_{timestamp}.json*
"""

            # Write summary to file
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_content)

            return summary_path

        except Exception as e:
            logger.error(f"Failed to save summary report: {e}")
            return ""

    def check_collection_health(self) -> bool:
        """Check if recent collections are working properly"""
        try:
            stats = self.db_manager.get_collection_stats()

            if stats.get("total_posts", 0) == 0:
                logger.warning(
                    "⚠️  No posts in database - may indicate collection issues"
                )
                return False

            # Check if we have recent data (within last 48 hours)
            latest_post = stats.get("latest_post_date")
            if latest_post:
                if isinstance(latest_post, str):
                    latest_post = datetime.fromisoformat(
                        latest_post.replace("Z", "+00:00")
                    )

                hours_since_latest = (
                    datetime.now() - latest_post
                ).total_seconds() / 3600

                if hours_since_latest > 48:
                    logger.warning(
                        f"⚠️  Latest post is {hours_since_latest:.1f} hours old"
                    )
                    return False
                else:
                    logger.info(f"✅ Latest post is {hours_since_latest:.1f} hours old")

            return True

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def generate_aggregate_report(self, days: int = 7) -> str:
        """Generate aggregate report from multiple collection reports"""
        try:
            # Find recent collection reports
            cutoff_date = datetime.now() - timedelta(days=days)
            report_pattern = "data/reports/collection_report_*.json"
            report_files = glob.glob(report_pattern)

            # Filter by date
            recent_reports = []
            for report_file in report_files:
                try:
                    # Extract timestamp from filename
                    filename = os.path.basename(report_file)
                    timestamp_str = filename.replace("collection_report_", "").replace(
                        ".json", ""
                    )
                    report_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    if report_date >= cutoff_date:
                        with open(report_file, "r") as f:
                            report_data = json.load(f)
                            report_data["report_file"] = report_file
                            recent_reports.append(report_data)
                except Exception as e:
                    logger.warning(f"Could not parse report {report_file}: {e}")
                    continue

            if not recent_reports:
                logger.warning(f"No collection reports found in last {days} days")
                return ""

            # Sort by date
            recent_reports.sort(key=lambda x: x["start_time"])

            # Calculate aggregate statistics
            total_posts = sum(r.get("posts_collected", 0) for r in recent_reports)
            total_saved = sum(r.get("posts_saved", 0) for r in recent_reports)
            total_errors = sum(r.get("errors", 0) for r in recent_reports)
            successful_runs = sum(1 for r in recent_reports if r.get("success", False))

            # Subreddit performance
            subreddit_stats = {}
            for report in recent_reports:
                for subreddit, stats in report.get("subreddit_results", {}).items():
                    if subreddit not in subreddit_stats:
                        subreddit_stats[subreddit] = {
                            "collected": 0,
                            "errors": 0,
                            "runs": 0,
                        }

                    if isinstance(stats, dict):
                        if "error" not in stats:
                            subreddit_stats[subreddit]["collected"] += stats.get(
                                "posts_collected", 0
                            )
                            subreddit_stats[subreddit]["runs"] += 1
                        else:
                            subreddit_stats[subreddit]["errors"] += 1

            # Generate aggregate report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"data/reports/aggregate_report_{days}days_{timestamp}.md"

            period_start = recent_reports[0]["start_time"]
            period_end = recent_reports[-1]["start_time"]
            success_rate = (
                (successful_runs / len(recent_reports) * 100) if recent_reports else 0
            )

            aggregate_content = f"""# Aggregate Collection Report ({days} Days)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {period_start} to {period_end}

## 📊 Overview

**Reporting Period:** {days} days
**Total Collection Runs:** {len(recent_reports)}
**Successful Runs:** {successful_runs} ({success_rate:.1f}%)
**Total Posts Collected:** {total_posts:,}
**Total Posts Saved:** {total_saved:,}
**Total Errors:** {total_errors}

## 📈 Collection Trends

### Daily Collection Summary
| Date | Posts Collected | Posts Saved | Errors | Status |
|------|----------------|-------------|--------|--------|
"""

            for report in recent_reports:
                date = (
                    report["start_time"][:10]
                    if isinstance(report["start_time"], str)
                    else str(report["start_time"])[:10]
                )
                status = "✅" if report.get("success", False) else "❌"
                aggregate_content += f"| {date} | {report.get('posts_collected', 0)} | {report.get('posts_saved', 0)} | {report.get('errors', 0)} | {status} |\n"

            aggregate_content += """
## 🎯 Subreddit Performance

| Subreddit | Posts Collected | Successful Runs | Error Rate |
|-----------|-----------------|-----------------|------------|
"""

            for subreddit, stats in sorted(
                subreddit_stats.items(), key=lambda x: x[1]["collected"], reverse=True
            ):
                total_runs = stats["runs"] + stats["errors"]
                error_rate = (
                    (stats["errors"] / total_runs * 100) if total_runs > 0 else 0
                )
                aggregate_content += f"| r/{subreddit} | {stats['collected']} | {stats['runs']}/{total_runs} | {error_rate:.1f}% |\n"

            # Add insights
            aggregate_content += f"""
## 🔍 Insights

### Performance Analysis
- **Most Active Community:** {max(subreddit_stats.items(), key=lambda x: x[1]['collected'])[0] if subreddit_stats else 'N/A'}
- **Average Posts per Run:** {total_posts / len(recent_reports) if recent_reports else 0:.1f}
- **Collection Reliability:** {success_rate:.1f}%

### Recommendations
"""

            if success_rate < 80:
                aggregate_content += "- ⚠️ **Low success rate:** Investigate API issues or rate limiting\n"
            if total_errors > total_posts * 0.1:
                aggregate_content += (
                    "- ⚠️ **High error rate:** Review error logs for patterns\n"
                )
            if total_posts < days * 10:
                aggregate_content += "- 🔍 **Low collection volume:** Consider expanding target subreddits or keywords\n"

            if success_rate >= 80 and total_posts > days * 50:
                aggregate_content += "- ✅ **Collection performing well:** Data ready for resilience analysis\n"

            aggregate_content += f"""
---
*Generated by Community Resilience Analysis Platform*  
*Based on {len(recent_reports)} collection reports from the last {days} days*
"""

            # Save aggregate report
            os.makedirs("data/reports", exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(aggregate_content)

            logger.info(f"📈 Aggregate report generated: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Failed to generate aggregate report: {e}")
            return ""


def main():
    """Main entry point for automated collection"""
    parser = argparse.ArgumentParser(
        description="Automated Reddit Collection for Community Resilience Analysis"
    )
    parser.add_argument(
        "--collect", action="store_true", help="Run data collection (default)"
    )
    parser.add_argument(
        "--report",
        type=int,
        metavar="DAYS",
        help="Generate aggregate report for last N days",
    )
    parser.add_argument(
        "--health-check", action="store_true", help="Run health check only"
    )
    args = parser.parse_args()

    # If no arguments provided, default to collection
    if not any([args.collect, args.report, args.health_check]):
        args.collect = True

    try:
        collector = AutomatedCollector()

        # Handle different command types
        if args.health_check:
            logger.info("🔍 Running health check...")
            if collector.validate_environment() and collector.check_collection_health():
                logger.info("✅ Health check passed")
                sys.exit(0)
            else:
                logger.error("❌ Health check failed")
                sys.exit(1)

        elif args.report:
            logger.info(f"📈 Generating {args.report}-day aggregate report...")
            report_path = collector.generate_aggregate_report(args.report)
            if report_path:
                logger.info(f"✅ Aggregate report generated: {report_path}")
                sys.exit(0)
            else:
                logger.error("❌ Failed to generate aggregate report")
                sys.exit(1)

        elif args.collect:
            # Standard collection process
            # Validate environment before starting
            if not collector.validate_environment():
                logger.error("❌ Environment validation failed - aborting collection")
                sys.exit(1)

            # Run health check
            if not collector.check_collection_health():
                logger.warning("⚠️  Collection health check failed - proceeding anyway")

            # Run collection cycle
            results = collector.run_collection_cycle()

            # Save detailed report
            report_path = collector.save_collection_report(results)

            # Exit with appropriate code
            if results["success"]:
                logger.info("✅ Automated collection completed successfully")
                sys.exit(0)
            else:
                logger.error("❌ Automated collection completed with errors")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT

    except Exception as e:
        logger.error(f"Critical error in automated collection: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
