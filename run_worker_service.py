#!/usr/bin/env python3

"""
Simple worker service runner
Alternative way to run the worker service
"""

import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Set environment variables from .env if available
env_file = current_dir / ".env"
if env_file.exists():
    print("📋 Loading environment variables from .env file...")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

if __name__ == "__main__":
    print("🚀 Starting UCLA Sentiment Analysis Worker Service")
    print("=" * 50)
    
    # Import the worker main module
    from worker.main import app
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8082))
    
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"📊 API Docs: http://{host}:{port}/docs")
    print("=" * 50)
    
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Worker service stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting worker service: {e}")
        sys.exit(1)
