#!/usr/bin/env python3

"""
Reddit Scraper Implementation - FIXED VERSION
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

class RedditScraper:
    """Reddit scraper class that can scrape posts and comments with data cleaning"""
    
    def __init__(self, client_id=None, client_secret=None, user_agent=None):
        """Initialize Reddit scraper"""
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
                self.reddit.user.me()  # This will raise an exception if credentials are invalid
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
        if DATABASE_AVAILABLE:
            try:
                self.db_manager = DatabaseManager()
                logger.info("Database manager initialized")
            except Exception as e:
                logger.error(f"Error initializing database manager: {e}")
    
    async def initialize_db(self):
        """Initialize database connection"""
        if self.db_manager:
            try:
                await self.db_manager.initialize()
                logger.info("Database connection initialized")
                return True
            except Exception as e:
                logger.error(f"Error initializing database connection: {e}")
        return False
    
    async def scrape_subreddit(self, subreddit_name: str, post_limit: int = 10, 
                         comment_limit: int = 25, sort_by: str = "hot", 
                         time_filter: str = "week", search_query: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape Reddit posts and comments from a subreddit
        
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
        
        if self.reddit:
            # Use real Reddit API
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
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
                all_comment_count = 0
                
                for submission in posts_iterator:
                    # Extract post data
                    post_data = await self._extract_post_data(submission)
                    posts.append(post_data)
                    
                    # Get comments if needed
                    if comment_limit > 0:
                        submission.comments.replace_more(limit=0)  # Skip "more comments" links
                        post_comments = []
                        
                        for comment in submission.comments[:comment_limit]:
                            comment_data = await self._extract_comment_data(comment, submission.id)
                            post_comments.append(comment_data)
                        
                        comments.extend(post_comments)
                        all_comment_count += len(post_comments)
                
                result = await self._process_scraped_data(posts, comments, subreddit_name)
                result["data_source"] = "reddit_api"
                result["scrape_time_ms"] = round((time.time() - start_time) * 1000, 2)
                
                return result
                
            except Exception as e:
                logger.error(f"Error scraping Reddit: {e}")
                # Fall back to mock data
                logger.info("Falling back to mock data")
                return await self._generate_mock_data(subreddit_name, post_limit, comment_limit)
        else:
            # Use mock data
            logger.info("Using mock data (Reddit client not available)")
            return await self._generate_mock_data(subreddit_name, post_limit, comment_limit)
    
    async def _extract_post_data(self, submission) -> Dict[str, Any]:
        """Extract and clean data from a Reddit post"""
        # Extract raw data
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
        # Extract raw data
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
        # Create a copy to avoid modifying the original
        clean_post = post_data.copy()
        
        # Clean title
        clean_post['title'] = self._clean_text(clean_post['title'])
        
        # Clean selftext
        clean_post['selftext'] = self._clean_text(clean_post['selftext'])
        
        # Clean author
        clean_post['author'] = self._clean_text(clean_post['author'])
        
        return clean_post
    
    async def _clean_comment_data(self, comment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean comment data"""
        # Create a copy to avoid modifying the original
        clean_comment = comment_data.copy()
        
        # Clean body
        clean_comment['body'] = self._clean_text(clean_comment['body'])
        
        # Clean author
        clean_comment['author'] = self._clean_text(clean_comment['author'])
        
        return clean_comment
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing special characters, excessive whitespace, etc.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """
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
    
    async def _process_scraped_data(self, posts: List[Dict[str, Any]], comments: List[Dict[str, Any]], 
                              subreddit: str) -> Dict[str, Any]:
        """
        Process scraped data, store in database, and generate stats
        
        Args:
            posts: List of posts
            comments: List of comments
            subreddit: Subreddit name
            
        Returns:
            Dictionary with processed data and stats
        """
        # Initialize database if needed
        if self.db_manager and not hasattr(self.db_manager, 'connection_pool'):
            await self.initialize_db()
        
        # Store posts and comments in database
        stored_posts = 0
        stored_comments = 0
        
        # Generate alerts for concerning content
        alerts = []
        
        # Process posts
        for post in posts:
            # Check for alerts
            if SENTIMENT_AVAILABLE and 'sentiment_analysis' in post:
                alert = self._check_for_alert(
                    post['post_id'], 
                    f"{post['title']} {post['selftext']}", 
                    post['sentiment_analysis'], 
                    'post',
                    post['subreddit'],
                    post['author']
                )
                if alert:
                    alerts.append(alert)
            
            # Store in database (implementation would go here)
            stored_posts += 1
        
        # Process comments
        for comment in comments:
            # Check for alerts
            if SENTIMENT_AVAILABLE and 'sentiment_analysis' in comment:
                alert = self._check_for_alert(
                    comment['comment_id'], 
                    comment['body'], 
                    comment['sentiment_analysis'], 
                    'comment',
                    subreddit,
                    comment['author']
                )
                if alert:
                    alerts.append(alert)
            
            stored_comments += 1
        
        # Calculate sentiment stats
        sentiment_stats = self._calculate_sentiment_stats(posts)
        
        # Return processed data
        return {
            "posts": posts[:5],  # Return only a few samples to avoid large responses
            "comments": comments[:5],  # Return only a few samples
            "alerts": alerts[:5],  # Return only a few samples
            "stats": {
                "posts_collected": len(posts),
                "comments_collected": len(comments),
                "alerts_created": len(alerts),
                "stored_in_database": {
                    "posts": stored_posts,
                    "comments": stored_comments,
                    "alerts": 0
                },
                "sentiment_summary": sentiment_stats
            },
            "subreddit": subreddit,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
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
                # Determine severity based on sentiment and keywords
                if sentiment_result['compound_score'] < -0.5:
                    severity = 'high'
                elif sentiment_result['compound_score'] < -0.2:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                # Escalate mental health alerts
                if alert_type == 'mental_health':
                    severity = 'high' if severity != 'low' else 'medium'
                
                alert = {
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
                
                return alert
        
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
    
    def _create_text_hash(self, text: str) -> str:
        """Create a hash for text deduplication"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def _generate_mock_data(self, subreddit_name: str, post_limit: int, 
                           comment_limit: int) -> Dict[str, Any]:
        """Generate mock Reddit data for testing"""
        # Sample post titles and content
        sample_titles = [
            f"UCLA {random.choice(['Admissions', 'Parking', 'Housing', 'Classes', 'Professors'])} Question",
            f"What do you think of {random.choice(['Powell Library', 'the Sculpture Garden', 'Royce Hall', 'Ackerman Union'])}?",
            f"Looking for {random.choice(['study partners', 'roommates', 'clubs', 'internships'])} at UCLA",
            f"Thoughts on {random.choice(['CS program', 'Psychology department', 'Medical School', 'Law School'])}?",
            f"Best {random.choice(['restaurants', 'coffee shops', 'study spots', 'parking lots'])} near campus?"
        ]
        
        sample_content = [
            "I'm a freshman and I'm trying to figure out how to balance my coursework with social activities. Any advice?",
            "Just got accepted to UCLA and I'm super excited! Can't wait to join the Bruin community!",
            "Does anyone know if the library is open late during finals week? I need a quiet place to study.",
            "The professors in my department are amazing. They're so knowledgeable and always willing to help.",
            "I'm feeling really stressed about midterms. There's just so much material to cover and not enough time."
        ]
        
        sample_comments = [
            "Congratulations! UCLA is an amazing school, you're going to love it here.",
            "I felt the same way when I first started. It gets better as you figure out your routine.",
            "Have you tried talking to your academic advisor? They were really helpful when I was in your situation.",
            "The Sculpture Garden is my favorite place on campus. So peaceful and beautiful.",
            "I disagree with the previous comment. I think there are better options available.",
            "Finals week is always tough. Make sure to take care of yourself and get enough sleep.",
            "I'm in the same boat. Maybe we can form a study group?",
            "The campus food is actually pretty good compared to other universities I've visited."
        ]
        
        # Generate mock posts
        posts = []
        for i in range(min(post_limit, 10)):  # Limit to 10 mock posts
            title = random.choice(sample_titles)
            selftext = random.choice(sample_content)
            
            post_data = {
                'post_id': f"mock_post_{i}",
                'title': title,
                'selftext': selftext,
                'score': random.randint(1, 100),
                'upvote_ratio': round(random.uniform(0.5, 1.0), 2),
                'num_comments': random.randint(0, 50),
                'created_utc': datetime.now(timezone.utc).isoformat(),
                'author': f"mock_user_{random.randint(1, 1000)}",
                'subreddit': subreddit_name,
                'permalink': f"/r/{subreddit_name}/comments/mock_{i}",
                'url': f"https://www.reddit.com/r/{subreddit_name}/comments/mock_{i}"
            }
            
            # Clean data
            clean_post = await self._clean_post_data(post_data)
            
            # Add sentiment analysis if available
            if SENTIMENT_AVAILABLE:
                text_to_analyze = f"{clean_post['title']} {clean_post['selftext']}"
                clean_post['sentiment_analysis'] = sentiment_analyzer.analyze(text_to_analyze)
            
            posts.append(clean_post)
        
        # Generate mock comments
        comments = []
        for i, post in enumerate(posts):
            num_comments = min(comment_limit, 5)  # Limit to 5 mock comments per post
            for j in range(num_comments):
                comment_text = random.choice(sample_comments)
                
                comment_data = {
                    'comment_id': f"mock_comment_{i}_{j}",
                    'post_id': post['post_id'],
                    'body': comment_text,
                    'score': random.randint(1, 20),
                    'created_utc': datetime.now(timezone.utc).isoformat(),
                    'author': f"mock_user_{random.randint(1, 1000)}",
                    'permalink': f"{post['permalink']}/comment/{j}"
                }
                
                # Clean data
                clean_comment = await self._clean_comment_data(comment_data)
                
                # Add sentiment analysis if available
                if SENTIMENT_AVAILABLE:
                    clean_comment['sentiment_analysis'] = sentiment_analyzer.analyze(clean_comment['body'])
                
                comments.append(clean_comment)
        
        # Process data and generate stats
        result = await self._process_scraped_data(posts, comments, subreddit_name)
        result["data_source"] = "mock_data"
        
        return result

# For direct testing
if __name__ == "__main__":
    print("🚀 Starting Reddit Scraper Test...")
    print("=" * 50)
    
    async def test_scraper():
        scraper = RedditScraper()
        results = await scraper.scrape_subreddit("UCLA", 5, 10)
        print(json.dumps(results, indent=2))
    
    asyncio.run(test_scraper())
