"""
Reddit data collection module for health misinformation research
"""

import praw
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from langdetect import detect
from loguru import logger
import time

from config.settings import Config, ResearchConfig

class RedditScraper:
    """Handles Reddit API interactions and data collection"""
    
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=Config.REDDIT_CLIENT_ID,
            client_secret=Config.REDDIT_CLIENT_SECRET,
            user_agent=Config.REDDIT_USER_AGENT
        )
        
        # Combine all target keywords
        self.keywords = (ResearchConfig.PRIMARY_KEYWORDS + 
                        ResearchConfig.COLLOQUIAL_TERMS)
        
        # All target subreddits
        self.target_subreddits = (ResearchConfig.LGBTQ_SUBREDDITS + 
                                 ResearchConfig.CANADIAN_SUBREDDITS + 
                                 ResearchConfig.NEWCOMER_SUBREDDITS)
        
        logger.info(f"Initialized Reddit scraper targeting {len(self.target_subreddits)} subreddits")
    
    def contains_health_keywords(self, text: str) -> bool:
        """Check if text contains any of our target health keywords"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.keywords)
    
    def detect_language(self, text: str) -> str:
        """Detect language of text content"""
        try:
            if len(text.strip()) < 10:  # Too short to reliably detect
                return 'unknown'
            return detect(text)
        except:
            return 'unknown'
    
    def is_newcomer_related(self, text: str) -> bool:
        """Check if text contains newcomer/immigrant indicators"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(phrase.lower() in text_lower for phrase in ResearchConfig.NEWCOMER_PHRASES)
    
    def scrape_subreddit(self, subreddit_name: str, limit: int = None) -> List[Dict]:
        """
        Scrape posts from a specific subreddit
        
        Args:
            subreddit_name: Name of subreddit to scrape
            limit: Maximum number of posts to collect
        
        Returns:
            List of post dictionaries with metadata
        """
        if limit is None:
            limit = Config.MAX_POSTS_PER_SUBREDDIT
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts_data = []
        
        logger.info(f"Scraping r/{subreddit_name} for health-related posts...")
        
        try:
            # Get recent posts (last 30 days worth)
            for post in subreddit.new(limit=limit * 3):  # Over-sample to filter down
                
                # Check if post contains health keywords
                post_text = f"{post.title} {post.selftext}"
                if not self.contains_health_keywords(post_text):
                    continue
                
                # Detect language
                language = self.detect_language(post_text)
                
                # Check for newcomer indicators
                is_newcomer = self.is_newcomer_related(post_text)
                
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
                
                # Collect comments for network analysis
                comments = self.extract_comments(post)
                post_data['comments'] = comments
                
                posts_data.append(post_data)
                
                # Respect rate limits
                time.sleep(0.1)
                
                if len(posts_data) >= limit:
                    break
            
            logger.info(f"Collected {len(posts_data)} relevant posts from r/{subreddit_name}")
            return posts_data
            
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {e}")
            return []
    
    def extract_comments(self, post) -> List[Dict]:
        """Extract comments from a post for network analysis"""
        comments_data = []
        
        try:
            post.comments.replace_more(limit=10)  # Load more comments
            
            for comment in post.comments.list():
                if hasattr(comment, 'body') and len(comment.body) >= Config.MIN_COMMENT_LENGTH:
                    
                    comment_data = {
                        'comment_id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'created_utc': datetime.fromtimestamp(comment.created_utc),
                        'score': comment.score,
                        'parent_id': comment.parent_id,
                        'language': self.detect_language(comment.body),
                        'is_newcomer_related': self.is_newcomer_related(comment.body)
                    }
                    
                    comments_data.append(comment_data)
        
        except Exception as e:
            logger.error(f"Error extracting comments: {e}")
        
        return comments_data
    
    def collect_all_data(self) -> pd.DataFrame:
        """Collect data from all target subreddits"""
        all_posts = []
        
        for subreddit in self.target_subreddits:
            posts = self.scrape_subreddit(subreddit)
            all_posts.extend(posts)
            
            # Be respectful with API calls
            time.sleep(2)
        
        df = pd.DataFrame(all_posts)
        
        # Save raw data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/raw_reddit_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(all_posts, f, indent=2, default=str)
        
        logger.info(f"Collected {len(all_posts)} total posts, saved to {filename}")
        return df

if __name__ == "__main__":
    scraper = RedditScraper()
    data = scraper.collect_all_data()
    print(f"Data collection complete: {len(data)} posts collected")
