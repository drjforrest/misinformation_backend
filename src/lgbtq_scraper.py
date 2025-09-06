#!/usr/bin/env python3
"""
LGBTQ+ Content Scraper for General Population Subreddits
Specialized scraper for collecting LGBTQ+-related content from diverse community subreddits
"""

import time
from datetime import datetime
from typing import Dict, List

from loguru import logger

from config.settings import Config, ResearchConfig
from src.reddit_scraper import RedditScraper
from src.translation_service import get_translation_service


class LGBTQScraper(RedditScraper):
    """
    Specialized scraper for LGBTQ+ content in general population subreddits
    Extends base scraper with LGBTQ+-focused keyword filtering and context awareness
    """

    def __init__(self, enable_database: bool = False, enable_translation: bool = True):
        super().__init__(enable_database)

        # Override target subreddits to focus on general population
        # Include both general population and some LGBTQ+ specific subs for training
        self.target_subreddits = (
            ResearchConfig.GENERAL_POPULATION_SUBREDDITS
            + ResearchConfig.LGBTQ_SUBREDDITS
            + ResearchConfig.CANADIAN_SUBREDDITS
        )

        # Use LGBTQ+ keywords instead of health keywords
        self.lgbtq_keywords = ResearchConfig.LGBTQ_KEYWORDS
        self.gay_terms = ResearchConfig.GAY_TERMS
        self.bi_terms = ResearchConfig.BI_TERMS
        self.msm_terms = ResearchConfig.MSM_TERMS

        # Initialize translation service
        self.enable_translation = enable_translation
        self.translation_service = (
            get_translation_service() if enable_translation else None
        )

        logger.info(
            f"Initialized LGBTQ+ scraper targeting {len(self.target_subreddits)} general population subreddits"
        )
        if enable_translation:
            logger.info("Translation service enabled for multilingual LGBTQ+ content")

    def contains_lgbtq_keywords(self, text: str) -> bool:
        """Check if text contains LGBTQ+-related keywords"""
        if not text:
            return False

        text_lower = text.lower()

        # Check main LGBTQ+ keywords
        for keyword in self.lgbtq_keywords:
            if keyword.lower() in text_lower:
                return True

        # Check identity-specific terms
        all_identity_terms = self.gay_terms + self.bi_terms + self.msm_terms
        for term in all_identity_terms:
            if term.lower() in text_lower:
                return True

        # Check for context patterns
        lgbtq_patterns = [
            r"\b(gay|bi|trans|queer|lesbian)\b.*\b(man|men|woman|women|people|community)\b",
            r"\b(attracted to|dating|interested in)\b.*\b(both|men|women|same sex)\b",
            r"\b(coming out|out of the closet)\b.*\b(as|to my)\b",
            r"\b(my|his|her)\b.*\b(boyfriend|girlfriend|partner)\b.*\b(is|was)\b",
            r"\b(pride|rainbow|lgbt)\b.*\b(month|flag|parade|event)\b",
            r"\b(gay|bi|trans)\b.*\b(rights|equality|marriage|law)\b",
        ]

        import re

        for pattern in lgbtq_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def identify_lgbtq_context(self, text: str) -> Dict[str, bool]:
        """Identify specific LGBTQ+ contexts in the text"""
        if not text:
            return {}

        text_lower = text.lower()
        contexts = {}

        # Check each identity context
        contexts["gay"] = any(term.lower() in text_lower for term in self.gay_terms)
        contexts["bi"] = any(term.lower() in text_lower for term in self.bi_terms)
        contexts["msm"] = any(term.lower() in text_lower for term in self.msm_terms)

        # Additional context detection
        contexts["general_lgbtq"] = any(
            keyword.lower() in text_lower for keyword in self.lgbtq_keywords
        )
        contexts["health_related"] = any(
            term in text_lower
            for term in ["health", "mental", "therapy", "doctor", "clinic"]
        )
        contexts["dating"] = any(
            term in text_lower
            for term in ["dating", "relationship", "partner", "boyfriend", "girlfriend"]
        )
        contexts["coming_out"] = any(
            term in text_lower
            for term in ["coming out", "out of the closet", "told my family"]
        )

        return contexts

    def detect_language(self, text: str) -> str:
        """Enhanced language detection using translation service"""
        if self.translation_service:
            return self.translation_service.detect_language(text)
        else:
            # Fallback to parent class method
            return super().detect_language(text)

    def translate_text(
        self, text: str, target_lang: str = "en", source_lang: str = "auto"
    ) -> Dict:
        """Translate text using translation service"""
        if self.translation_service:
            return self.translation_service.translate_text(
                text, target_lang, source_lang
            )
        else:
            return {
                "translation": text,
                "source_lang": "unknown",
                "target_lang": target_lang,
                "backend_used": "none",
                "confidence": 0.0,
                "error": "Translation service not available",
            }

    def scrape_subreddit_lgbtq(
        self, subreddit_name: str, limit: int = None, skip_existing: bool = True
    ) -> List[Dict]:
        """
        Scrape posts from a subreddit with LGBTQ+ focus
        """
        if limit is None:
            limit = Config.MAX_POSTS_PER_SUBREDDIT

        subreddit = self.reddit.subreddit(subreddit_name)
        posts_data = []
        skipped_existing = 0

        logger.info(f"Scraping r/{subreddit_name} for LGBTQ+-related posts...")

        try:
            # Get recent posts (last 30 days worth)
            for post in subreddit.new(limit=limit * 3):  # Over-sample to filter down
                # Skip if already exists in database
                if (
                    self.enable_database
                    and skip_existing
                    and self.db_manager.post_exists(post.id)
                ):
                    skipped_existing += 1
                    continue

                # Check if post contains LGBTQ+ keywords
                post_text = f"{post.title} {post.selftext}"
                if not self.contains_lgbtq_keywords(post_text):
                    continue

                # Detect language
                language = self.detect_language(post_text)

                # Handle translation for non-English content
                english_translation = None
                translation_confidence = None
                translation_backend = None

                if self.enable_translation and language not in ["en", "unknown"]:
                    try:
                        translation_result = self.translate_text(
                            post_text, target_lang="en", source_lang=language
                        )

                        if translation_result.get(
                            "translation"
                        ) and not translation_result.get("error"):
                            english_translation = translation_result["translation"]
                            translation_confidence = translation_result.get(
                                "confidence", 0.0
                            )
                            translation_backend = translation_result.get(
                                "backend_used", "unknown"
                            )

                            # Also check translated text for LGBTQ+ keywords and contexts
                            if not self.contains_lgbtq_keywords(post_text):
                                if self.contains_lgbtq_keywords(english_translation):
                                    # Include this post if translation reveals LGBTQ+ content
                                    pass
                                else:
                                    continue  # Skip if neither original nor translation has LGBTQ+ content
                        else:
                            logger.debug(
                                f"Translation failed for post {post.id}: {translation_result.get('error')}"
                            )

                    except Exception as e:
                        logger.debug(f"Translation error for post {post.id}: {e}")

                # Check for newcomer indicators (in both original and translated text)
                is_newcomer = self.is_newcomer_related(post_text)
                if english_translation and not is_newcomer:
                    is_newcomer = self.is_newcomer_related(english_translation)

                # Identify LGBTQ+ contexts (in both original and translated text)
                lgbtq_contexts = self.identify_lgbtq_context(post_text)
                if english_translation:
                    translated_contexts = self.identify_lgbtq_context(
                        english_translation
                    )
                    # Merge contexts (original takes precedence)
                    for context, value in translated_contexts.items():
                        if value and not lgbtq_contexts.get(context, False):
                            lgbtq_contexts[context] = value

                post_data = {
                    "post_id": post.id,
                    "subreddit": subreddit_name,
                    "title": post.title,
                    "selftext": post.selftext,
                    "author": str(post.author) if post.author else "[deleted]",
                    "created_utc": datetime.fromtimestamp(post.created_utc),
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "num_comments": post.num_comments,
                    "url": f"https://reddit.com{post.permalink}",
                    "language": language,
                    "is_newcomer_related": is_newcomer,
                    "full_text": post_text,
                    "lgbtq_contexts": lgbtq_contexts,
                    "primary_lgbtq_context": self._get_primary_context(lgbtq_contexts),
                }

                # Add translation data if available
                if english_translation:
                    post_data["english_translation"] = english_translation
                    post_data["translation_confidence"] = translation_confidence
                    post_data["translation_backend"] = translation_backend

                # Collect comments for network analysis
                comments = self.extract_comments_lgbtq(post)
                post_data["comments"] = comments

                posts_data.append(post_data)

                # Respect rate limits
                time.sleep(0.1)

                if len(posts_data) >= limit:
                    break

            logger.info(
                f"Collected {len(posts_data)} LGBTQ+-related posts from r/{subreddit_name}"
            )
            if skipped_existing > 0:
                logger.info(f"Skipped {skipped_existing} posts already in database")
            return posts_data

        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")
            return []

    def extract_comments_lgbtq(self, post) -> List[Dict]:
        """Extract comments with LGBTQ+ context analysis"""
        comments_data = []

        try:
            post.comments.replace_more(limit=10)  # Load more comments

            for comment in post.comments.list():
                if (
                    hasattr(comment, "body")
                    and len(comment.body) >= Config.MIN_COMMENT_LENGTH
                ):
                    # Identify LGBTQ+ contexts in comment
                    lgbtq_contexts = self.identify_lgbtq_context(comment.body)

                    comment_data = {
                        "comment_id": comment.id,
                        "author": (
                            str(comment.author) if comment.author else "[deleted]"
                        ),
                        "body": comment.body,
                        "created_utc": datetime.fromtimestamp(comment.created_utc),
                        "score": comment.score,
                        "parent_id": comment.parent_id,
                        "language": self.detect_language(comment.body),
                        "is_newcomer_related": self.is_newcomer_related(comment.body),
                        "lgbtq_contexts": lgbtq_contexts,
                        "primary_lgbtq_context": self._get_primary_context(
                            lgbtq_contexts
                        ),
                    }

                    comments_data.append(comment_data)

        except Exception as e:
            logger.error(f"Error extracting LGBTQ+ comments: {e}")

        return comments_data

    def _get_primary_context(self, contexts: Dict[str, bool]) -> str:
        """Determine the primary LGBTQ+ context"""
        # Priority order for contexts
        priority_order = ["gay", "bi", "msm", "general_lgbtq"]

        for context in priority_order:
            if contexts.get(context, False):
                return context

        return "general_lgbtq" if contexts.get("general_lgbtq", False) else "unknown"

    def collect_lgbtq_data(self, save_to_database: bool = None) -> List[Dict]:
        """Collect LGBTQ+ data from all target general population subreddits"""
        if save_to_database is None:
            save_to_database = self.enable_database

        all_posts = []

        for subreddit in self.target_subreddits:
            logger.info(f"Processing subreddit: r/{subreddit}")
            posts = self.scrape_subreddit_lgbtq(subreddit)
            all_posts.extend(posts)

            # Save to database immediately if enabled
            if save_to_database and posts:
                stats = self.db_manager.bulk_save_posts(posts)
                logger.info(f"Database save stats for r/{subreddit}: {stats}")

            # Be respectful with API calls
            time.sleep(2)

        # Save raw data as backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/lgbtq_reddit_data_{timestamp}.json"

        import json

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(all_posts, f, indent=2, default=str, ensure_ascii=False)

        logger.info(
            f"Collected {len(all_posts)} total LGBTQ+ posts, saved to {filename}"
        )

        if save_to_database:
            # Get final database stats
            db_stats = self.db_manager.get_collection_stats()
            logger.info(
                f"Database now contains: {db_stats.get('total_posts', 0)} posts, {db_stats.get('total_comments', 0)} comments"
            )

        return all_posts

    def get_lgbtq_content_stats(self, posts: List[Dict]) -> Dict:
        """Generate statistics about collected LGBTQ+ content"""
        stats = {
            "total_posts": len(posts),
            "context_distribution": {},
            "subreddit_distribution": {},
            "language_distribution": {},
            "newcomer_posts": 0,
        }

        for post in posts:
            # Context distribution
            context = post.get("primary_lgbtq_context", "unknown")
            stats["context_distribution"][context] = (
                stats["context_distribution"].get(context, 0) + 1
            )

            # Subreddit distribution
            subreddit = post.get("subreddit", "unknown")
            stats["subreddit_distribution"][subreddit] = (
                stats["subreddit_distribution"].get(subreddit, 0) + 1
            )

            # Language distribution
            language = post.get("language", "unknown")
            stats["language_distribution"][language] = (
                stats["language_distribution"].get(language, 0) + 1
            )

            # Newcomer tracking
            if post.get("is_newcomer_related"):
                stats["newcomer_posts"] += 1

        return stats

    def close(self):
        """Clean up resources"""
        if self.translation_service:
            self.translation_service.close()
        super().close() if hasattr(super(), "close") else None


