#!/usr/bin/env python3

"""
Local runner for DistilBERT Model Service
Runs the lightweight LLM service locally for development
"""

import os
import sys
from pathlib import Path
import uvicorn

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_environment():
    """Setup environment variables for local development"""
    
    # Model service configuration
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8081")
    os.environ.setdefault("MODEL_CACHE_DIR", str(current_dir / "models"))
    os.environ.setdefault("PRELOAD_MODEL", "distilbert-sentiment")
    
    # Create model cache directory
    model_cache_dir = Path(os.environ["MODEL_CACHE_DIR"])
    model_cache_dir.mkdir(exist_ok=True)
    
    print("🔧 Environment configured for DistilBERT Model Service")
    print(f"   Model Cache: {os.environ.get('MODEL_CACHE_DIR')}")
    print(f"   Preload Model: {os.environ.get('PRELOAD_MODEL')}")

if __name__ == "__main__":
    setup_environment()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8081))
    
    print(f"🤖 Starting DistilBERT Model Service locally on {host}:{port}")
    print("📡 Endpoints: /predict/llm and /predict/llm/batch")
    print("🚀 Lightweight LLM service with pre-downloaded models")
    print("📚 API docs will be available at http://localhost:8081/docs")
    
    # Import and run the DistilBERT service
    uvicorn.run(
        "model_services.distilbert_service:app",
        host=host,
        port=port,
        reload=True,  # Enable reload for development
        log_level="info",
        access_log=True
    )
