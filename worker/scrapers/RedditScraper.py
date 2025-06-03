#!/usr/bin/env python3
"""
Reddit Scraper for UCLA Sentiment Analysis Pipeline
Scrapes posts and comments from target subreddits, focusing on UCLA-related content
"""

import os
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
import argparse

import praw
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from praw.models import MoreComments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditScraper:
    """Reddit scraper for collecting posts and comments from specified subreddits"""
    
    def __init__(self, config: Dict):
        """Initialize the scraper with configuration"""
        self.config = config
        self.subreddit_name = config['subreddit']
        
        # Ensure data_dir is a Path object and is absolute
        data_dir = config.get('data_dir', 'Data')
        if not isinstance(data_dir, Path):
            data_dir = Path(data_dir)
        if not data_dir.is_absolute():
            # Make relative to current working directory
            data_dir = Path.cwd() / data_dir
            
        self.data_dir = data_dir
        self.post_limit = config.get('post_limit', 1000)
        self.comment_limit = config.get('comment_limit', 100)
        
        # Initialize Reddit API client
        self.reddit = praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent=config['user_agent']
        )
        
        # Create directory structure
        self.posts_dir = self.data_dir / 'posts'
        self.comments_dir = self.data_dir / 'comments'
        self.metadata_dir = self.data_dir / 'metadata'
        
        for dir_path in [self.posts_dir, self.comments_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load processed post IDs to avoid duplicates
        self.processed_ids_file = self.metadata_dir / f'{self.subreddit_name}_processed.json'
        self.processed_ids = self._load_processed_ids()
        
        logger.info(f"Initialized scraper for r/{self.subreddit_name}")
        logger.info(f"Data directory: {self.data_dir}")
        logger.info(f"Previously processed: {len(self.processed_ids)} posts")
    
    def _load_processed_ids(self) -> Set[str]:
        """Load previously processed post IDs"""
        if self.processed_ids_file.exists():
            try:
                with open(self.processed_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_ids', []))
            except Exception as e:
                logger.error(f"Error loading processed IDs: {e}")
        return set()
    
    def _save_processed_ids(self):
        """Save processed post IDs to file"""
        try:
            data = {
                'processed_ids': list(self.processed_ids),
                'last_updated': datetime.now(timezone.utc).isoformat(),
                'subreddit': self.subreddit_name,
                'total_processed': len(self.processed_ids)
            }
            with open(self.processed_ids_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed IDs: {e}")
    
    def extract_post_data(self, post) -> Dict:
        """Extract data from a Reddit post"""
        try:
            return {
                'post_id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'score': post.score,
                'upvote_ratio': post.upvote_ratio,
                'num_comments': post.num_comments,
                'created_utc': datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                'author': str(post.author) if post.author else '[deleted]',
                'subreddit': post.subreddit.display_name,
                'permalink': post.permalink,
                'url': post.url,
                'is_self': post.is_self,
                'is_original_content': post.is_original_content,
                'over_18': post.over_18,
                'spoiler': post.spoiler,
                'stickied': post.stickied,
                'locked': post.locked,
                'scraped_at': datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Error extracting post data for {post.id}: {e}")
            return None
    
    def extract_comment_data(self, comment, post_id: str) -> Dict:
        """Extract data from a Reddit comment"""
        try:
            return {
                'comment_id': comment.id,
                'post_id': post_id,
                'body': comment.body,
                'score': comment.score,
                'created_utc': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                'author': str(comment.author) if comment.author else '[deleted]',
                'parent_id': comment.parent_id,
                'is_submitter': comment.is_submitter,
                'stickied': comment.stickied,
                'depth': comment.depth if hasattr(comment, 'depth') else 0,
                'scraped_at': datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"Error extracting comment data for {comment.id}: {e}")
            return None
    
    def collect_comments(self, post) -> List[Dict]:
        """Collect comments from a post"""
        comments_data = []
        
        try:
            # Replace MoreComments with actual comments (limited to avoid API overuse)
            post.comments.replace_more(limit=5)
            
            def process_comment_tree(comments, max_depth=3, current_depth=0):
                if current_depth > max_depth or len(comments_data) >= self.comment_limit:
                    return
                
                for comment in comments:
                    if len(comments_data) >= self.comment_limit:
                        break
                    
                    if isinstance(comment, MoreComments):
                        continue
                    
                    comment_data = self.extract_comment_data(comment, post.id)
                    if comment_data:
                        comment_data['depth'] = current_depth
                        comments_data.append(comment_data)
                    
                    # Process replies recursively
                    if comment.replies and current_depth < max_depth:
                        process_comment_tree(comment.replies, max_depth, current_depth + 1)
            
            process_comment_tree(post.comments)
            
        except Exception as e:
            logger.error(f"Error collecting comments for post {post.id}: {e}")
        
        return comments_data
    
    def scrape_subreddit(self) -> Dict:
        """Scrape posts from the target subreddit"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        stats = {
                'total_posts_found': 0,
                'new_posts_processed': 0,
                'total_comments_collected': 0,
                'start_time': datetime.now(timezone.utc),
                'subreddit': self.subreddit_name
        }
        
        posts_data = []
        comments_data = []
        
        try:
            subreddit = self.reddit.subreddit(self.subreddit_name)
            logger.info(f"Starting to scrape r/{self.subreddit_name}")
            
            # Get posts from different time periods
            time_filters = ['day', 'week', 'month']
            posts_seen = set()
            
            # Get posts for each time filter
            all_posts = []
            for time_filter in time_filters:
                post_limit = self.post_limit // len(time_filters)
                # Ensure we use an integer value for limit
                posts = subreddit.top(
                    time_filter=time_filter, 
                    limit=int(post_limit)
                )
                all_posts.extend(posts)
            
            for post in all_posts:
                stats['total_posts_found'] += 1
                    
                # Skip if already processed
                if post.id in posts_seen or post.id in self.processed_ids:
                    continue
                    
                # Extract post data
                post_data = self.extract_post_data(post)
                if not post_data:
                    continue
                
                # Collect comments without filtering
                post_comments = self.collect_comments(post)
                
                # Add all data without filtering
                posts_data.append(post_data)
                comments_data.extend(post_comments)
                
                # Update stats
                stats['new_posts_processed'] += 1
                stats['total_comments_collected'] += len(post_comments)
                self.processed_ids.add(post.id)
                
                # Log progress
                if stats['new_posts_processed'] % 50 == 0:
                    logger.info(f"Processed {stats['new_posts_processed']} posts, "
                                f"collected {stats['total_comments_collected']} comments")
                        
            # Brief pause between time filters
            time.sleep(1)
            
            # Save data if we collected anything
            if posts_data:
                self._save_data(posts_data, comments_data, timestamp)
                self._save_processed_ids()
                
            stats['end_time'] = datetime.now(timezone.utc)
            print(f"Duration: {stats['end_time'] - stats['start_time']}")
            stats['duration_minutes'] = (stats['end_time'] - stats['start_time']).total_seconds() / 60
            
            logger.info(f"Scraping completed. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in scrape_subreddit: {e}")
            return stats
    
    def _save_data(self, posts_data: List[Dict], comments_data: List[Dict], timestamp: str):
        """Save collected data to parquet files"""
        try:
            # Save posts
            if posts_data:
                posts_df = pd.DataFrame(posts_data)
                posts_file = self.posts_dir / f'{self.subreddit_name}_{timestamp}.parquet'
                posts_df.to_parquet(posts_file, compression='snappy', index=False)
                logger.info(f"Saved {len(posts_data)} posts to {posts_file}")
            
            # Save comments
            if comments_data:
                comments_df = pd.DataFrame(comments_data)
                comments_file = self.comments_dir / f'{self.subreddit_name}_{timestamp}.parquet'
                comments_df.to_parquet(comments_file, compression='snappy', index=False)
                logger.info(f"Saved {len(comments_data)} comments to {comments_file}")
            
        except Exception as e:
            logger.error(f"Error saving data: {e}")

def load_config() -> Dict:
    """Load configuration from environment variables or file"""
    config = {
        'client_id': os.getenv('REDDIT_CLIENT_ID'),
        'client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
        'user_agent': os.getenv('REDDIT_USER_AGENT'),
        'subreddit': os.getenv('SUBREDDIT', 'UCLA'),
        'data_dir': os.getenv('DATA_DIR', 'Data'),  # Default to 'Data' directory in current directory
        'post_limit': int(os.getenv('POST_LIMIT', '1000')),
        'comment_limit': int(os.getenv('COMMENT_LIMIT', '100'))
    }
    
    # Check for required fields
    required_fields = ['client_id', 'client_secret', 'user_agent']
    missing_fields = [field for field in required_fields if not config[field]]
    
    if missing_fields:
        raise ValueError(f"Missing required configuration: {missing_fields}")
    
    return config

# def main():
#     """Main function"""
#     parser = argparse.ArgumentParser(description='Reddit Scraper for UCLA Sentiment Analysis')
#     parser.add_argument('-sr','--subreddit',action='store',dest='subreddit', type=str, help='Subreddit to scrape')
#     parser.add_argument('-dd','--data-dir',action='store',dest='data-dir', type=str, help='Data directory path')
#     parser.add_argument('-pl','--post-limit',action='store',dest='post-limit', type=int, help='Maximum posts to collect')
#     parser.add_argument('-cl','--comment-limit',action='store',dest='comment-limit', type=int, help='Maximum comments per post')
#     parser.add_argument('-fl','--keyword-filter',action='store',dest='keyword-filter', type=str, help='Keyword filter for context')
    
#     args = parser.parse_args()
    
#     try:
#         # Load configuration
#         config = load_config()
        
#         # Override with command line arguments if provided
#         if args.subreddit:
#             config['subreddit'] = args.subreddit
#         if args.data_dir:
#             config['data_dir'] = args.data_dir
#         if args.post_limit:
#             config['post_limit'] = args.post_limit
#         if args.comment_limit:
#             config['comment_limit'] = args.comment_limit
#         if args.keyword_filter:
#             config['keyword_filter'] = args.keyword_filter
        
#         # Initialize and run scraper
#         scraper = RedditScraper(config)
#         stats = scraper.scrape_subreddit()
        
#         # Log final statistics
#         logger.info("="*50)
#         logger.info("SCRAPING COMPLETED")
#         logger.info(f"Subreddit: {stats['subreddit']}")
#         logger.info(f"New posts processed: {stats['new_posts_processed']}")
#         logger.info(f"Total comments collected: {stats['total_comments_collected']}")
#         logger.info(f"Duration: {stats.get('duration_minutes', 0):.2f} minutes")
#         logger.info("="*50)
        
#     except Exception as e:
#         logger.error(f"Error in main: {e}")
#         raise

# if __name__ == '__main__':
#     main()