def collect_lgbtq_training_data():
    """Main function to collect LGBTQ+ training data"""
    logger.info("🏳️‍🌈 Starting LGBTQ+ Data Collection for Training")
    logger.info("=" * 50)

    scraper = LGBTQScraper(enable_database=True)

    # Collect data
    posts = scraper.collect_lgbtq_data()

    if posts:
        # Generate and display statistics
        stats = scraper.get_lgbtq_content_stats(posts)

        print("\n📊 Collection Statistics:")
        print(f"Total LGBTQ+ posts collected: {stats['total_posts']}")
        print(f"Newcomer-related posts: {stats['newcomer_posts']}")

        print("\n🌈 Context Distribution:")
        for context, count in sorted(
            stats["context_distribution"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (count / stats["total_posts"]) * 100 if stats["total_posts"] > 0 else 0
            )
            print(f"  {context}: {count} posts ({percentage:.1f}%)")

        print("\n📍 Top Subreddits:")
        for subreddit, count in sorted(
            stats["subreddit_distribution"].items(), key=lambda x: x[1], reverse=True
        )[:10]:
            print(f"  r/{subreddit}: {count} posts")

        print("\n🗣️ Language Distribution:")
        for language, count in sorted(
            stats["language_distribution"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (
                (count / stats["total_posts"]) * 100 if stats["total_posts"] > 0 else 0
            )
            print(f"  {language}: {count} posts ({percentage:.1f}%)")

    else:
        print("❌ No LGBTQ+ posts found")

    return posts


if __name__ == "__main__":
    collect_lgbtq_training_data()
