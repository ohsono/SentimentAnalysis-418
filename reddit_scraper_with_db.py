#!/usr/bin/env python3

"""
Reddit Scraper Implementation with Database Storage
Enhanced version that properly stores data in PostgreSQL
"""

import os
import sys
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import re
import string
import asyncio

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_root, '.env'))
    print("✅ Environment variables loaded successfully")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import praw, but don't fail if not available
try:
    import praw
    from praw.models import Submission, Comment
    PRAW_AVAILABLE = True
    print("✅ PRAW library available")
except ImportError:
    logger.warning("PRAW not available. Using mock Reddit data.")
    PRAW_AVAILABLE = False
    print("❌ PRAW not available. Install with: pip install praw")

# Import database manager if available
try:
    from app.database.postgres_manager import DatabaseManager
    DATABASE_AVAILABLE = True
    print("✅ Database manager available")
except ImportError:
    logger.warning("Database manager not available. Results will not be stored in database.")
    DATABASE_AVAILABLE = False
    print("⚠️  Database manager not available")

# Import sentiment analyzer if available
try:
    from app.api.simple_sentiment_analyzer import SimpleSentimentAnalyzer
    sentiment_analyzer = SimpleSentimentAnalyzer()
    SENTIMENT_AVAILABLE = True
    print("✅ Sentiment analyzer available")
except ImportError:
    logger.warning("Sentiment analyzer not available. Will not analyze sentiment.")
    SENTIMENT_AVAILABLE = False
    sentiment_analyzer = None
    print("⚠️  Sentiment analyzer not available")

