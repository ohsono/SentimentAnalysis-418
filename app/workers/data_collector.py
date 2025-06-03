#!/usr/bin/env python3

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any
import os
import json

from ..services.reddit_scraper import RedditScraper
from ..services.data_processor import DataProcessor
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..services.alert_service import AlertService
from ..utils.config import load_config
from ..utils.logging import setup_logging

logger = logging.getLogger(__name__)

class DataCollectorWorker:
    """Background worker for data collection"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or load_config()
        self.reddit_scraper = RedditScraper(self.config)
        self.data_processor = DataProcessor(self.config)
        self.sentiment_analyzer = SentimentAnalyzer()
        self.alert_service = AlertService(self.config)
        self.running = False
        
    async def start(self):
        """Start the data collection worker"""
        self.running = True
        logger.info("Data collection worker started")
        
        while self.running:
            try:
                await self.collect_and_process_data()
                
                # Sleep for configured interval (default 1 hour)
                interval = self.config.get('collection_interval', 3600)
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in data collection worker: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop the data collection worker"""
        self.running = False
        logger.info("Data collection worker stopped")
    
    async def collect_and_process_data(self):
        """Collect and process Reddit data"""
        try:
            # Get configuration
            subreddit = self.config.get('reddit', {}).get('subreddit', 'UCLA')
            post_limit = self.config.get('reddit', {}).get('post_limit', 100)
            
            logger.info(f"Starting data collection for r/{subreddit}")
            
            # Scrape Reddit data
            reddit_data = self.reddit_scraper.scrape_subreddit(subreddit, post_limit)
            
            if 'error' in reddit_data:
                logger.error(f"Reddit scraping failed: {reddit_data['error']}")
                return
            
            # Process posts
            processed_posts = self.data_processor.process_posts(reddit_data['posts'])
            processed_comments = self.data_processor.process_comments(reddit_data['comments'])
            
            # Analyze sentiment
            for post in processed_posts:
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                post['sentiment_analysis'] = sentiment
                
                # Check for alerts
                for red_flag in post.get('red_flags', []):
                    self.alert_service.create_alert(post, red_flag['type'], red_flag['severity'])
            
            for comment in processed_comments:
                text = comment.get('body', '')
                sentiment = self.sentiment_analyzer.analyze_sentiment(text)
                comment['sentiment_analysis'] = sentiment
                
                # Check for alerts
                for red_flag in comment.get('red_flags', []):
                    self.alert_service.create_alert(comment, red_flag['type'], red_flag['severity'])
            
            # Log statistics
            stats = reddit_data.get('stats', {})
            stats.update({
                'processed_posts': len(processed_posts),
                'processed_comments': len(processed_comments),
                'alerts_created': len(self.alert_service.get_active_alerts()),
                'processing_completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"Data collection completed: {stats}")
            
            # Save results (in production, would save to database)
            await self.save_results(processed_posts, processed_comments, stats)
            
        except Exception as e:
            logger.error(f"Error in collect_and_process_data: {e}")
    
    async def save_results(self, posts: list, comments: list, stats: dict):
        """Save processing results"""
        try:
            # In production, would save to database
            # For now, save to local files for demonstration
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create data directory if it doesn't exist
            os.makedirs('data/processed', exist_ok=True)
            
            # Save posts
            posts_file = f'data/processed/posts_{timestamp}.json'
            with open(posts_file, 'w') as f:
                json.dump(posts, f, indent=2, default=str)
            
            # Save comments
            comments_file = f'data/processed/comments_{timestamp}.json'
            with open(comments_file, 'w') as f:
                json.dump(comments, f, indent=2, default=str)
            
            # Save stats
            stats_file = f'data/processed/stats_{timestamp}.json'
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
            
            logger.info(f"Results saved: {len(posts)} posts, {len(comments)} comments")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main():
    """Main function for running the data collector"""
    setup_logging()
    config = load_config()
    
    worker = DataCollectorWorker(config)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        worker.stop()

if __name__ == "__main__":
    asyncio.run(main())
