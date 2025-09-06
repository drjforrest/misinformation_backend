"""
Main entry point for the Health Misinformation Detection Platform
"""

import argparse
import json
import os
from datetime import datetime
from typing import Dict, Optional

from loguru import logger

from src.network_analysis import NetworkAnalyzer

# Setup logging
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/misinformation_analysis.log",
    rotation="1 week",
    retention="1 month",
    level="INFO",
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
    from src.data_persistence import DataPersistenceManager
    from src.reddit_scraper import RedditScraper

    logger.info("Starting Reddit data collection with database persistence...")

    # Get pre-collection stats
    db_manager = DataPersistenceManager()
    pre_stats = db_manager.get_collection_stats()
    logger.info(
        f"Database contains {pre_stats.get('total_posts', 0)} posts before collection"
    )

    # Run collection with database enabled
    scraper = RedditScraper(enable_database=True)
    data = scraper.collect_all_data(save_to_database=True)

    # Get post-collection stats
    post_stats = db_manager.get_collection_stats()

    logger.info(f"Data collection complete: {len(data)} posts collected")
    logger.info(
        f"Database now contains: {post_stats.get('total_posts', 0)} posts total"
    )

    return data


def collect_multilingual_data():
    """Run multilingual data collection from Reddit (file-based)"""
    from src.multilingual_scraper import MultilingualRedditScraper

    logger.info("Starting multilingual Reddit data collection (file-based)...")
    scraper = MultilingualRedditScraper(enable_database=False, enable_translation=True)

    # Collect data from all target subreddits with translation support
    data = scraper.collect_all_data_multilingual(save_to_database=False)

    logger.info(f"Multilingual data collection complete: {len(data)} posts collected")
    return data


def collect_multilingual_data_to_database():
    """Run multilingual data collection from Reddit with database persistence"""
    from src.data_persistence import DataPersistenceManager
    from src.multilingual_scraper import MultilingualRedditScraper

    logger.info(
        "Starting multilingual Reddit data collection with database persistence..."
    )

    # Get pre-collection stats
    db_manager = DataPersistenceManager()
    pre_stats = db_manager.get_collection_stats()
    logger.info(
        f"Database contains {pre_stats.get('total_posts', 0)} posts before collection"
    )

    # Run collection with database enabled and translation support
    scraper = MultilingualRedditScraper(enable_database=True, enable_translation=True)
    data = scraper.collect_all_data_multilingual(save_to_database=True)

    # Get post-collection stats
    post_stats = db_manager.get_collection_stats()

    logger.info(f"Multilingual data collection complete: {len(data)} posts collected")
    logger.info(
        f"Database now contains: {post_stats.get('total_posts', 0)} posts total"
    )

    return data


def translate_keywords():
    """Generate multilingual health keyword translations"""
    from src.translation_service import TranslationService

    logger.info("Generating multilingual health keyword translations...")

    service = TranslationService()
    translations = service.translate_health_keywords()

    logger.info(f"✅ Keyword translations complete: {len(translations)} languages")

    # Show summary
    for lang, keywords in translations.items():
        logger.info(f"  {lang}: {len(keywords)} keywords translated")

    service.close()
    return translations


def analyze_network(data_path: str = None):
    """Run community resilience network analysis"""
    logger.info("Starting community resilience network analysis")

    # Try database-based analysis first (preferred for community resilience)
    try:
        network_data = NetworkAnalyzer().build_user_network()

        if network_data and network_data.get("nodes"):
            logger.info(
                f"Database analysis: Found {len(network_data['nodes'])} community members in support network"
            )

            # Generate database-based network report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = f"data/community_network_report_{timestamp}.json"

            with open(report_path, "w") as f:
                json.dump(network_data, f, indent=2)

            logger.info(f"Community network analysis saved to {report_path}")
            print("\n🤝 Community Support Network Analysis Complete!")
            print(
                f"   • Network nodes (community members): {len(network_data['nodes'])}"
            )
            print(
                f"   • Network edges (supportive interactions): {len(network_data.get('edges', []))}"
            )
            print(f"   • Analysis saved to: {report_path}")
            print("   • View network: python launch_community_resilience.py")
            return network_data

    except Exception as e:
        logger.warning(f"Database network analysis failed: {e}")
        print(
            "⚠️  Database network analysis unavailable, falling back to file-based analysis"
        )

    # Fallback to file-based analysis if database analysis fails
    if data_path:
        logger.info(f"Using file-based network analysis on {data_path}")
        from src.network_analysis import MisinformationNetwork

        network = MisinformationNetwork()
        network.load_data(data_path)
        network.build_interaction_network()

        # Generate report (reinterpreted as community interaction analysis)
        report = network.generate_network_report()

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"data/network_report_{timestamp}.json"

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Network analysis complete. Report saved to {report_path}")
        return report
    else:
        logger.error("No data source available for network analysis")
        print("❌ Error: No database data or file path provided for network analysis")
        return None


