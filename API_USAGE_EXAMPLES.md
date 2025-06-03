# Worker API Usage Examples

## 🚀 Fixed: Reddit Scraping API - Correct Usage

### ❌ Previous Error
```
GET /scrape -> 405 Method Not Allowed
```

### ✅ Fixed Solutions

## 1. GET /scrape - API Information
```bash
curl http://localhost:8082/scrape
```
This now returns helpful information about how to use the scraping API.

## 2. POST /scrape - Submit Scraping Task

### Basic Example
```bash
curl -X POST http://localhost:8082/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "python",
    "post_limit": 5,
    "comment_limit": 3
  }'
```

### Advanced Example
```bash
curl -X POST http://localhost:8082/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "MachineLearning",
    "post_limit": 10,
    "comment_limit": 5,
    "sort_by": "hot",
    "time_filter": "week",
    "search_query": "neural networks"
  }'
```

## 3. Check Health Status
```bash
curl http://localhost:8082/health
```

## 4. List All Tasks
```bash
curl http://localhost:8082/tasks
```

## 5. Check Task Status
```bash
# Replace TASK_ID with actual task ID from scrape response
curl http://localhost:8082/tasks/TASK_ID
```

## 6. API Documentation
Visit: http://localhost:8082/docs

## Python Examples

### Using requests library
```python
import requests

# Submit scraping task
response = requests.post('http://localhost:8082/scrape', json={
    'subreddit': 'python',
    'post_limit': 5,
    'comment_limit': 3,
    'sort_by': 'hot'
})

result = response.json()
task_id = result['task_id']
print(f"Task submitted: {task_id}")

# Check task status
status_response = requests.get(f'http://localhost:8082/tasks/{task_id}')
status = status_response.json()
print(f"Task status: {status['status']}")
```

## Request Parameters

### Required Fields
- `subreddit`: Name of subreddit (without "r/")
- `post_limit`: Number of posts (1-1000)  
- `comment_limit`: Comments per post (1-200)

### Optional Fields
- `sort_by`: "hot", "new", "top", "rising" (default: "hot")
- `time_filter`: "all", "day", "week", "month", "year" (default: "week")
- `search_query`: Search within subreddit (optional)

## Test the Fixed API
```bash
# Option 1: Use development mode (with auto-reload, no warning)
python run_worker_local.py

# Option 2: Use production mode (no auto-reload, no warning) 
python run_worker_prod.py

# Option 3: Run the automated test script
python test_worker_api.py
```

This will test all endpoints and show you exactly how the API works!
