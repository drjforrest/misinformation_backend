"""
Main entry point for the Health Misinformation Detection Platform
"""

import argparse
from datetime import datetime
from loguru import logger
import os
import json

# Setup logging
os.makedirs('logs', exist_ok=True)
logger.add(
    "logs/misinformation_analysis.log",
    rotation="1 week",
    retention="1 month",
    level="INFO"
)

def collect_data():
    """Run data collection from Reddit (file-based)"""
    from src.reddit_scraper import RedditScraper
    
    logger.info("Starting Reddit data collection (file-based)...")
    scraper = RedditScraper()
    
    # Collect data from all target subreddits
    data = scraper.collect_all_data()
    
    logger.info(f"Data collection complete: {len(data)} posts collected")
    return data

def collect_data_to_database():
    """Run data collection from Reddit with database persistence"""
    from src.reddit_scraper import RedditScraper
    from src.data_persistence import DataPersistenceManager
    
    logger.info("Starting Reddit data collection with database persistence...")
    
    # Get pre-collection stats
    db_manager = DataPersistenceManager()
    pre_stats = db_manager.get_collection_stats()
    logger.info(f"Database contains {pre_stats.get('total_posts', 0)} posts before collection")
    
    # Run collection with database enabled
    scraper = RedditScraper(enable_database=True)
    data = scraper.collect_all_data(save_to_database=True)
    
    # Get post-collection stats
    post_stats = db_manager.get_collection_stats()
    
    logger.info(f"Data collection complete: {len(data)} posts collected")
    logger.info(f"Database now contains: {post_stats.get('total_posts', 0)} posts total")
    
    return data

def analyze_network(data_path: str):
    """Run network analysis on collected data"""
    from src.network_analysis import MisinformationNetwork
    
    logger.info(f"Starting network analysis on {data_path}")
    
    network = MisinformationNetwork()
    network.load_data(data_path)
    network.build_interaction_network()
    
    # Generate report
    report = network.generate_network_report()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"data/network_report_{timestamp}.json"
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Network analysis complete. Report saved to {report_path}")
    return report

def launch_annotation_tool(data_path: str):
    """Launch the Gradio annotation interface"""
    from gradio_app.annotation_interface import AnnotationInterface
    
    logger.info("Launching annotation interface...")
    
    annotation_tool = AnnotationInterface(data_path)
    annotation_tool.launch(share=False)

def launch_enhanced_annotation_tool(data_path: str):
    """Launch the enhanced Gradio annotation interface with full schema support"""
    from gradio_app.enhanced_annotation_interface import EnhancedAnnotationInterface
    
    logger.info("Launching enhanced annotation interface...")
    
    annotation_tool = EnhancedAnnotationInterface(data_path)
    annotation_tool.launch(share=False)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Health Misinformation Detection Platform')
    
    parser.add_argument(
        'command',
        choices=['collect', 'collect-db', 'analyze', 'annotate', 'annotate-enhanced', 'demo'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--data-path',
        type=str,
        help='Path to data file for analysis or annotation'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Limit number of posts to collect (for demo)'
    )
    
    args = parser.parse_args()
    
    if args.command == 'collect':
        collect_data()
    
    elif args.command == 'collect-db':
        collect_data_to_database()
    
    elif args.command == 'analyze':
        if not args.data_path:
            logger.error("--data-path required for analysis")
            return
        analyze_network(args.data_path)
    
    elif args.command == 'annotate':
        if not args.data_path:
            logger.error("--data-path required for annotation")
            return
        launch_annotation_tool(args.data_path)
    
    elif args.command == 'annotate-enhanced':
        if not args.data_path:
            logger.error("--data-path required for enhanced annotation")
            return
        launch_enhanced_annotation_tool(args.data_path)
    
    elif args.command == 'demo':
        logger.info("Running demo workflow...")
        
        # Quick data collection
        from src.reddit_scraper import RedditScraper
        scraper = RedditScraper()
        
        # Just collect from one subreddit for demo
        demo_data = scraper.scrape_subreddit('askgaybros', limit=args.limit)
        
        # Save demo data
        demo_path = f"data/demo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(demo_path, 'w') as f:
            json.dump(demo_data, f, indent=2, default=str)
        
        logger.info(f"Demo data collected: {len(demo_data)} posts saved to {demo_path}")
        
        # Run basic analysis
        if demo_data:
            from src.network_analysis import MisinformationNetwork
            network = MisinformationNetwork()
            
            # Convert demo data to expected format
            with open(demo_path, 'r') as f:
                data = json.load(f)
            
            # Quick analysis
            total_posts = len(data)
            languages = {}
            newcomer_count = 0
            
            for post in data:
                lang = post.get('language', 'unknown')
                languages[lang] = languages.get(lang, 0) + 1
                if post.get('is_newcomer_related'):
                    newcomer_count += 1
            
            print(f"\n🎯 Demo Results:")
            print(f"   • Total posts collected: {total_posts}")
            print(f"   • Languages detected: {list(languages.keys())}")
            print(f"   • Newcomer-related posts: {newcomer_count}")
            print(f"   • Data saved to: {demo_path}")
            print(f"\n💡 Next steps:")
            print(f"   • Basic annotation: python main.py annotate --data-path {demo_path}")
            print(f"   • Enhanced annotation: python main.py annotate-enhanced --data-path {demo_path}")
            print(f"   • Network analysis: python main.py analyze --data-path {demo_path}")

if __name__ == "__main__":
    main()
