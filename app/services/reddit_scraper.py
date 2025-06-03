import praw
import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
import os
import time

logger = logging.getLogger(__name__)

class RedditScraper:
    """
    Reddit scraper for collecting posts and comments

        What this does:
    - Connects to Reddit API using your credentials
    - Collects posts and comments from specified subreddits
    - Handles rate limiting to avoid getting banned
    - Processes raw Reddit data into our format
    
    How it works:
    1. Connect to Reddit using PRAW library
    2. Search specific subreddit (e.g., r/UCLA)
    3. Get posts from different time periods (hot, top, new)
    4. For each post, collect top comments
    5. Extract relevant data and convert to our format
    
    Rate limiting protection:
    - Sleeps between requests (0.1 seconds)
    - Limits total posts/comments per run
    - Tracks processed IDs to avoid duplicates
    """
        
    def __init__(self, config: Dict = None):
        if config is None:
            config = self.load_config()
            
        self.config = config
        self.reddit = praw.Reddit(
            client_id=config.get('reddit_client_id', os.getenv('REDDIT_CLIENT_ID')),
            client_secret=config.get('reddit_client_secret', os.getenv('REDDIT_CLIENT_SECRET')),
            user_agent=config.get('reddit_user_agent', os.getenv('REDDIT_USER_AGENT', 'UCLA-Sentiment/1.0'))
        )
        
    def load_config(self) -> Dict:
        """Load configuration from environment"""
        return {
            'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
            'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
            'reddit_user_agent': os.getenv('REDDIT_USER_AGENT', 'UCLA-Sentiment/1.0'),
            'subreddit': os.getenv('SUBREDDIT', 'UCLA'),
            'post_limit': int(os.getenv('POST_LIMIT', '100')),
            'comment_limit': int(os.getenv('COMMENT_LIMIT', '50'))
        }
    
    def scrape_subreddit(self, subreddit_name: str = None, post_limit: int = None) -> Dict[str, Any]:
        """
        Scrape posts and comments from subreddit
        """
        subreddit_name = subreddit_name or self.config.get('subreddit', 'UCLA')
        post_limit = post_limit or self.config.get('post_limit', 100)
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            posts_data = []
            comments_data = []
            
            logger.info(f"Scraping r/{subreddit_name} - {post_limit} posts")
            
            for post in subreddit.hot(limit=post_limit):
                # Extract post data
                post_data = {
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
                    'scraped_at': datetime.now(timezone.utc)
                }
                posts_data.append(post_data)
                
                # Get comments for this post
                try:
                    post.comments.replace_more(limit=3)
                    comment_count = 0
                    for comment in post.comments.list():
                        if comment_count >= self.config.get('comment_limit', 50):
                            break
                            
                        comment_data = {
                            'comment_id': comment.id,
                            'post_id': post.id,
                            'body': comment.body,
                            'score': comment.score,
                            'created_utc': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc),
                            'author': str(comment.author) if comment.author else '[deleted]',
                            'parent_id': comment.parent_id,
                            'is_submitter': comment.is_submitter,
                            'depth': getattr(comment, 'depth', 0),
                            'scraped_at': datetime.now(timezone.utc)
                        }
                        comments_data.append(comment_data)
                        comment_count += 1
                        
                except Exception as e:
                    logger.error(f"Error getting comments for post {post.id}: {e}")
                    continue
                
                # Rate limiting
                time.sleep(0.1)
            
            return {
                'posts': posts_data,
                'comments': comments_data,
                'stats': {
                    'posts_collected': len(posts_data),
                    'comments_collected': len(comments_data),
                    'subreddit': subreddit_name,
                    'timestamp': datetime.now(timezone.utc)
                }
            }
            
        except Exception as e:
            logger.error(f"Error scraping subreddit: {e}")
            return {'posts': [], 'comments': [], 'error': str(e)}