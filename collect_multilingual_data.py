#!/usr/bin/env python3
"""
Multilingual Data Collection Script with configurable subreddits
Expands data collection to include diverse language communities and health-related subreddits
"""

import time
from datetime import datetime
from typing import List, Dict
import json
from pathlib import Path
from loguru import logger

from src.multilingual_scraper import MultilingualRedditScraper
from config.settings import ResearchConfig


class MultilingualHealthCollector:
    """Enhanced data collector targeting multilingual health communities"""

    def __init__(self, config_file="config/scraping_config.json"):
        self.scraper = MultilingualRedditScraper(
            enable_database=True, enable_translation=True
        )

        # Load configuration
        self.config = self._load_config(config_file)
        self.multilingual_subreddits = self.config.get("multilingual_subreddits", [])

        # Health keywords in multiple languages
        self.multilingual_keywords = self.config.get(
            "health_keywords",
            {
                "english": ResearchConfig.PRIMARY_KEYWORDS
                + ResearchConfig.COLLOQUIAL_TERMS,
                "spanish": [
                    "VIH",
                    "PrEP",
                    "sífilis",
                    "clamidia",
                    "gonorrea",
                    "condón",
                    "salud sexual",
                ],
                "tagalog": [
                    "HIV",
                    "PrEP",
                    "silis",
                    "STD",
                    "kalusugang sekswal",
                    "proteksyon",
                ],
                "chinese": [
                    "艾滋病",
                    "HIV",
                    "梅毒",
                    "淋病",
                    "衣原体",
                    "性健康",
                    "安全套",
                ],
                "french": [
                    "VIH",
                    "PrEP",
                    "syphilis",
                    "chlamydia",
                    "gonorrhée",
                    "santé sexuelle",
                ],
                "punjabi": ["HIV", "ਏਚਆਈਵੀ", "ਸਿਫਿਲਿਸ", "ਸੈਕਸੁਅਲ ਸਿਹਤ"],
            },
        )

    def _load_config(self, config_file):
        """Load configuration from JSON file"""
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            logger.warning(f"Config file {config_file} not found, using defaults")
            return {
                "multilingual_subreddits": [
                    "NewToCanada",
                    "ImmigrationCanada",
                    "immigrationlaw",
                    "PersonalFinanceCanada",
                    "toronto",
                    "vancouver",
                    "montreal",
                    "calgary",
                    "edmonton",
                    "askTO",
                    "vancouver4friends",
                    "HealthAnxiety",
                    "medical_advice",
                    "AskDocs",
                    "STD",
                    "std",
                    "HIV",
                    "sexualhealth",
                    "sexualhealthtalk",
                    "askgaybros",
                    "gaybros",
                    "lgbt",
                    "ainbow",
                    "gay_irl",
                    "torontogaybros",
                    "relationship_advice",
                    "TooAfraidToAsk",
                    "NoStupidQuestions",
                    "offmychest",
                    "CasualConversation",
                    "Philippines",
                    "canada",
                    "China",
                    "Chinese",
                    "italy",
                    "Spain",
                    "mexico",
                    "india",
                    "pakistan",
                ]
            }

    def add_subreddit(self, subreddit_name):
        """Add a subreddit to the collection list"""
        if subreddit_name not in self.multilingual_subreddits:
            self.multilingual_subreddits.append(subreddit_name)
            logger.info(f"Added r/{subreddit_name} to collection list")
            return True
        return False

    def remove_subreddit(self, subreddit_name):
        """Remove a subreddit from the collection list"""
        if subreddit_name in self.multilingual_subreddits:
            self.multilingual_subreddits.remove(subreddit_name)
            logger.info(f"Removed r/{subreddit_name} from collection list")
            return True
        return False

    def load_discovered_subreddits(
        self, discovered_file="data/discovered_subreddits.json"
    ):
        """Load discovered subreddits and add them to the collection list"""
        discovered_path = Path(discovered_file)
        if discovered_path.exists():
            with open(discovered_path, "r") as f:
                discovered = json.load(f)

            added_count = 0
            for subreddit_name in discovered.keys():
                if self.add_subreddit(subreddit_name):
                    added_count += 1

            logger.info(f"Added {added_count} discovered subreddits to collection list")
            return added_count
        else:
            logger.warning(f"Discovered subreddits file {discovered_file} not found")
            return 0

    def collect_targeted_multilingual_data(
        self, posts_per_subreddit: int = 50
    ) -> Dict[str, any]:
        """Collect data specifically targeting multilingual health discussions"""

        logger.info("🌐 Starting targeted multilingual health data collection...")

        collection_results = {
            "subreddit_stats": {},
            "language_distribution": {},
            "total_posts": 0,
            "translation_stats": {"success": 0, "failed": 0, "cached": 0},
            "newcomer_posts": 0,
            "health_keyword_posts": 0,
            "collection_timestamp": datetime.now().isoformat(),
        }

        successful_subreddits = 0
        failed_subreddits = []

        for subreddit in self.multilingual_subreddits:
            logger.info(f"🔍 Collecting from r/{subreddit}...")

            try:
                # Use the multilingual scraper
                posts = self.scraper.scrape_subreddit_multilingual(
                    subreddit, limit=posts_per_subreddit, skip_existing=True
                )

                if posts:
                    # Analyze this subreddit's data
                    subreddit_analysis = self._analyze_subreddit_data(posts, subreddit)
                    collection_results["subreddit_stats"][
                        subreddit
                    ] = subreddit_analysis

                    # Update global stats
                    self._update_global_stats(collection_results, subreddit_analysis)

                    successful_subreddits += 1
                    logger.info(
                        f"✅ r/{subreddit}: {len(posts)} posts, {subreddit_analysis['languages_found']} languages"
                    )
                else:
                    logger.info(f"⚪ r/{subreddit}: No relevant posts found")
                    failed_subreddits.append(f"{subreddit} (no posts)")

            except Exception as e:
                logger.error(f"❌ r/{subreddit}: Error - {e}")
                failed_subreddits.append(f"{subreddit} (error: {str(e)[:50]})")

            # Rate limiting
            time.sleep(3)

        # Generate collection summary
        collection_results["collection_summary"] = {
            "successful_subreddits": successful_subreddits,
            "failed_subreddits": len(failed_subreddits),
            "failed_list": failed_subreddits,
            "total_subreddits_attempted": len(self.multilingual_subreddits),
        }

        # Save detailed results
        self._save_collection_report(collection_results)

        # Log final results
        self._log_final_results(collection_results)

        return collection_results

    def _analyze_subreddit_data(self, posts: List[Dict], subreddit: str) -> Dict:
        """Analyze posts from a specific subreddit"""
        analysis = {
            "post_count": len(posts),
            "languages": {},
            "translations": 0,
            "newcomer_posts": 0,
            "health_posts": 0,
            "languages_found": 0,
            "avg_confidence": 0,
            "translation_methods": {},
        }

        confidence_scores = []

        for post in posts:
            # Language tracking
            lang = post.get("language", "unknown")
            analysis["languages"][lang] = analysis["languages"].get(lang, 0) + 1

            # Translation tracking
            if post.get("english_translation"):
                analysis["translations"] += 1

                # Track translation method
                method = post.get("translation_backend", "unknown")
                analysis["translation_methods"][method] = (
                    analysis["translation_methods"].get(method, 0) + 1
                )

                # Confidence scores
                confidence = post.get("translation_confidence")
                if confidence is not None:
                    confidence_scores.append(confidence)

            # Newcomer content
            if post.get("is_newcomer_related"):
                analysis["newcomer_posts"] += 1

            # Health content (check if contains health keywords)
            post_text = f"{post.get('title', '')} {post.get('selftext', '')}"
            if self._contains_health_keywords(post_text, post.get("language", "en")):
                analysis["health_posts"] += 1

        analysis["languages_found"] = len(analysis["languages"])
        if confidence_scores:
            analysis["avg_confidence"] = sum(confidence_scores) / len(confidence_scores)

        return analysis

    def _contains_health_keywords(self, text: str, language: str) -> bool:
        """Check if text contains health keywords in multiple languages"""
        if not text:
            return False

        text_lower = text.lower()

        # Check English keywords
        for keyword in self.multilingual_keywords["english"]:
            if keyword.lower() in text_lower:
                return True

        # Check language-specific keywords
        if language in ["es", "spanish"]:
            for keyword in self.multilingual_keywords["spanish"]:
                if keyword.lower() in text_lower:
                    return True
        elif language in ["tl", "tagalog"]:
            for keyword in self.multilingual_keywords["tagalog"]:
                if keyword.lower() in text_lower:
                    return True
        elif language in ["zh", "zh-cn", "zh-tw", "chinese"]:
            for keyword in self.multilingual_keywords["chinese"]:
                if keyword in text:  # Chinese doesn't need case conversion
                    return True
        elif language in ["fr", "french"]:
            for keyword in self.multilingual_keywords["french"]:
                if keyword.lower() in text_lower:
                    return True
        elif language in ["pa", "punjabi"]:
            for keyword in self.multilingual_keywords["punjabi"]:
                if keyword in text:  # Punjabi script doesn't need case conversion
                    return True

        return False

    def _update_global_stats(self, collection_results: Dict, subreddit_analysis: Dict):
        """Update global collection statistics"""
        collection_results["total_posts"] += subreddit_analysis["post_count"]
        collection_results["newcomer_posts"] += subreddit_analysis["newcomer_posts"]
        collection_results["health_keyword_posts"] += subreddit_analysis["health_posts"]

        # Update language distribution
        for lang, count in subreddit_analysis["languages"].items():
            collection_results["language_distribution"][lang] = (
                collection_results["language_distribution"].get(lang, 0) + count
            )

        # Update translation stats
        collection_results["translation_stats"]["success"] += subreddit_analysis[
            "translations"
        ]

    def _save_collection_report(self, results: Dict):
        """Save detailed collection report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data/multilingual_collection_report_{timestamp}.json"

        import json
        from pathlib import Path

        Path("data").mkdir(exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"📊 Collection report saved to {report_file}")

    def _log_final_results(self, results: Dict):
        """Log comprehensive final results"""
        logger.info("🎉 Multilingual Collection Complete!")
        logger.info("=" * 50)

        logger.info("📊 COLLECTION SUMMARY:")
        logger.info(f"  • Total posts collected: {results['total_posts']}")
        logger.info(
            f"  • Successful subreddits: {results['collection_summary']['successful_subreddits']}"
        )
        logger.info(f"  • Health-related posts: {results['health_keyword_posts']}")
        logger.info(f"  • Newcomer-focused posts: {results['newcomer_posts']}")

        logger.info("\n🌍 LANGUAGE DISTRIBUTION:")
        for lang, count in sorted(
            results["language_distribution"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (count / results["total_posts"] * 100)
                if results["total_posts"] > 0
                else 0
            )
            logger.info(f"  • {lang}: {count} posts ({percentage:.1f}%)")

        logger.info("\n🔄 TRANSLATION STATISTICS:")
        trans_stats = results["translation_stats"]
        total_translated = trans_stats["success"] + trans_stats["failed"]
        if total_translated > 0:
            success_rate = (trans_stats["success"] / total_translated) * 100
            logger.info(f"  • Translation success rate: {success_rate:.1f}%")
            logger.info(f"  • Successful translations: {trans_stats['success']}")
            logger.info(f"  • Failed translations: {trans_stats['failed']}")

        # Top performing subreddits
        logger.info("\n🏆 TOP MULTILINGUAL SUBREDDITS:")
        subreddit_scores = []
        for subreddit, stats in results["subreddit_stats"].items():
            multilingual_score = (
                stats["languages_found"] * stats["post_count"]
                + stats["translations"] * 2
            )
            subreddit_scores.append((subreddit, multilingual_score, stats))

        for subreddit, score, stats in sorted(
            subreddit_scores, key=lambda x: x[1], reverse=True
        )[:5]:
            logger.info(
                f"  • r/{subreddit}: {stats['post_count']} posts, {stats['languages_found']} languages, {stats['translations']} translations"
            )

        if results["collection_summary"]["failed_subreddits"] > 0:
            logger.info(
                f"\n⚠️  FAILED SUBREDDITS ({results['collection_summary']['failed_subreddits']}):"
            )
            for failed in results["collection_summary"]["failed_list"][
                :5
            ]:  # Show first 5
                logger.info(f"  • {failed}")

    def close(self):
        """Clean up resources"""
        self.scraper.close()


def main():
    """Run multilingual data collection"""
    print("🌐 Multilingual Health Data Collection")
    print("=" * 50)
    print("This will collect health-related posts from diverse communities")
    print("including immigrant, newcomer, and multilingual subreddits.\n")

    # Ask for configuration options
    collector = MultilingualHealthCollector()

    print(f"Loaded {len(collector.multilingual_subreddits)} subreddits from config")

    # Option to load discovered subreddits
    response = input("Load discovered subreddits? (y/n): ").lower().strip()
    if response == "y":
        added = collector.load_discovered_subreddits()
        print(f"Added {added} discovered subreddits")
        print(f"Total subreddits: {len(collector.multilingual_subreddits)}")

    # Ask for confirmation
    response = (
        input("Proceed with multilingual data collection? (y/n): ").lower().strip()
    )
    if response != "y":
        print("Collection cancelled.")
        return

    # Ask for posts per subreddit
    try:
        posts_per_sub = int(input("Posts per subreddit (default 50): ") or "50")
    except ValueError:
        posts_per_sub = 50

    print(f"\n🚀 Starting collection with {posts_per_sub} posts per subreddit...")

    collector = MultilingualHealthCollector()

    try:
        results = collector.collect_targeted_multilingual_data(
            posts_per_subreddit=posts_per_sub
        )

        print("\n✅ Collection completed successfully!")
        print(
            f"📊 Collected {results['total_posts']} posts from {len(results['language_distribution'])} languages"
        )
        print(f"🌍 Languages found: {list(results['language_distribution'].keys())}")

        # Refresh the analytics dashboard data
        print(
            "\n🔄 You can now refresh the analytics dashboard to see the new multilingual data!"
        )
        print("🌐 Dashboard URL: http://127.0.0.1:7862")

    except KeyboardInterrupt:
        print("\n⏹️  Collection interrupted by user")
    except Exception as e:
        logger.error(f"Collection failed: {e}")
    finally:
        collector.close()


if __name__ == "__main__":
    main()