def launch_annotation_tool(limit: int = 100, filter_criteria: Optional[Dict] = None):
    """Launch the Gradio annotation interface with database-driven loading"""
    from gradio_app.annotation_interface import AnnotationInterface

    logger.info("Launching database-driven annotation interface...")

    annotation_tool = AnnotationInterface(limit=limit, filter_criteria=filter_criteria)
    annotation_tool.launch(share=False)


def launch_enhanced_annotation_tool(
    limit: int = 100, filter_criteria: Optional[Dict] = None
):
    """Launch the enhanced Gradio annotation interface with database-driven loading"""
    from gradio_app.enhanced_annotation_interface import EnhancedAnnotationInterface

    logger.info("Launching enhanced database-driven annotation interface...")

    annotation_tool = EnhancedAnnotationInterface(
        limit=limit, filter_criteria=filter_criteria
    )
    annotation_tool.launch(share=False)


def create_visualizations(data_path: str, output_dir: str = "visualizations"):
    """Generate comprehensive research visualizations"""
    from src.research_visualizations import ResearchVisualizations

    logger.info(f"Creating research visualizations for {data_path}...")

    viz = ResearchVisualizations(data_path)
    saved_files = viz.save_all_visualizations(output_dir)

    logger.info(f"Generated {len(saved_files)} visualizations in {output_dir}/")

    print("\n📊 Research Visualizations Generated:")
    for name, path in saved_files.items():
        print(f"   🎯 {name.title()}: {path}")

    print("\n🌟 Open these HTML files in your browser for interactive analysis!")

    return saved_files


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Health Misinformation Detection Platform"
    )

    parser.add_argument(
        "command",
        choices=[
            "collect",
            "collect-db",
            "collect-multilingual",
            "collect-multilingual-db",
            "translate-keywords",
            "analyze",
            "annotate",
            "annotate-enhanced",
            "visualize",
            "demo",
        ],
        help="Command to run",
    )

    parser.add_argument(
        "--data-path",
        type=str,
        help="Path to data file for analysis or annotation (legacy support)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Limit number of posts to load for annotation",
    )

    parser.add_argument(
        "--subreddit",
        type=str,
        help="Filter posts by specific subreddit for annotation",
    )

    parser.add_argument(
        "--language", type=str, help="Filter posts by language for annotation"
    )

    args = parser.parse_args()

    if args.command == "collect":
        collect_data()

    elif args.command == "collect-db":
        collect_data_to_database()

    elif args.command == "collect-multilingual":
        collect_multilingual_data()

    elif args.command == "collect-multilingual-db":
        collect_multilingual_data_to_database()

    elif args.command == "translate-keywords":
        translate_keywords()

    elif args.command == "analyze":
        # data_path is now optional - prefer database analysis
        analyze_network(args.data_path)

    elif args.command == "annotate":
        # Build filter criteria from command line arguments
        filter_criteria = {}
        if args.subreddit:
            filter_criteria["subreddit"] = args.subreddit
        if args.language:
            filter_criteria["language"] = args.language

        # Use data-path for legacy support, but prefer database-driven approach
        if args.data_path:
            logger.warning(
                "Using legacy JSON file mode. Consider using database-driven annotation without --data-path"
            )
            # For backward compatibility, still support JSON file loading
            import json

            from gradio_app.annotation_interface import AnnotationInterface

            with open(args.data_path, "r") as f:
                legacy_data = json.load(f)
            # Create a legacy interface instance that works with the loaded data
            annotation_tool = AnnotationInterface.__new__(AnnotationInterface)
            annotation_tool.posts_data = legacy_data
            annotation_tool.current_post_index = 0
            annotation_tool.annotation_db = "data/annotations.db"
            annotation_tool.init_database()
            annotation_tool.session_stats = {
                "posts_reviewed": 0,
                "session_start": datetime.now(),
            }
            annotation_tool.current_user = "default_user"
            annotation_tool.launch(share=False)
        else:
            launch_annotation_tool(limit=args.limit, filter_criteria=filter_criteria)

    elif args.command == "annotate-enhanced":
        # Build filter criteria from command line arguments
        filter_criteria = {}
        if args.subreddit:
            filter_criteria["subreddit"] = args.subreddit
        if args.language:
            filter_criteria["language"] = args.language

        # Use data-path for legacy support, but prefer database-driven approach
        if args.data_path:
            logger.warning(
                "Using legacy JSON file mode. Consider using database-driven annotation without --data-path"
            )
            # For backward compatibility, still support JSON file loading
            import json

            from gradio_app.enhanced_annotation_interface import (
                EnhancedAnnotationInterface,
            )

            with open(args.data_path, "r") as f:
                legacy_data = json.load(f)
            # Create a legacy interface instance that works with the loaded data
            annotation_tool = EnhancedAnnotationInterface.__new__(
                EnhancedAnnotationInterface
            )
            annotation_tool.posts_data = legacy_data
            annotation_tool.current_post_index = 0
            annotation_tool.annotation_db = "data/enhanced_annotations.db"
            annotation_tool.init_enhanced_database()
            annotation_tool.session_stats = {
                "posts_reviewed": 0,
                "session_start": datetime.now(),
            }
            annotation_tool.current_user = "default_user"
            annotation_tool.launch(share=False)
        else:
            launch_enhanced_annotation_tool(
                limit=args.limit, filter_criteria=filter_criteria
            )

    elif args.command == "visualize":
        if not args.data_path:
            logger.error("--data-path required for visualization")
            return
        create_visualizations(args.data_path)

    elif args.command == "demo":
        logger.info("Running demo workflow...")

        # Quick data collection
        from src.reddit_scraper import RedditScraper

        scraper = RedditScraper()

        # Just collect from one subreddit for demo
        demo_data = scraper.scrape_subreddit("askgaybros", limit=args.limit)

        # Save demo data
        demo_path = f"data/demo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(demo_path, "w") as f:
            json.dump(demo_data, f, indent=2, default=str)

        logger.info(f"Demo data collected: {len(demo_data)} posts saved to {demo_path}")

        # Run basic community resilience analysis
        if demo_data:
            # Convert demo data to expected format
            with open(demo_path, "r") as f:
                data = json.load(f)

            # Quick community analysis
            total_posts = len(data)
            languages = {}
            newcomer_count = 0

            for post in data:
                lang = post.get("language", "unknown")
                languages[lang] = languages.get(lang, 0) + 1
                if post.get("is_newcomer_related"):
                    newcomer_count += 1

            print("\n🤝 Community Resilience Demo Results:")
            print(f"   • Total community posts collected: {total_posts}")
            print(f"   • Languages in community discussions: {list(languages.keys())}")
            print(f"   • Posts supporting newcomers: {newcomer_count}")
            print(f"   • Community data saved to: {demo_path}")

            # Auto-generate visualizations for demo
            print("\n📊 Generating community analysis visualizations...")
            create_visualizations(demo_path, "demo_visualizations")

            print("\n💡 Next steps for community resilience research:")
            print(
                "   • View community patterns: Open demo_visualizations/*.html in browser"
            )
            print(
                f"   • Community analysis: python main.py annotate --data-path {demo_path}"
            )
            print("   • Research interface: python launch_research_annotation.py")
            print("   • Resilience analysis: python launch_community_resilience.py")
            print(
                f"   • Support network analysis: python main.py analyze --data-path {demo_path}"
            )
            print(
                f"   • Generate more visualizations: python main.py visualize --data-path {demo_path}"
            )


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
