# Simple pydantic_models.py without model_config

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class ModelPredictionRequest(BaseModel):
    text: str = Field(..., description="Text to analyze for sentiment")
    model_name: Optional[str] = Field(default="default", description="Model to use for prediction")
    return_confidence: Optional[bool] = Field(default=True, description="Whether to return confidence scores")

class ModelBatchRequest(BaseModel):
    texts: List[str] = Field(..., description="List of texts to analyze")
    model_name: Optional[str] = Field(default="default", description="Model to use for prediction")
    return_confidence: Optional[bool] = Field(default=True, description="Whether to return confidence scores")

class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    confidence: Optional[float] = None
    scores: Optional[Dict[str, float]] = None
    model_used: str
    processing_time: float

class BatchSentimentResponse(BaseModel):
    results: List[SentimentResponse]
    total_processed: int
    total_processing_time: float
    model_used: str

class HealthResponse(BaseModel):
    status: str
    service_name: str
    timestamp: datetime
    manager_available: bool  # Changed from model_manager_available to avoid namespace conflict
    memory_info: Optional[Dict[str, Any]] = None
    uptime: Optional[str] = None
    models_loaded: Optional[List[str]] = None

class ModelInfo(BaseModel):
    name: str
    type: str
    loaded: bool
    size_mb: Optional[float] = None
    last_used: Optional[datetime] = None

class ModelsResponse(BaseModel):
    available_models: List[ModelInfo]
    current_model: Optional[str] = None
    total_models: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None

class ModelDownloadRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to download")
    force_download: Optional[bool] = Field(default=False, description="Force re-download if model exists")

class ModelDownloadResponse(BaseModel):
    message: str
    model_name: str
    status: str
    download_size_mb: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    timestamp: datetime

class ModelInfoResponse(BaseModel):
    model_key: str
    name: str
    type: str
    architecture: Optional[str] = None
    loaded: bool
    size_mb: Optional[float] = None
    parameters: Optional[str] = None
    accuracy: Optional[float] = None
    last_used: Optional[datetime] = None
    created_date: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    supported_languages: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    performance_metrics: Optional[Dict[str, float]] = None

class SystemMetrics(BaseModel):
    memory: Dict[str, float]
    cpu: Dict[str, float]

class ProcessMetrics(BaseModel):
    memory: Dict[str, float]
    cpu_percent: float
    threads: int
    pid: int

class ModelMetrics(BaseModel):
    loaded_count: int
    available_count: int
    current_model: Optional[str] = None

class RequestMetrics(BaseModel):
    total_predictions: int
    total_batch_predictions: int
    average_response_time_ms: float
    error_rate: float

class ServiceMetrics(BaseModel):
    uptime: str
    status: str
    manager_available: bool
    timestamp: str

class MetricsResponse(BaseModel):
    service: ServiceMetrics
    system: SystemMetrics
    process: ProcessMetrics
    models: ModelMetrics
    requests: RequestMetrics