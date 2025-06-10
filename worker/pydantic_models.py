from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

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

class PipelineRequest(BaseModel):
    """Request model for pipeline execution"""
    subreddit: str = Field(default="UCLA", description="Subreddit to scrape")
    post_limit: int = Field(default=100, ge=1, le=1000, description="Number of posts to retrieve")
    comment_limit: int = Field(default=50, ge=1, le=200, description="Number of comments per post")
    enable_processing: bool = Field(default=True, description="Enable data processing step")
    enable_cleaning: bool = Field(default=True, description="Enable data cleaning step")
    enable_database: bool = Field(default=True, description="Enable database loading step")
    priority: str = Field(default="normal", description="Pipeline priority: low, normal, high")
    scheduled_time: Optional[str] = Field(None, description="Schedule for future execution (ISO datetime)")
    notify_webhook: Optional[str] = Field(None, description="Webhook URL for completion notification")

class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status"""
    pipeline_id: str
    status: str  # queued, running, completed, failed, cancelled
    current_step: Optional[str] = None  # scraping, processing, cleaning, database
    progress: float = Field(description="Progress percentage (0-100)")
    steps_completed: List[str] = Field(default_factory=list)
    steps_failed: List[str] = Field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: List[str] = Field(default_factory=list)

class PipelineHistoryResponse(BaseModel):
    """Response model for pipeline execution history"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_minutes: float
    recent_executions: List[Dict[str, Any]]
    next_scheduled: Optional[str] = None

class ScheduleRequest(BaseModel):
    """Request model for scheduling operations"""
    operation_type: str = Field(description="Type of operation: scrape, pipeline")
    schedule_time: str = Field(description="Schedule time (ISO datetime or cron expression)")
    recurrence: Optional[str] = Field(None, description="Recurrence pattern: once, daily, weekly, hourly")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific parameters")
    enabled: bool = Field(default=True, description="Whether the schedule is enabled")

class ScheduleResponse(BaseModel):
    """Response model for schedule operations"""
    schedule_id: str
    operation_type: str
    next_execution: str
    recurrence: Optional[str] = None
    enabled: bool
    created_at: str
    parameters: Dict[str, Any]

class WorkerHealthResponse(BaseModel):
    """Enhanced health response model"""
    status: str
    service: str
    version: str
    scheduler_enabled: bool
    pipeline_running: bool
    database_connected: bool
    redis_connected: bool
    active_pipelines: int
    queue_size: int
    uptime_seconds: float
    task_stats: Dict[str, Any]
    next_scheduled_scrape: Optional[str] = None
    system_resources: Optional[Dict[str, Any]] = None
    timestamp: str

