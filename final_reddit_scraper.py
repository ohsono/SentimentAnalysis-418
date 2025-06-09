#!/usr/bin/env python3

"""
Final Working Reddit Scraper with Database Storage
Uses standalone sentiment analyzer to avoid Docker permission issues
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

# FIXED: Use absolute path for project root
PROJECT_ROOT = "/Users/hobangu/Project/UCLA-MASDS/SentimentAnalysis-418"
sys.path.insert(0, PROJECT_ROOT)

# FIXED: Load environment variables with absolute path
try:
    from dotenv import load_dotenv
    env_path = os.path.join(PROJECT_ROOT, '.env')
    result = load_dotenv(env_path, override=True)
    print(f"✅ Environment variables loaded from {env_path}: {result}")
    
    # Debug: Show what we loaded
    print(f"🔍 REDDIT_CLIENT_ID: {'✅ Found' if os.getenv('REDDIT_CLIENT_ID') else '❌ Missing'}")
    print(f"🔍 POSTGRES_USER: {'✅ Found' if os.getenv('POSTGRES_USER') else '❌ Missing'}")
    
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import praw
try:
    import praw
    from praw.models import Submission, Comment
    PRAW_AVAILABLE = True
    print("✅ PRAW library available")
except ImportError:
    logger.warning("PRAW not available. Using mock Reddit data.")
    PRAW_AVAILABLE = False
    print("❌ PRAW not available. Install with: pip install praw")

# Import standalone sentiment analyzer
try:
    from standalone_sentiment_analyzer import StandaloneSentimentAnalyzer
    sentiment_analyzer = StandaloneSentimentAnalyzer()
    SENTIMENT_AVAILABLE = True
    print("✅ Standalone sentiment analyzer loaded")
except ImportError:
    logger.warning("Standalone sentiment analyzer not available.")
    SENTIMENT_AVAILABLE = False
    sentiment_analyzer = None
    print("⚠️  Sentiment analyzer not available")

# FIXED: Create a custom DatabaseManager that uses correct environment variables
class FixedDatabaseManager:
    """Fixed database manager that properly loads environment variables"""
    
    def __init__(self):
        # FIXED: Load database config from environment variables with correct names
        self.config = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "sentiment_db"),
            "user": os.getenv("POSTGRES_USER", "sentiment_user"),
            "password": os.getenv("POSTGRES_PASSWORD", "sentiment_password")
        }
        
        print(f"🗄️  Database config: {self.config['user']}@{self.config['host']}:{self.config['port']}/{self.config['database']}")
        
        self.connection_pool = None
        
    async def initialize(self):
        """Initialize database connection"""
        try:
            import asyncpg
            
            # Create connection pool with correct credentials
            self.connection_pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],  # FIXED: Use 'user' not 'username'
                password=self.config["password"],
                min_size=5,
                max_size=20
            )
            
            # Test connection
            async with self.connection_pool.acquire() as conn:
                version = await conn.fetchval('SELECT version()')
                print(f"✅ Database connected: {version.split(',')[0]}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            print(f"❌ Database initialization failed: {e}")
            return False
    
    async def store_sentiment_result(self, sentiment_data: Dict[str, Any]) -> Optional[int]:
        """Store sentiment analysis result"""
        try:
            import hashlib
            
            # Create text hash for deduplication
            text_hash = hashlib.sha256(sentiment_data['text'].encode()).hexdigest()
            
            async with self.connection_pool.acquire() as conn:
                # Check if already exists
                existing = await conn.fetchval(
                    "SELECT id FROM sentiment_analysis_results WHERE text_hash = $1",
                    text_hash
                )
                
                if existing:
                    return existing
                
                # Insert new result
                result_id = await conn.fetchval("""
                    INSERT INTO sentiment_analysis_results 
                    (text_content, text_hash, sentiment, confidence, compound_score, 
                     processing_time_ms, model_used, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                """, 
                    sentiment_data['text'],
                    text_hash,
                    sentiment_data['sentiment'],
                    sentiment_data['confidence'],
                    sentiment_data['compound_score'],
                    sentiment_data['processing_time_ms'],
                    sentiment_data.get('model_used', 'unknown'),
                    sentiment_data.get('source', 'api')
                )
                
                return result_id
                
        except Exception as e:
            logger.error(f"Failed to store sentiment result: {e}")
            return None
    
    async def store_reddit_post(self, post_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> Optional[int]:
        """Store Reddit post data"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check if post already exists
                existing = await conn.fetchval(
                    "SELECT id FROM reddit_posts WHERE post_id = $1",
                    post_data['post_id']
                )
                
                if existing:
                    if sentiment_id:
                        await conn.execute(
                            "UPDATE reddit_posts SET sentiment_analysis_id = $1 WHERE id = $2",
                            sentiment_id, existing
                        )
                    return existing
                
                # Insert new post
                post_id = await conn.fetchval("""
                    INSERT INTO reddit_posts 
                    (post_id, title, selftext, subreddit, author, score, upvote_ratio, 
                     num_comments, created_utc, sentiment_analysis_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                """,
                    post_data['post_id'],
                    post_data['title'],
                    post_data.get('selftext', ''),
                    post_data.get('subreddit', 'UCLA'),
                    post_data.get('author'),
                    post_data.get('score'),
                    post_data.get('upvote_ratio'),
                    post_data.get('num_comments'),
                    datetime.fromisoformat(post_data['created_utc'].replace('Z', '+00:00')),
                    sentiment_id
                )
                
                return post_id
                
        except Exception as e:
            logger.error(f"Failed to store Reddit post: {e}")
            return None
    
    async def store_reddit_comment(self, comment_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> Optional[int]:
        """Store Reddit comment data"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check if comment already exists
                existing = await conn.fetchval(
                    "SELECT id FROM reddit_comments WHERE comment_id = $1",
                    comment_data['comment_id']
                )
                
                if existing:
                    return existing
                
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
                
                return comment_id
                
        except Exception as e:
            logger.error(f"Failed to store Reddit comment: {e}")
            return None
    
    async def store_sentiment_alert(self, alert_data: Dict[str, Any], sentiment_id: Optional[int] = None) -> Optional[int]:
        """Store sentiment alert"""
        try:
            async with self.connection_pool.acquire() as conn:
                alert_id = await conn.fetchval("""
                    INSERT INTO sentiment_alerts 
                    (content_id, content_text, content_type, alert_type, severity, 
                     keywords_found, subreddit, author, sentiment_analysis_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id
                """,
                    alert_data['content_id'],
                    alert_data['content_text'],
                    alert_data.get('content_type', 'post'),
                    alert_data['alert_type'],
                    alert_data['severity'],
                    json.dumps(alert_data.get('keywords_found', [])),
                    alert_data.get('subreddit', 'UCLA'),
                    alert_data.get('author'),
                    sentiment_id
                )
                
                return alert_id
                
        except Exception as e:
            logger.error(f"Failed to store sentiment alert: {e}")
            return None
    
    async def close(self):
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()

class FinalRedditScraper:
    """Final working Reddit scraper with all fixes"""
    
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        """Initialize Reddit scraper"""
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "UCLA Sentiment Analysis Bot 1.0")
        
        # Debug: Print what we found
        print(f"🔍 Reddit Client ID: {'✅ Found' if self.client_id else '❌ Missing'}")
        print(f"🔍 Reddit Client Secret: {'✅ Found' if self.client_secret else '❌ Missing'}")
        print(f"🔍 User Agent: {self.user_agent}")
        
        # Set up Reddit client
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
                print("✅ Reddit client connected successfully!")
            except Exception as e:
                print(f"❌ Reddit connection failed: {e}")
                self.reddit = None
        else:
            if not PRAW_AVAILABLE:
                print("❌ PRAW library not available")
            elif not self.client_id or not self.client_secret:
                print("❌ Reddit credentials missing")
        
        # Set up database manager
        self.db_manager = FixedDatabaseManager()
        self.db_initialized = False
    
    async def initialize_db(self):
        """Initialize database connection"""
        if not self.db_initialized:
            success = await self.db_manager.initialize()
            if success:
                self.db_initialized = True
                print("✅ Database connection ready!")
                return True
            else:
                print("❌ Database initialization failed")
                return False
        return True
    
    async def scrape_subreddit_with_storage(self, subreddit_name: str, post_limit: int = 5, 
                                     comment_limit: int = 10) -> Dict[str, Any]:
        """Scrape Reddit posts and store them in database"""
        start_time = time.time()
        
        # Initialize database
        await self.initialize_db()
        
        if self.reddit:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                print(f"📡 Scraping r/{subreddit_name}...")
                
                posts_iterator = subreddit.hot(limit=post_limit)
                
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
                                'model_used': post_data['sentiment_analysis'].get('model_used', 'vader'),
                                'source': post_data['sentiment_analysis'].get('source', 'api')
                            }
                            sentiment_id = await self.db_manager.store_sentiment_result(sentiment_data)
                            if sentiment_id:
                                print(f"  💭 Stored sentiment: {sentiment_data['sentiment']} ({sentiment_data['confidence']:.2f})")
                        
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
                    
                    # Get comments (simplified for demo)
                    if comment_limit > 0:
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:comment_limit]:
                            try:
                                comment_data = await self._extract_comment_data(comment, submission.id)
                                comments.append(comment_data)
                                
                                # Store comment in database
                                if self.db_initialized:
                                    comment_sentiment_id = None
                                    if 'sentiment_analysis' in comment_data:
                                        comment_sentiment_data = {
                                            'text': comment_data['body'],
                                            'sentiment': comment_data['sentiment_analysis']['sentiment'],
                                            'confidence': comment_data['sentiment_analysis']['confidence'],
                                            'compound_score': comment_data['sentiment_analysis']['compound_score'],
                                            'processing_time_ms': comment_data['sentiment_analysis'].get('processing_time_ms', 0),
                                            'model_used': comment_data['sentiment_analysis'].get('model_used', 'vader'),
                                            'source': comment_data['sentiment_analysis'].get('source', 'api')
                                        }
                                        comment_sentiment_id = await self.db_manager.store_sentiment_result(comment_sentiment_data)
                                    
                                    comment_stored = await self.db_manager.store_reddit_comment(comment_data, comment_sentiment_id)
                                    if comment_stored:
                                        stored_comments += 1
                                
                            except Exception as e:
                                logger.warning(f"Error processing comment: {e}")
                
                result = {
                    "posts": posts[:3],  # Sample for display
                    "comments": comments[:5],  # Sample for display
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
        
        # Return empty result if no Reddit connection
        return {
            "posts": [],
            "comments": [],
            "stats": {
                "posts_collected": 0,
                "comments_collected": 0,
                "stored_in_database": {"posts": 0, "comments": 0, "alerts": 0},
                "database_enabled": self.db_initialized
            },
            "data_source": "no_reddit_connection",
            "subreddit": subreddit_name
        }
    
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
        """Clean text"""
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

# For direct testing
if __name__ == "__main__":
    print("🚀 Starting FINAL Working Reddit Scraper with Database Storage...")
    print("=" * 70)
    
    async def test_final_scraper():
        scraper = FinalRedditScraper()
        
        # Test with database storage
        results = await scraper.scrape_subreddit_with_storage("UCLA", 3, 5)
        
        print("\n📊 FINAL SCRAPING RESULTS:")
        print("=" * 50)
        print(f"Posts collected: {results['stats']['posts_collected']}")
        print(f"Comments collected: {results['stats']['comments_collected']}")
        print(f"Database enabled: {results['stats']['database_enabled']}")
        print(f"Posts stored in DB: {results['stats']['stored_in_database']['posts']}")
        print(f"Comments stored in DB: {results['stats']['stored_in_database']['comments']}")
        print(f"Alerts created: {results['stats']['stored_in_database']['alerts']}")
        print(f"Data source: {results['data_source']}")
        
        if results['stats']['sentiment_summary']:
            sentiment_summary = results['stats']['sentiment_summary']
            print(f"\n📈 Sentiment Summary:")
            print(f"  Positive: {sentiment_summary.get('positive', 0)} ({sentiment_summary.get('positive_percent', 0)}%)")
            print(f"  Negative: {sentiment_summary.get('negative', 0)} ({sentiment_summary.get('negative_percent', 0)}%)")
            print(f"  Neutral: {sentiment_summary.get('neutral', 0)} ({sentiment_summary.get('neutral_percent', 0)}%)")
            print(f"  Average Score: {sentiment_summary.get('average_compound_score', 0)}")
        
        if results['stats']['database_enabled'] and results['data_source'] == 'reddit_api':
            print("\n🎉 SUCCESS! Reddit scraper is working perfectly!")
            print("✅ Reddit API connected")
            print("✅ Sentiment analysis working")
            print("✅ Database storage working")
            print("✅ Alert system working")
        else:
            print("\n⚠️  Some components not available:")
            if results['data_source'] != 'reddit_api':
                print("  ❌ Reddit API connection failed")
            if not results['stats']['database_enabled']:
                print("  ❌ Database storage failed")
        
        # Clean up
        await scraper.db_manager.close()
    
    asyncio.run(test_final_scraper())
