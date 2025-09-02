#!/usr/bin/env python3
"""
Enhanced multilingual Reddit scraper with translation support
Extends the base Reddit scraper to handle multiple languages
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

from src.reddit_scraper import RedditScraper
from src.translation_service import get_translation_service
from config.settings import Config, ResearchConfig


class MultilingualRedditScraper(RedditScraper):
    """
    Enhanced Reddit scraper with multilingual support
    Extends base scraper to detect, translate, and match content in multiple languages
    """
    
    def __init__(self, enable_database: bool = False, enable_translation: bool = True):
        super().__init__(enable_database)
        
        self.enable_translation = enable_translation
        self.translation_service = get_translation_service() if enable_translation else None
        
        # Load multilingual keywords if translation is enabled
        if self.enable_translation:
            self._initialize_multilingual_keywords()
        
        logger.info(f"Multilingual scraper initialized (translation: {enable_translation})")
    
    def _initialize_multilingual_keywords(self):
        """Initialize multilingual keyword matching"""
        try:
            # Get multilingual keywords from translation service
            multilingual_keywords = self.translation_service.get_health_keywords_multilingual()
            
            if len(multilingual_keywords) > len(self.keywords):
                self.keywords = multilingual_keywords
                logger.info(f"Loaded {len(multilingual_keywords)} multilingual keywords")
            else:
                logger.warning("No additional multilingual keywords loaded, using English only")
                
        except Exception as e:
            logger.error(f"Could not load multilingual keywords: {e}")
            logger.info("Falling back to English-only keywords")
    
    def detect_language(self, text: str) -> str:
        """Enhanced language detection using translation service"""
        if self.translation_service:
            return self.translation_service.detect_language(text)
        else:
            # Fallback to original method
            return super().detect_language(text)
    
    def contains_health_keywords(self, text: str) -> bool:
        """Enhanced multilingual keyword matching"""
        if not text:
            return False
        
        # Original English matching
        if super().contains_health_keywords(text):
            return True
        
        # If no translation service, stop here
        if not self.translation_service:
            return False
        
        # For non-English text, try translation-based matching
        detected_lang = self.detect_language(text)
        
        # Skip translation if already English or language unknown
        if detected_lang in ['en', 'unknown'] or len(text.strip()) < 10:
            return False
        
        try:
            # Translate to English for keyword matching
            translation_result = self.translation_service.translate_text(
                text, target_lang='en', source_lang=detected_lang
            )
            
            if translation_result.get('translation') and not translation_result.get('error'):
                translated_text = translation_result['translation']
                return super().contains_health_keywords(translated_text)
            
        except Exception as e:
            logger.debug(f"Translation failed for keyword matching: {e}")
        
        return False
    
    def scrape_subreddit_multilingual(self, subreddit_name: str, limit: int = None, 
                                     skip_existing: bool = True) -> List[Dict]:
        """
        Enhanced scraping with multilingual support and translation caching
        """
        if limit is None:
            limit = Config.MAX_POSTS_PER_SUBREDDIT
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts_data = []
        skipped_existing = 0
        translation_stats = {'cached': 0, 'translated': 0, 'failed': 0}
        
        logger.info(f"Multilingual scraping r/{subreddit_name}...")
        
        try:
            # Get recent posts
            for post in subreddit.new(limit=limit * 3):  # Over-sample to filter
                
                # Skip if already exists in database
                if self.enable_database and skip_existing and self.db_manager.post_exists(post.id):
                    skipped_existing += 1
                    continue
                
                # Check if post contains health keywords (multilingual)
                post_text = f"{post.title} {post.selftext}"
                if not self.contains_health_keywords(post_text):
                    continue
                
                # Detect language
                language = self.detect_language(post_text)
                
                # Handle translation for non-English content
                english_translation = None
                translation_confidence = None
                translation_backend = None
                
                if self.enable_translation and language not in ['en', 'unknown']:
                    try:
                        translation_result = self.translation_service.translate_text(
                            post_text, target_lang='en', source_lang=language
                        )
                        
                        if translation_result.get('translation') and not translation_result.get('error'):
                            english_translation = translation_result['translation']
                            translation_confidence = translation_result.get('confidence', 0.0)
                            translation_backend = translation_result.get('backend_used', 'unknown')
                            
                            # Update translation stats
                            if translation_backend == 'cache':
                                translation_stats['cached'] += 1
                            else:
                                translation_stats['translated'] += 1
                        else:
                            translation_stats['failed'] += 1
                            logger.debug(f"Translation failed for post {post.id}: {translation_result.get('error')}")
                    
                    except Exception as e:
                        translation_stats['failed'] += 1
                        logger.debug(f"Translation error for post {post.id}: {e}")
                
                # Check for newcomer indicators
                is_newcomer = self.is_newcomer_related(post_text)
                
                # Also check translated text for newcomer indicators
                if english_translation and not is_newcomer:
                    is_newcomer = self.is_newcomer_related(english_translation)
                
                post_data = {
                    'post_id': post.id,
                    'subreddit': subreddit_name,
                    'title': post.title,
                    'selftext': post.selftext,
                    'author': str(post.author) if post.author else '[deleted]',
                    'created_utc': datetime.fromtimestamp(post.created_utc),
                    'score': post.score,
                    'upvote_ratio': post.upvote_ratio,
                    'num_comments': post.num_comments,
                    'url': f"https://reddit.com{post.permalink}",
                    'language': language,
                    'is_newcomer_related': is_newcomer,
                    'full_text': post_text
                }
                
                # Add translation data if available
                if english_translation:
                    post_data['english_translation'] = english_translation
                    post_data['translation_confidence'] = translation_confidence
                    post_data['translation_backend'] = translation_backend
                
                # Extract comments with multilingual support
                comments = self.extract_comments_multilingual(post)
                post_data['comments'] = comments
                
                posts_data.append(post_data)
                
                # Respect rate limits
                time.sleep(0.1)
                
                if len(posts_data) >= limit:
                    break
            
            logger.info(f"Multilingual collection from r/{subreddit_name}:")
            logger.info(f"  ✅ Collected {len(posts_data)} relevant posts")
            logger.info(f"  📊 Translation stats: {translation_stats}")
            if skipped_existing > 0:
                logger.info(f"  ⏭️  Skipped {skipped_existing} existing posts")
            
            return posts_data
            
        except Exception as e:
            logger.error(f"Error in multilingual scraping r/{subreddit_name}: {e}")
            return []
    
    def extract_comments_multilingual(self, post) -> List[Dict]:
        """Extract comments with multilingual translation support"""
        comments_data = []
        
        try:
            post.comments.replace_more(limit=5)  # Limit for efficiency
            
            for comment in post.comments.list():
                if hasattr(comment, 'body') and len(comment.body) >= Config.MIN_COMMENT_LENGTH:
                    
                    # Detect language
                    language = self.detect_language(comment.body)
                    
                    # Handle translation for non-English comments
                    english_translation = None
                    translation_confidence = None
                    
                    if (self.enable_translation and language not in ['en', 'unknown'] 
                        and len(comment.body.strip()) >= 20):  # Only translate longer comments
                        
                        try:
                            translation_result = self.translation_service.translate_text(
                                comment.body, target_lang='en', source_lang=language
                            )
                            
                            if translation_result.get('translation') and not translation_result.get('error'):
                                english_translation = translation_result['translation']
                                translation_confidence = translation_result.get('confidence', 0.0)
                        
                        except Exception as e:
                            logger.debug(f"Comment translation failed: {e}")
                    
                    # Check for newcomer indicators in original and translated text
                    is_newcomer = self.is_newcomer_related(comment.body)
                    if english_translation and not is_newcomer:
                        is_newcomer = self.is_newcomer_related(english_translation)
                    
                    comment_data = {
                        'comment_id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'score': comment.score,
                        'parent_id': comment.parent_id,
                        'language': language,
                        'is_newcomer_related': is_newcomer
                    }
                    
                    # Add translation data if available
                    if english_translation:
                        comment_data['english_translation'] = english_translation
                        comment_data['translation_confidence'] = translation_confidence
                    
                    comments_data.append(comment_data)
        
        except Exception as e:
            logger.error(f"Error extracting multilingual comments: {e}")
        
        return comments_data
    
    def collect_all_data_multilingual(self, save_to_database: bool = None) -> List[Dict]:
        """Collect multilingual data from all target subreddits with performance monitoring"""
        if save_to_database is None:
            save_to_database = self.enable_database
        
        all_posts = []
        detailed_stats = self._initialize_detailed_stats()
        
        for subreddit in self.target_subreddits:
            logger.info(f"Processing subreddit: r/{subreddit}")
            posts = self.scrape_subreddit_multilingual(subreddit)
            all_posts.extend(posts)
            
            # Aggregate detailed translation and language stats
            subreddit_stats = self._analyze_posts_stats(posts)
            self._update_detailed_stats(detailed_stats, subreddit_stats, subreddit)
            
            # Save to database immediately if enabled
            if save_to_database and posts:
                db_stats = self.db_manager.bulk_save_posts(posts)
                logger.info(f"Database save stats for r/{subreddit}: {db_stats}")
            
            # Be respectful with API calls
            time.sleep(2)
        
        # Save raw multilingual data as backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/multilingual_reddit_data_{timestamp}.json"
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, default=str, ensure_ascii=False)
        
        # Generate and save performance report
        self._save_performance_report(detailed_stats, timestamp)
        
        # Log comprehensive results
        self._log_collection_results(all_posts, detailed_stats, filename, save_to_database)
        
        return all_posts
    
    def _initialize_detailed_stats(self) -> Dict:
        """Initialize detailed statistics tracking"""
        return {
            'total_posts': 0,
            'languages': {},
            'translation_backends': {'cached': 0, 'translated': 0, 'failed': 0},
            'backend_types': {},
            'subreddit_breakdown': {},
            'newcomer_posts': 0,
            'translation_confidence_scores': [],
            'processing_time': datetime.now()
        }
    
    def _analyze_posts_stats(self, posts: List[Dict]) -> Dict:
        """Analyze posts for detailed statistics"""
        stats = {
            'post_count': len(posts),
            'languages': {},
            'translations': {'cached': 0, 'translated': 0, 'failed': 0},
            'backend_types': {},
            'newcomer_count': 0,
            'confidence_scores': []
        }
        
        for post in posts:
            # Language distribution
            lang = post.get('language', 'unknown')
            stats['languages'][lang] = stats['languages'].get(lang, 0) + 1
            
            # Translation statistics
            if post.get('english_translation'):
                backend = post.get('translation_backend', 'unknown')
                if backend == 'cache':
                    stats['translations']['cached'] += 1
                else:
                    stats['translations']['translated'] += 1
                    
                # Track backend types
                stats['backend_types'][backend] = stats['backend_types'].get(backend, 0) + 1
                
                # Collect confidence scores
                confidence = post.get('translation_confidence')
                if confidence is not None:
                    stats['confidence_scores'].append(confidence)
            elif lang not in ['en', 'unknown']:
                stats['translations']['failed'] += 1
            
            # Newcomer tracking
            if post.get('is_newcomer_related'):
                stats['newcomer_count'] += 1
        
        return stats
    
    def _update_detailed_stats(self, detailed_stats: Dict, subreddit_stats: Dict, subreddit: str):
        """Update detailed statistics with subreddit data"""
        # Update totals
        detailed_stats['total_posts'] += subreddit_stats['post_count']
        detailed_stats['newcomer_posts'] += subreddit_stats['newcomer_count']
        
        # Merge language distributions
        for lang, count in subreddit_stats['languages'].items():
            detailed_stats['languages'][lang] = detailed_stats['languages'].get(lang, 0) + count
        
        # Update translation stats
        for stat_type, count in subreddit_stats['translations'].items():
            detailed_stats['translation_backends'][stat_type] += count
        
        # Update backend types
        for backend, count in subreddit_stats['backend_types'].items():
            detailed_stats['backend_types'][backend] = detailed_stats['backend_types'].get(backend, 0) + count
        
        # Store confidence scores
        detailed_stats['translation_confidence_scores'].extend(subreddit_stats['confidence_scores'])
        
        # Store subreddit breakdown
        detailed_stats['subreddit_breakdown'][subreddit] = subreddit_stats
    
    def _save_performance_report(self, detailed_stats: Dict, timestamp: str):
        """Save detailed performance report as JSON"""
        import json
        
        # Calculate summary statistics
        confidence_scores = detailed_stats['translation_confidence_scores']
        performance_report = {
            'collection_timestamp': timestamp,
            'processing_duration': str(datetime.now() - detailed_stats['processing_time']),
            'summary': {
                'total_posts_collected': detailed_stats['total_posts'],
                'newcomer_posts': detailed_stats['newcomer_posts'],
                'translation_performance': detailed_stats['translation_backends'],
                'language_distribution': detailed_stats['languages'],
                'translation_backends_used': detailed_stats['backend_types']
            },
            'translation_quality': {
                'total_translations': len(confidence_scores),
                'avg_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                'min_confidence': min(confidence_scores) if confidence_scores else 0,
                'max_confidence': max(confidence_scores) if confidence_scores else 0
            },
            'subreddit_breakdown': detailed_stats['subreddit_breakdown']
        }
        
        report_file = f"data/multilingual_performance_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(performance_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Performance report saved to {report_file}")
    
    def _log_collection_results(self, all_posts: List[Dict], detailed_stats: Dict, filename: str, save_to_database: bool):
        """Log comprehensive collection results"""
        logger.info(f"🌐 Multilingual Collection Complete!")
        logger.info(f"   📊 Total posts collected: {len(all_posts)}")
        
        # Language distribution
        languages = detailed_stats['languages']
        logger.info(f"   🌍 Languages detected: {len(languages)} languages")
        for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / detailed_stats['total_posts']) * 100 if detailed_stats['total_posts'] > 0 else 0
            logger.info(f"     • {lang}: {count} posts ({percentage:.1f}%)")
        
        # Translation performance
        trans_stats = detailed_stats['translation_backends']
        total_attempted = sum(trans_stats.values())
        if total_attempted > 0:
            logger.info(f"   🔄 Translation performance:")
            logger.info(f"     • Cached: {trans_stats['cached']} ({(trans_stats['cached']/total_attempted)*100:.1f}%)")
            logger.info(f"     • Translated: {trans_stats['translated']} ({(trans_stats['translated']/total_attempted)*100:.1f}%)")
            logger.info(f"     • Failed: {trans_stats['failed']} ({(trans_stats['failed']/total_attempted)*100:.1f}%)")
        
        # Translation quality
        confidence_scores = detailed_stats['translation_confidence_scores']
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            logger.info(f"   📈 Translation quality: {avg_confidence:.3f} avg confidence ({len(confidence_scores)} translations)")
        
        # Backend usage
        if detailed_stats['backend_types']:
            logger.info(f"   ⚙️  Translation backends used:")
            for backend, count in detailed_stats['backend_types'].items():
                logger.info(f"     • {backend}: {count} translations")
        
        logger.info(f"   👥 Newcomer-related posts: {detailed_stats['newcomer_posts']}")
        logger.info(f"   📁 Data saved to: {filename}")
        
        if save_to_database:
            db_stats = self.db_manager.get_collection_stats()
            logger.info(f"   💾 Database: {db_stats.get('total_posts', 0)} posts, {db_stats.get('total_comments', 0)} comments")
    
    def close(self):
        """Clean up resources"""
        if self.translation_service:
            self.translation_service.close()

def test_multilingual_scraping():
    """Test the multilingual scraping functionality"""
    print("🌐 Testing Multilingual Reddit Scraping")
    print("=" * 45)
    
    # Create multilingual scraper
    scraper = MultilingualRedditScraper(enable_database=True, enable_translation=True)
    
    # Test on a diverse subreddit
    posts = scraper.scrape_subreddit_multilingual('NewToCanada', limit=10)
    
    if posts:
        print(f"\n✅ SUCCESS: Collected {len(posts)} posts!")
        
        # Show language distribution
        languages = {}
        translations = 0
        
        for post in posts:
            lang = post.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1
            if post.get('english_translation'):
                translations += 1
        
        print(f"\n📊 Language Distribution:")
        for lang, count in languages.items():
            print(f"   {lang}: {count} posts")
        
        print(f"\n🔄 Translation Summary:")
        print(f"   Translated: {translations} posts")
        print(f"   English: {languages.get('en', 0)} posts")
        
        # Show sample translated post
        for post in posts:
            if post.get('english_translation'):
                print(f"\n📝 Sample Translation:")
                print(f"   Original ({post['language']}): {post['title'][:100]}...")
                print(f"   Translation: {post.get('english_translation', '')[:100]}...")
                print(f"   Backend: {post.get('translation_backend', 'unknown')}")
                print(f"   Confidence: {post.get('translation_confidence', 0.0):.2f}")
                break
    
    else:
        print("❌ No multilingual posts found")
    
    scraper.close()
    return posts

if __name__ == "__main__":
    # Run test
    test_multilingual_scraping()
