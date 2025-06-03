from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class RedditPost(BaseModel):
    """
    What this does:
    - Stores all Reddit post information
    - Includes original data (title, score, etc.)
    - Adds processing results (sentiment, categories, alerts)
    
    Data flow:
    Reddit API → Raw Post Data → Processing → Enhanced Post with Analysis
    
    Example enhanced post:
    {
        "post_id": "abc123",
        "title": "Struggling with CS classes",
        "selftext": "I'm having a hard time with my computer science coursework...",
        "score": 25,
        "author": "student456",
        "subreddit": "UCLA",
        
        # Added by our processing:
        "sentiment": {
            "compound": -0.3,
            "category": "negative"
        },
        "categories": {
            "academic_departments": ["computer_science"]
        },
        "red_flags": [
            {"type": "academic_stress", "severity": "medium"}
        ]
    }
    """

    post_id: str
    title: str
    selftext: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: datetime
    author: str
    subreddit: str
    permalink: str
    url: str
    is_self: bool
    processed_at: Optional[datetime] = None
    sentiment: Optional[Dict[str, Any]] = None
    categories: Optional[Dict[str, Any]] = None

class RedditComment(BaseModel):
    """
    What this does:
    - Similar to RedditPost but for comments
    - Links comments to their parent posts
    - Tracks conversation depth (replies to replies)
    
    Why important:
    - Comments often contain more personal/emotional content
    - Can provide context to posts
    - Help understand community response to issues
    """

    comment_id: str
    post_id: str
    body: str
    score: int
    created_utc: datetime
    author: str
    parent_id: str
    is_submitter: bool
    depth: int = 0
    processed_at: Optional[datetime] = None
    sentiment: Optional[Dict[str, Any]] = None
    categories: Optional[Dict[str, Any]] = None
