#!/bin/bash

# DistilBERT Model Service Setup Script
# Sets up and tests the lightweight LLM service with /predict/llm endpoints

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  DistilBERT Model Service Setup${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found. Please run this script from the project root directory.${NC}"
    exit 1
fi

echo -e "${YELLOW}🤖 Setting up DistilBERT Model Service...${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${BLUE}📋 DistilBERT Model Service Features:${NC}"
echo -e "   • Lightweight LLM using DistilBERT"
echo -e "   • Pre-downloaded models for fast startup"
echo -e "   • /predict/llm endpoint for single predictions"
echo -e "   • /predict/llm/batch endpoint for batch processing"
echo -e "   • CPU optimized for cost efficiency"
echo -e "   • Multiple model variants available"

echo -e "\n${YELLOW}📦 Building DistilBERT Model Service container...${NC}"
if docker build -t ucla/distilbert-model-service -f Dockerfile.model-service-distilbert .; then
    echo -e "${GREEN}✅ DistilBERT service container built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build DistilBERT service container${NC}"
    exit 1
fi

echo -e "\n${YELLOW}🚀 Starting DistilBERT Model Service...${NC}"
if docker-compose up -d model-service-api; then
    echo -e "${GREEN}✅ DistilBERT service started${NC}"
else
    echo -e "${RED}❌ Failed to start DistilBERT service${NC}"
    exit 1
fi

echo -e "\n${YELLOW}⏳ Waiting for DistilBERT service to initialize...${NC}"
echo -e "   This may take a moment as models are being loaded..."

# Wait for service to be ready with model loading time
sleep 15

# Check if service is responding
max_retries=6
retry_count=0
service_ready=false

while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8081/health > /dev/null; then
        service_ready=true
        break
    fi
    retry_count=$((retry_count + 1))
    echo -e "   Waiting... (attempt $retry_count/$max_retries)"
    sleep 10
done

if [ "$service_ready" = true ]; then
    echo -e "${GREEN}✅ DistilBERT service is ready${NC}"
else
    echo -e "${RED}❌ DistilBERT service failed to start properly${NC}"
    echo -e "${YELLOW}💡 Check logs with: docker logs ucla_model_service${NC}"
    exit 1
fi

# Test the health endpoint
echo -e "\n${BLUE}🔍 Testing DistilBERT service health...${NC}"
if health_response=$(curl -s http://localhost:8081/health); then
    echo -e "${GREEN}✅ Health check passed${NC}"
    
    # Parse and display health info
    if command -v python3 > /dev/null; then
        python3 -c "
import json
try:
    health = json.loads('$health_response')
    print(f'   Service: {health.get(\"service\", \"unknown\")}')
    print(f'   Status: {health.get(\"status\", \"unknown\")}')
    print(f'   Loaded Models: {health.get(\"loaded_models\", [])}')
    memory = health.get('memory_info', {})
    if memory:
        print(f'   Memory Usage: {memory.get(\"percent\", 0)}% ({memory.get(\"used_mb\", 0):.0f}MB)')
except:
    pass
"
    fi
else
    echo -e "${RED}❌ Health check failed${NC}"
fi

# Test the predict/llm endpoint
echo -e "\n${BLUE}🧪 Testing /predict/llm endpoint...${NC}"
test_prediction=$(curl -s -X POST http://localhost:8081/predict/llm \
    -H "Content-Type: application/json" \
    -d '{"text": "I love studying at UCLA!", "model": "distilbert-sentiment"}')

if echo "$test_prediction" | grep -q "sentiment"; then
    echo -e "${GREEN}✅ /predict/llm endpoint working${NC}"
    
    # Show prediction result
    if command -v python3 > /dev/null; then
        python3 -c "
import json
try:
    result = json.loads('$test_prediction')
    print(f'   Text: \"I love studying at UCLA!\"')
    print(f'   Sentiment: {result.get(\"sentiment\", \"unknown\")}')
    print(f'   Confidence: {result.get(\"confidence\", 0):.3f}')
    print(f'   Processing Time: {result.get(\"processing_time_ms\", 0):.1f}ms')
except:
    pass
"
    fi
else
    echo -e "${RED}❌ /predict/llm endpoint failed${NC}"
    echo -e "Response: $test_prediction"
fi

# Test the predict/llm/batch endpoint
echo -e "\n${BLUE}🧪 Testing /predict/llm/batch endpoint...${NC}"
batch_prediction=$(curl -s -X POST http://localhost:8081/predict/llm/batch \
    -H "Content-Type: application/json" \
    -d '{"texts": ["UCLA is amazing!", "This is stressful"], "model": "distilbert-sentiment"}')

if echo "$batch_prediction" | grep -q "summary"; then
    echo -e "${GREEN}✅ /predict/llm/batch endpoint working${NC}"
    
    # Show batch results
    if command -v python3 > /dev/null; then
        python3 -c "
import json
try:
    result = json.loads('$batch_prediction')
    summary = result.get('summary', {})
    print(f'   Texts processed: {summary.get(\"total_processed\", 0)}')
    print(f'   Successful: {summary.get(\"successful\", 0)}')
    print(f'   Average time per text: {summary.get(\"average_time_per_text_ms\", 0):.1f}ms')
    dist = summary.get('sentiment_distribution', {})
    print(f'   Sentiment distribution: +{dist.get(\"positive\", 0)} -{dist.get(\"negative\", 0)} ={dist.get(\"neutral\", 0)}')
except:
    pass
"
    fi
else
    echo -e "${RED}❌ /predict/llm/batch endpoint failed${NC}"
    echo -e "Response: $batch_prediction"
fi

# Show available models
echo -e "\n${BLUE}📋 Available Models:${NC}"
models_response=$(curl -s http://localhost:8081/models)
if command -v python3 > /dev/null; then
    python3 -c "
import json
try:
    models_data = json.loads('$models_response')
    models = models_data.get('models', {})
    for key, info in models.items():
        status = 'loaded' if info.get('loaded') else 'available'
        print(f'   • {key}: {info.get(\"description\", \"No description\")} ({status})')
except:
    print('   Error parsing models response')
"
fi

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}  DistilBERT Service Ready!${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "\n${GREEN}✅ DistilBERT Model Service Setup Complete!${NC}"

echo -e "\n${BLUE}🚀 API Endpoints Available:${NC}"
echo -e "   • Health: GET http://localhost:8081/health"
echo -e "   • Single prediction: POST http://localhost:8081/predict/llm"
echo -e "   • Batch prediction: POST http://localhost:8081/predict/llm/batch"
echo -e "   • Models list: GET http://localhost:8081/models"
echo -e "   • API docs: http://localhost:8081/docs"

echo -e "\n${BLUE}💡 Quick Test Commands:${NC}"
echo -e "   # Single prediction"
echo -e "   ${YELLOW}curl -X POST http://localhost:8081/predict/llm \\${NC}"
echo -e "   ${YELLOW}  -H 'Content-Type: application/json' \\${NC}"
echo -e "   ${YELLOW}  -d '{\"text\": \"UCLA is great!\", \"model\": \"distilbert-sentiment\"}'${NC}"

echo -e "\n   # Batch prediction"
echo -e "   ${YELLOW}curl -X POST http://localhost:8081/predict/llm/batch \\${NC}"
echo -e "   ${YELLOW}  -H 'Content-Type: application/json' \\${NC}"
echo -e "   ${YELLOW}  -d '{\"texts\": [\"I love this!\", \"Too difficult\"], \"model\": \"distilbert-sentiment\"}'${NC}"

echo -e "\n   # Run comprehensive tests"
echo -e "   ${YELLOW}python test_distilbert_service.py${NC}"

echo -e "\n${BLUE}🔧 Management Commands:${NC}"
echo -e "   • View logs: ${YELLOW}docker logs ucla_model_service${NC}"
echo -e "   • Restart service: ${YELLOW}docker-compose restart model-service-api${NC}"
echo -e "   • Stop service: ${YELLOW}docker-compose stop model-service-api${NC}"

echo -e "\n${GREEN}🎉 Your lightweight LLM service is now ready for sentiment analysis!${NC}"
