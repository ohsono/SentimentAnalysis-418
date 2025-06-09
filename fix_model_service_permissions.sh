#!/bin/bash

# Fix Model Service Permissions and Configuration
# Run this script to fix the sentiment analysis model service issues

echo "🔧 UCLA Sentiment Analysis - Fixing Model Service Issues"
echo "========================================================="

# 1. Fix Docker permissions
echo "📁 Fixing model cache directory permissions..."
sudo chmod -R 755 ./model_cache/ 2>/dev/null || mkdir -p ./model_cache
sudo chown -R $USER:$USER ./model_cache/ 2>/dev/null || echo "Note: Running without sudo, permissions may need manual adjustment"

# 2. Create proper model directories
echo "📂 Creating model directories..."
mkdir -p model_cache/distilbert-sentiment
mkdir -p model_cache/vader
mkdir -p logs
mkdir -p models

# 3. Fix Docker Compose service configuration
echo "🐳 Updating Docker Compose configuration..."
cat > docker-compose.model-fix.yml << 'EOF'
services:
  model-service-fixed:
    build:
      context: .
      dockerfile: Dockerfile.model-service-fixed
    container_name: model_service_fixed
    environment:
      - HOST=0.0.0.0
      - PORT=8081
      - MODEL_CACHE_DIR=/app/models
      - PRELOAD_MODEL=vader  # Start with VADER, then download others
      - PYTHONPATH=/app
      - NLTK_DATA=/app/nltk_data
    volumes:
      - ./model_cache:/app/models:rw
      - ./logs:/app/logs:rw
      - ./nltk_data:/app/nltk_data:rw
    ports:
      - "8081:8081"
    user: "1000:1000"  # Use your user ID
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    networks:
      - sentiment_network

networks:
  sentiment_network:
    driver: bridge
EOF

# 4. Create fixed Dockerfile
echo "🐳 Creating fixed Dockerfile..."
cat > Dockerfile.model-service-fixed << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MODEL_CACHE_DIR=/app/models
ENV NLTK_DATA=/app/nltk_data

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements_model_service_distilbert.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements_model_service_distilbert.txt

# Create directories with proper permissions
RUN mkdir -p /app/models /app/logs /app/nltk_data && \
    chmod -R 755 /app/models /app/logs /app/nltk_data

# Download NLTK data as root first
RUN python -c "import nltk; nltk.download('vader_lexicon', download_dir='/app/nltk_data', quiet=True)"

# Copy application code
COPY model_services/ ./model_services/
COPY requirements*.txt ./

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Model Service..."\n\
echo "📁 Model cache dir: $MODEL_CACHE_DIR"\n\
echo "🔍 Checking permissions..."\n\
ls -la /app/models || echo "Creating models directory..."\n\
mkdir -p /app/models /app/logs\n\
echo "✅ Starting service on port 8081"\n\
cd /app\n\
exec python -m model_services.fixed_model_service --host 0.0.0.0 --port 8081' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Use entrypoint
CMD ["/app/entrypoint.sh"]
EOF

# 5. Download NLTK data locally
echo "📥 Downloading NLTK VADER lexicon..."
python3 -c "
import nltk
import os
nltk_data_dir = './nltk_data'
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)
try:
    nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
    print('✅ VADER lexicon downloaded successfully')
except Exception as e:
    print(f'⚠️ VADER download failed: {e}')
"

# 6. Test VADER locally
echo "🧪 Testing VADER sentiment analysis..."
python3 -c "
import sys
sys.path.append('.')
try:
    import nltk
    nltk.data.path.append('./nltk_data')
    from nltk.sentiment import SentimentIntensityAnalyzer
    analyzer = SentimentIntensityAnalyzer()
    test_text = 'This is a great day for UCLA!'
    scores = analyzer.polarity_scores(test_text)
    print(f'✅ VADER test successful: {scores}')
except Exception as e:
    print(f'❌ VADER test failed: {e}')
"

# 7. Create test endpoint script
echo "🧪 Creating test script..."
cat > test_model_service.py << 'EOF'
#!/usr/bin/env python3
import requests
import json
import time

def test_model_service():
    base_url = "http://localhost:8081"
    
    print("🧪 Testing UCLA Sentiment Analysis Model Service")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Service is healthy")
        else:
            print(f"⚠️ Service health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test prediction endpoint
    test_data = {
        "text": "UCLA is an amazing university!",
        "model_name": "vader",  # Start with VADER
        "return_confidence": True
    }
    
    try:
        print(f"\n🔮 Testing prediction with: '{test_data['text']}'")
        response = requests.post(
            f"{base_url}/predict", 
            json=test_data, 
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction successful!")
            print(f"   Sentiment: {result.get('sentiment')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Model: {result.get('model_used')}")
        else:
            print(f"❌ Prediction failed: {response.text}")
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")

if __name__ == "__main__":
    test_model_service()
EOF

chmod +x test_model_service.py

echo ""
echo "✅ Model service fix complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Stop current containers: docker-compose down"
echo "2. Build new service: docker-compose -f docker-compose.model-fix.yml build"
echo "3. Start fixed service: docker-compose -f docker-compose.model-fix.yml up model-service-fixed"
echo "4. Test the service: python3 test_model_service.py"
echo ""
echo "🔧 Alternative local testing:"
echo "   python3 -m model_services.fixed_model_service"
echo ""
