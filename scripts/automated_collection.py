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

import sys
import os
import json
import traceback
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reddit_scraper import RedditScraper
from src.data_persistence import DataPersistenceManager
from config.settings import Config, ResearchConfig

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
        os.makedirs('logs', exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add file logger with rotation
        logger.add(
            "logs/automated_collection.log",
            rotation="1 week",
            retention="2 months",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )
        
        # Add console logger for cron job output
        logger.add(
            sys.stdout,
            level="INFO",
            format="{time:HH:mm:ss} | {level} | {message}"
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
                test_subreddit = self.scraper.reddit.subreddit('test')
                test_subreddit.display_name  # This will fail if auth is broken
                logger.info("✅ Reddit API authentication successful")
            except Exception as e:
                logger.error(f"❌ Reddit API authentication failed: {e}")
                return False
            
            # Test database connection
            try:
                stats = self.db_manager.get_collection_stats()
                if 'error' in stats:
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
            'start_time': cycle_start,
            'success': False,
            'posts_collected': 0,
            'posts_saved': 0,
            'posts_updated': 0,
            'errors': 0,
            'subreddit_results': {},
            'duration_seconds': 0
        }
        
        try:
            logger.info("Starting data collection cycle...")
            
            # Get pre-collection database stats
            pre_stats = self.db_manager.get_collection_stats()
            logger.info(f"Database contains {pre_stats.get('total_posts', 0)} posts before collection")
            
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
                        skip_existing=True
                    )
                    
                    subreddit_stats = {
                        'posts_collected': len(posts),
                        'posts_saved': 0,
                        'posts_updated': 0,
                        'errors': 0
                    }
                    
                    total_collected += len(posts)
                    
                    # Save to database if we got posts
                    if posts:
                        db_stats = self.db_manager.bulk_save_posts(posts)
                        subreddit_stats.update(db_stats)
                        
                        total_db_saves += db_stats.get('saved', 0)
                        total_db_updates += db_stats.get('updated', 0) 
                        total_errors += db_stats.get('errors', 0)
                        
                        logger.info(f"r/{subreddit}: {len(posts)} posts → DB: {db_stats}")
                    else:
                        logger.info(f"r/{subreddit}: No new health-related posts found")
                    
                    results['subreddit_results'][subreddit] = subreddit_stats
                    
                    # Rate limiting between subreddits
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing r/{subreddit}: {e}")
                    results['subreddit_results'][subreddit] = {'error': str(e)}
                    total_errors += 1
            
            # Update results
            results.update({
                'posts_collected': total_collected,
                'posts_saved': total_db_saves,
                'posts_updated': total_db_updates,
                'errors': total_errors,
                'success': total_errors == 0 or total_collected > 0
            })
            
            # Get post-collection database stats
            post_stats = self.db_manager.get_collection_stats()
            
            results['final_database_stats'] = post_stats
            
            cycle_end = datetime.now()
            results['duration_seconds'] = (cycle_end - cycle_start).total_seconds()
            
            logger.info(f"🎯 Collection cycle complete in {results['duration_seconds']:.1f}s")
            logger.info(f"   📈 Collected: {total_collected} posts")
            logger.info(f"   💾 Database: {total_db_saves} saved, {total_db_updates} updated")
            logger.info(f"   📊 Total in DB: {post_stats.get('total_posts', 0)} posts")
            
            if total_errors > 0:
                logger.warning(f"   ⚠️  {total_errors} errors occurred")
            
            return results
            
        except Exception as e:
            logger.error(f"Critical error in collection cycle: {e}")
            logger.error(traceback.format_exc())
            results['error'] = str(e)
            results['duration_seconds'] = (datetime.now() - cycle_start).total_seconds()
            return results
    
    def save_collection_report(self, results: Dict) -> str:
        """Save detailed collection report to file"""
        try:
            os.makedirs('data/reports', exist_ok=True)
            
            timestamp = results['start_time'].strftime("%Y%m%d_%H%M%S")
            report_path = f"data/reports/collection_report_{timestamp}.json"
            
            # Make datetime objects JSON serializable
            serializable_results = json.loads(json.dumps(results, default=str))
            
            with open(report_path, 'w') as f:
                json.dump(serializable_results, f, indent=2)
            
            logger.info(f"📋 Collection report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to save collection report: {e}")
            return ""
    
    def check_collection_health(self) -> bool:
        """Check if recent collections are working properly"""
        try:
            stats = self.db_manager.get_collection_stats()
            
            if stats.get('total_posts', 0) == 0:
                logger.warning("⚠️  No posts in database - may indicate collection issues")
                return False
            
            # Check if we have recent data (within last 48 hours)
            latest_post = stats.get('latest_post_date')
            if latest_post:
                if isinstance(latest_post, str):
                    latest_post = datetime.fromisoformat(latest_post.replace('Z', '+00:00'))
                
                hours_since_latest = (datetime.now() - latest_post).total_seconds() / 3600
                
                if hours_since_latest > 48:
                    logger.warning(f"⚠️  Latest post is {hours_since_latest:.1f} hours old")
                    return False
                else:
                    logger.info(f"✅ Latest post is {hours_since_latest:.1f} hours old")
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

def main():
    """Main entry point for automated collection"""
    try:
        collector = AutomatedCollector()
        
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
        if results['success']:
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
