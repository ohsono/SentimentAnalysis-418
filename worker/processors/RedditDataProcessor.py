#!/usr/bin/env python3

import re

import pandas as pd
import numpy as np
#from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import demoji
from datetime import datetime, timezone
from typing import Dict, List, Any
import logging
from collections import defaultdict
from transformers import pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditDataProcessor:
    """
    Processes scraped Reddit data for analysis
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the data processor with config
        Args:
            config (Dict): The configuration dictionary
        """
        if config is None:
            config = {}
        self.keyword_include = config.get('keyword_include', ['UCLA','ucla', 'Bruins', 'bruins', 'UCLA Bruins', 'ucla bruins'])
        self.keyword_exclude = config.get('keyword_exclude', ['NSFW','nsfw'])
        self.analyzer = SentimentIntensityAnalyzer()
        demoji.download_codes()  # For emoji handling


        self.subreddit = config.get('subreddit', '')
        self.processed_data = None
    

    def _clean_text(self, text):
        # Step 0: Convert emojis to text descriptions
        text = demoji.replace_with_desc(text, sep=" ")
        
        # Step 1: Remove Reddit markdown
        text = re.sub(r'\*{1,3}|_{1,3}|~{2}|`{1,3}', '', text)
        
        # Step 2: Convert emojis to text descriptions
        text = demoji.replace_with_desc(text, sep=" ")
        
        # Step 3: Remove URLs and special characters
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'[^a-zA-Z\s\']', '', text)
        
        # Step 4: Clean whitespace
        return ' '.join(text.lower().split())
    
    def _add_sentiment(self, text):
        vs = self.analyzer.polarity_scores(text)
        #return vs['compound']  # Returns score between -1 and 1
        return {
            'sentiment_compound': vs['compound'], # aggregated score
            'sentiment_negative': vs['neg'], # between -1 and 0
            'sentiment_neutral': vs['neu'], # score == 0
            'sentiment_positive': vs['pos'] # between 0 and 1
        }


    def _process_entry(self, entry):
        # Add data lineage metadata
        entry['processed_date'] = datetime.utcnow().isoformat()
        entry['text_length'] = len(entry['body'])
        
        # Clean text and add sentiment
        entry['cleaned_text'] = self._clean_text(entry['body'])
        entry['sentiment'] = self._add_sentiment(entry['cleaned_text'])
        
        return entry

    def _contains_keywords(self, text: str, keywords: List[str]) -> bool:
        """
        Check if text contains any of the specified keywords (case-insensitive)
        Args:
            text (str): The text to check
            keywords (List[str]): The list of keywords to check for
        Returns:
            bool: True if text contains any of the specified keywords, False otherwise
        """
        if not keywords:
            return False
        lower_text = text.lower()
        return any(keyword.lower() in lower_text for keyword in keywords)

    def _add_sentiment_metadata(self, df):
        """
        Add sentiment metadata to the dataframe
        Args:
            df (pd.DataFrame): The dataframe to add sentiment metadata to
        Returns:
            pd.DataFrame: The dataframe with sentiment metadata
        """
        df['sentiment_category'] = pd.cut(df['sentiment'],
                                        bins=[-1, -0.5, 0.5, 1],
                                        labels=['negative', 'neutral', 'positive'])
        df['emotional_intensity'] = df['sentiment'].abs()
        return df

    # def advanced_sentiment_analysis(self,texts):
    #     sentiment_analyzer = pipeline(
    #         "sentiment-analysis",
    #         model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    #         return_all_scores=True
    #     )
    #     results = sentiment_analyzer(texts)
    #     return [(score[0]['score'], score[1]['score'], score[2]['score']) for score in results]

    # # Example usage
    # sample_texts = cleaned_data['cleaned_text'].tolist()
    # sentiment_scores = advanced_sentiment_analysis(sample_texts[:2])  # Limiting for demo
    # print("\nAdvanced Sentiment Scores:")
    # for text, scores in zip(sample_texts[:2], sentiment_scores):
    #     print(f"Text: {text[:50]}...")
    #     print(f"Negative: {scores[0]:.2f}, Neutral: {scores[1]:.2f}, Positive: {scores[2]:.2f}")


    def process_data(self, data):
            df = pd.DataFrame(data)
            
            # Add source metadata
            df['data_source'] = df.apply(lambda x: f"{x['subreddit']}_{x['id']}", axis=1)
            
            # Filtering
            mask = pd.Series([True] * len(df))
            if self.include_keywords:
                mask &= df['body'].str.contains('|'.join(self.include_keywords), case=False)
            if self.exclude_keywords:
                mask &= ~df['body'].str.contains('|'.join(self.exclude_keywords), case=False)
            
            filtered = df[mask].apply(self._process_entry, axis=1)
            
            # Quality checks
            filtered = filtered[filtered['text_length'] >= 50]  # Remove short posts
            filtered = filtered.drop_duplicates(subset=['cleaned_text'])
            
            return filtered

    def process_data(self, raw_posts: List[Dict], raw_comments: List[Dict]) -> Dict[str, Any]:
        """
        Process raw data with keyword filtering
        Returns filtered posts/comments and statistics
        """
        try:
            filtered_posts = []
            filtered_comments = []
            stats = {
                'total_posts': len(raw_posts),
                'total_comments': len(raw_comments),
                'filtered_posts': 0,
                'filtered_comments': 0,
                'excluded_posts': 0,
                'excluded_comments': 0
            }

            # Create comment index by post_id
            comments_by_post = defaultdict(list)
            for comment in raw_comments:
                comments_by_post[comment['post_id']].append(comment)

            for post in raw_posts:
                # Check post exclusion
                post_text = f"{post['title']} {post['selftext']}"
                if self._contains_keywords(post_text, self.keyword_exclude):
                    stats['excluded_posts'] += 1
                    continue
                
                # Check post inclusion
                post_has_include = self._contains_keywords(post_text, self.keyword_include)
                
                # Process comments
                post_comments = comments_by_post.get(post['post_id'], [])
                filtered_post_comments = []
                
                for comment in post_comments:
                    if self._contains_keywords(comment['body'], self.keyword_exclude):
                        stats['excluded_comments'] += 1
                        continue
                    
                    if post_has_include or self._contains_keywords(comment['body'], self.keyword_include):
                        filtered_post_comments.append(comment)
                
                # Only keep post if it has include keywords or has filtered comments
                if post_has_include or filtered_post_comments:
                    filtered_posts.append(post)
                    filtered_comments.extend(filtered_post_comments)
                    stats['filtered_posts'] += 1
                    stats['filtered_comments'] += len(filtered_post_comments)

            # Calculate final statistics
            stats['filtered_posts_ratio'] = stats['filtered_posts'] / stats['total_posts'] if stats['total_posts'] > 0 else 0
            stats['filtered_comments_ratio'] = stats['filtered_comments'] / stats['total_comments'] if stats['total_comments'] > 0 else 0
            
            self.processed_data = {
                'posts': filtered_posts,
                'comments': filtered_comments,
                'stats': stats
            }
            
            return self.processed_data
            
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            raise