class RedditScraperWithDB:
    """Enhanced Reddit scraper with database storage"""
    
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        """Initialize Reddit scraper with database support"""
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "UCLA Sentiment Analysis Bot 1.0")
        
        # Debug: Print what we found
        print(f"🔍 Reddit Client ID: {'✅ Found' if self.client_id else '❌ Missing'}")
        print(f"🔍 Reddit Client Secret: {'✅ Found' if self.client_secret else '❌ Missing'}")
        print(f"🔍 User Agent: {self.user_agent}")
        
        # Set up Reddit client if credentials available
        self.reddit = None
        if PRAW_AVAILABLE and self.client_id and self.client_secret:
            try:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=self.user_agent
                )
                # Test the connection
                self.reddit.user.me()
                logger.info("✅ Reddit client initialized and authenticated successfully")
                print("✅ Reddit client connected successfully!")
            except Exception as e:
                logger.error(f"❌ Error initializing Reddit client: {e}")
                print(f"❌ Reddit connection failed: {e}")
                self.reddit = None
        else:
            if not PRAW_AVAILABLE:
                logger.warning("❌ Reddit client not initialized: PRAW library not available")
            elif not self.client_id or not self.client_secret:
                logger.warning("❌ Reddit client not initialized: Missing credentials")
                print("💡 To fix: Make sure REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET are set in .env file")
        
        # Set up database manager if available
        self.db_manager = None
        self.db_initialized = False
        if DATABASE_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                logger.info("✅ Database manager created")
                print("✅ Database manager ready")
            except Exception as e:
                logger.error(f"Error creating database manager: {e}")
                print(f"❌ Database manager creation failed: {e}")
    
    async def initialize_db(self):
        """Initialize database connection"""
        if self.db_manager and not self.db_initialized:
            try:
                success = await self.db_manager.initialize()
                if success:
                    self.db_initialized = True
                    logger.info("✅ Database connection initialized")
                    print("✅ Database connection ready!")
                    return True
                else:
                    logger.error("❌ Database initialization failed")
                    print("❌ Database initialization failed")
                    return False
            except Exception as e:
                logger.error(f"Error initializing database connection: {e}")
                print(f"❌ Database initialization error: {e}")
                return False
        return self.db_initialized
    
    async def scrape_subreddit_with_storage(self, subreddit_name: str, post_limit: int = 10, 
                                     comment_limit: int = 25, sort_by: str = "hot", 
                                     time_filter: str = "week", search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape Reddit posts and store them in database
        
        Args:
            subreddit_name: Name of subreddit to scrape
            post_limit: Maximum number of posts to retrieve
            comment_limit: Maximum number of comments to retrieve per post
            sort_by: Sort method ("hot", "new", "top", "rising")
            time_filter: Time filter for top posts ("hour", "day", "week", "month", "year", "all")
            search_query: Search query within subreddit
            
        Returns:
            Dictionary containing scraped data and stats
        """
        start_time = time.time()
        
        # Initialize database if available
        if self.db_manager:
            await self.initialize_db()
        
        if self.reddit:
            # Use real Reddit API
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"📡 Scraping r/{subreddit_name}...")
                
                # Get posts based on sort method
                if search_query:
                    logger.info(f"Searching r/{subreddit_name} for '{search_query}'")
                    posts_iterator = subreddit.search(search_query, sort=sort_by, time_filter=time_filter, limit=post_limit)
                elif sort_by == "hot":
                    posts_iterator = subreddit.hot(limit=post_limit)
                elif sort_by == "new":
                    posts_iterator = subreddit.new(limit=post_limit)
                elif sort_by == "top":
                    posts_iterator = subreddit.top(time_filter=time_filter, limit=post_limit)
                elif sort_by == "rising":
                    posts_iterator = subreddit.rising(limit=post_limit)
                else:
                    posts_iterator = subreddit.hot(limit=post_limit)
                
                # Fetch posts and comments
                posts = []
                comments = []
                stored_posts = 0
                stored_comments = 0
                stored_alerts = 0
                
                for submission in posts_iterator:
                    # Extract post data
                    post_data = await self._extract_post_data(submission)
                    posts.append(post_data)
                    
                    # Store in database if available
                    if self.db_initialized:
                        sentiment_id = None
                        
                        # Store sentiment analysis if available
                        if 'sentiment_analysis' in post_data:
                            sentiment_data = {
                                'text': f"{post_data['title']} {post_data['selftext']}",
                                'sentiment': post_data['sentiment_analysis']['sentiment'],
                                'confidence': post_data['sentiment_analysis']['confidence'],
                                'compound_score': post_data['sentiment_analysis']['compound_score'],
                                'processing_time_ms': post_data['sentiment_analysis'].get('processing_time_ms', 0),
                                'model_used': post_data['sentiment_analysis'].get('model_used', 'unknown'),
                                'source': post_data['sentiment_analysis'].get('source', 'api')
                            }
                            sentiment_id = await self.db_manager.store_sentiment_result(sentiment_data)
                        
                        # Store Reddit post
                        post_db_id = await self.db_manager.store_reddit_post(post_data, sentiment_id)
                        if post_db_id:
                            stored_posts += 1
                            print(f"  💾 Stored post: {post_data['title'][:50]}...")
                        
                        # Check for alerts
                        if 'sentiment_analysis' in post_data:
                            alert = self._check_for_alert(
                                post_data['post_id'], 
                                f"{post_data['title']} {post_data['selftext']}", 
                                post_data['sentiment_analysis'], 
                                'post',
                                post_data['subreddit'],
                                post_data['author']
                            )
                            if alert:
                                alert_id = await self.db_manager.store_sentiment_alert(alert, sentiment_id)
                                if alert_id:
                                    stored_alerts += 1
                                    print(f"  🚨 Alert created: {alert['alert_type']} - {alert['severity']}")
                    
                    # Get comments if needed
                    if comment_limit > 0:
                        submission.comments.replace_more(limit=0)
                        post_comments = []
                        
                        for comment in submission.comments[:comment_limit]:
                            try:
                                comment_data = await self._extract_comment_data(comment, submission.id)
                                post_comments.append(comment_data)
                                
                                # Store comment in database if available
                                if self.db_initialized:
                                    comment_sentiment_id = None
                                    
                                    # Store comment sentiment analysis if available
                                    if 'sentiment_analysis' in comment_data:
                                        comment_sentiment_data = {
                                            'text': comment_data['body'],
                                            'sentiment': comment_data['sentiment_analysis']['sentiment'],
                                            'confidence': comment_data['sentiment_analysis']['confidence'],
                                            'compound_score': comment_data['sentiment_analysis']['compound_score'],
                                            'processing_time_ms': comment_data['sentiment_analysis'].get('processing_time_ms', 0),
                                            'model_used': comment_data['sentiment_analysis'].get('model_used', 'unknown'),
                                            'source': comment_data['sentiment_analysis'].get('source', 'api')
                                        }
                                        comment_sentiment_id = await self.db_manager.store_sentiment_result(comment_sentiment_data)
                                    
                                    # Store comment
                                    comment_stored = await self._store_reddit_comment(comment_data, comment_sentiment_id)
                                    if comment_stored:
                                        stored_comments += 1
                                
                            except Exception as e:
                                logger.warning(f"Error processing comment: {e}")
                        
                        comments.extend(post_comments)
                
                result = {
                    "posts": posts[:5],  # Return sample for display
                    "comments": comments[:10],  # Return sample for display
                    "stats": {
                        "posts_collected": len(posts),
                        "comments_collected": len(comments),
                        "stored_in_database": {
                            "posts": stored_posts,
                            "comments": stored_comments,
                            "alerts": stored_alerts
                        },
                        "database_enabled": self.db_initialized,
                        "sentiment_summary": self._calculate_sentiment_stats(posts)
                    },
                    "subreddit": subreddit_name,
                    "data_source": "reddit_api",
                    "scrape_time_ms": round((time.time() - start_time) * 1000, 2),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                return result
                
            except Exception as e:
                logger.error(f"Error scraping Reddit: {e}")
                print(f"❌ Scraping failed: {e}")
                # Fall back to mock data
                logger.info("Falling back to mock data")
                return await self._generate_mock_data(subreddit_name, post_limit, comment_limit)
        else:
            # Use mock data
            logger.info("Using mock data (Reddit client not available)")
            return await self._generate_mock_data(subreddit_name, post_limit, comment_limit)
    
    async def _store_reddit_comment(self, comment_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> bool:
        """Store Reddit comment in database"""
        try:
            if not self.db_initialized:
                return False
            
            async with self.db_manager.connection_pool.acquire() as conn:
                # Check if comment already exists
                existing = await conn.fetchval(
                    "SELECT id FROM reddit_comments WHERE comment_id = $1",
                    comment_data['comment_id']
                )
                
                if existing:
                    return True
                
                # Insert new comment
                comment_id = await conn.fetchval("""
                    INSERT INTO reddit_comments 
                    (comment_id, post_id, body, author, score, created_utc, sentiment_analysis_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """,
                    comment_data['comment_id'],
                    comment_data['post_id'],
                    comment_data['body'],
                    comment_data.get('author'),
                    comment_data.get('score'),
                    datetime.fromisoformat(comment_data['created_utc'].replace('Z', '+00:00')),
                    sentiment_id
                )
                
                return comment_id is not None
                
        except Exception as e:
            logger.error(f"Failed to store Reddit comment: {e}")
            return False
    
    async def _extract_post_data(self, submission) -> Dict[str, Any]:
        """Extract and clean data from a Reddit post"""
        post_data = {
            'post_id': submission.id,
            'title': submission.title,
            'selftext': submission.selftext,
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'created_utc': datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
            'author': str(submission.author) if submission.author else '[deleted]',
            'subreddit': submission.subreddit.display_name,
            'permalink': submission.permalink,
            'url': submission.url
        }
        
        # Clean the data
        clean_post = await self._clean_post_data(post_data)
        
        # Analyze sentiment if available
        if SENTIMENT_AVAILABLE:
            text_to_analyze = f"{clean_post['title']} {clean_post['selftext']}"
            clean_post['sentiment_analysis'] = sentiment_analyzer.analyze(text_to_analyze)
        
        return clean_post
    
    async def _extract_comment_data(self, comment, post_id: str) -> Dict[str, Any]:
        """Extract and clean data from a Reddit comment"""
        comment_data = {
            'comment_id': comment.id,
            'post_id': post_id,
            'body': comment.body,
            'score': comment.score,
            'created_utc': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).isoformat(),
            'author': str(comment.author) if comment.author else '[deleted]',
            'permalink': comment.permalink
        }
        
        # Clean the data
        clean_comment = await self._clean_comment_data(comment_data)
        
        # Analyze sentiment if available
        if SENTIMENT_AVAILABLE:
            clean_comment['sentiment_analysis'] = sentiment_analyzer.analyze(clean_comment['body'])
        
        return clean_comment
    
    async def _clean_post_data(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean post data"""
        clean_post = post_data.copy()
        clean_post['title'] = self._clean_text(clean_post['title'])
        clean_post['selftext'] = self._clean_text(clean_post['selftext'])
        clean_post['author'] = self._clean_text(clean_post['author'])
        return clean_post
    
    async def _clean_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean comment data"""
        clean_comment = comment_data.copy()
        clean_comment['body'] = self._clean_text(clean_comment['body'])
        clean_comment['author'] = self._clean_text(clean_comment['author'])
        return clean_comment
    
    def _clean_text(self, text: str) -> str:
        """Clean text by removing special characters, excessive whitespace, etc."""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        # Replace newlines with spaces
        text = text.replace('\n', ' ')
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove non-printable characters
        text = ''.join(c for c in text if c in string.printable)
        
        return text
    
    def _check_for_alert(self, content_id: str, content_text: str, sentiment_result: Dict[str, Any], 
                       content_type: str, subreddit: str, author: str) -> Optional[Dict[str, Any]]:
        """Check if content should trigger an alert"""
        alert_keywords = {
            'mental_health': ['depressed', 'depression', 'suicide', 'kill myself', 'end it all', 'worthless'],
            'stress': ['overwhelmed', 'stressed', 'anxious', 'panic', 'breakdown', 'can\'t handle'],
            'academic': ['failing', 'dropped out', 'academic probation', 'expelled'],
            'harassment': ['bullied', 'harassed', 'threatened', 'stalked']
        }
        
        content_text_lower = content_text.lower()
        
        for alert_type, keywords in alert_keywords.items():
            found_keywords = [kw for kw in keywords if kw in content_text_lower]
            if found_keywords:
                if sentiment_result['compound_score'] < -0.5:
                    severity = 'high'
                elif sentiment_result['compound_score'] < -0.2:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                if alert_type == 'mental_health':
                    severity = 'high' if severity != 'low' else 'medium'
                
                return {
                    'content_id': content_id,
                    'content_text': content_text,
                    'content_type': content_type,
                    'alert_type': alert_type,
                    'severity': severity,
                    'keywords_found': found_keywords,
                    'subreddit': subreddit,
                    'author': author,
                    'confidence': sentiment_result['confidence'],
                    'compound_score': sentiment_result['compound_score'],
                    'status': 'active'
                }
        
        return None
    
    def _calculate_sentiment_stats(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment statistics from posts"""
        if not posts or not SENTIMENT_AVAILABLE:
            return {}
        
        sentiments = []
        compound_scores = []
        
        for post in posts:
            if 'sentiment_analysis' in post:
                sentiments.append(post['sentiment_analysis']['sentiment'])
                compound_scores.append(post['sentiment_analysis']['compound_score'])
        
        if not sentiments:
            return {}
        
        positive_count = sentiments.count('positive')
        negative_count = sentiments.count('negative')
        neutral_count = sentiments.count('neutral')
        total_count = len(sentiments)
        
        avg_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0
        
        return {
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "positive_percent": round(positive_count / total_count * 100, 1) if total_count > 0 else 0,
            "negative_percent": round(negative_count / total_count * 100, 1) if total_count > 0 else 0,
            "neutral_percent": round(neutral_count / total_count * 100, 1) if total_count > 0 else 0,
            "average_compound_score": round(avg_compound, 3)
        }
    
    async def _generate_mock_data(self, subreddit_name: str, post_limit: int, 
                           comment_limit: int) -> Dict[str, Any]:
        """Generate mock Reddit data for testing when API not available"""
        return {
            "posts": [],
            "comments": [],
            "stats": {
                "posts_collected": 0,
                "comments_collected": 0,
                "stored_in_database": {"posts": 0, "comments": 0, "alerts": 0},
                "database_enabled": False
            },
            "data_source": "mock_data",
            "subreddit": subreddit_name
        }

# For direct testing
if __name__ == "__main__":
    print("🚀 Starting Enhanced Reddit Scraper with Database Storage...")
    print("=" * 60)
    
    async def test_enhanced_scraper():
        scraper = RedditScraperWithDB()
        
        # Test with database storage
        results = await scraper.scrape_subreddit_with_storage("UCLA", 3, 5)
        
        print("\n📊 SCRAPING RESULTS:")
        print("=" * 40)
        print(f"Posts collected: {results['stats']['posts_collected']}")
        print(f"Comments collected: {results['stats']['comments_collected']}")
        print(f"Database enabled: {results['stats']['database_enabled']}")
        print(f"Posts stored in DB: {results['stats']['stored_in_database']['posts']}")
        print(f"Comments stored in DB: {results['stats']['stored_in_database']['comments']}")
        print(f"Alerts created: {results['stats']['stored_in_database']['alerts']}")
        print(f"Data source: {results['data_source']}")
        
        if results['stats']['database_enabled']:
            print("\n🎉 SUCCESS! Reddit data is being stored in the database!")
        else:
            print("\n⚠️  Database not available - data not stored")
    
    asyncio.run(test_enhanced_scraper())
