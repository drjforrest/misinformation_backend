"""
Main entry point for the Health Misinformation Detection Platform
"""

import argparse
from datetime import datetime
from loguru import logger
import os

# Setup logging
os.makedirs('logs', exist_ok=True)
logger.add(
    "logs/misinformation_analysis.log",
    rotation="1 week",
    retention="1 month",
    level="INFO"
)

def collect_data():
    """Run data collection from Reddit"""
    from src.reddit_scraper import RedditScraper
    
    logger.info("Starting Reddit data collection...")
    scraper = RedditScraper()
    
    # Collect data from all target subreddits
    data = scraper.collect_all_data()
    
    logger.info(f"Data collection complete: {len(data)} posts collected")
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

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Health Misinformation Detection Platform')
    
    parser.add_argument(
        'command',
        choices=['collect', 'analyze', 'annotate', 'demo'],
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
            print(f"   • Run: python main.py annotate --data-path {demo_path}")
            print(f"   • Or: python main.py analyze --data-path {demo_path}")

if __name__ == "__main__":
    main()
