from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModelPredictionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    model: str = Field(default="distilbert-sentiment")
    include_probabilities: bool = Field(default=True)

class ModelBatchRequest(BaseModel):
    texts: List[str] = Field(..., max_items=50)
    model: str = Field(default="distilbert-sentiment") 
    include_probabilities: bool = Field(default=True)

class ModelDownloadRequest(BaseModel):
    model: str = Field(...)

class HealthResponse(BaseModel):
    status: str
    service: str
    model_manager_available: bool
    loaded_models: List[str]
    memory_info: Dict[str, Any]
    timestamp: str
