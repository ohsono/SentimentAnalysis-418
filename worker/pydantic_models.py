from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class WorkerScrapeRequest(BaseModel):
    subreddit: str = Field(default="UCLA", description="Subreddit to scrape")
    post_limit: int = Field(default=10, ge=1, le=1000, description="Number of posts to retrieve")
    comment_limit: int = Field(default=25, ge=1, le=200, description="Number of comments per post")
    sort_by: str = Field(default="hot", description="Sort method: hot, new, top, rising")
    time_filter: str = Field(default="week", description="Time filter for top posts")
    search_query: Optional[str] = Field(None, description="Search query within subreddit")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
    submitted_at: str
    result: Optional[Dict[str, Any]] = None

