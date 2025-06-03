# UCLA Sentiment Analysis API Documentation

## API Endpoints

### Root Endpoint
```
GET /
```
Returns basic information about the API.

### Health Check
```
GET /health
```
Returns health status of the API and its services.

### Sentiment Analysis
```
POST /predict
```
Analyzes sentiment of a text using VADER.

**Request Body:**
```json
{
  "text": "Your text to analyze",
  "include_probabilities": true
}
```

### Batch Sentiment Analysis
```
POST /predict/batch
```
Analyzes sentiment of multiple texts in a single request.

**Request Body:**
```json
[
  "First text to analyze",
  "Second text to analyze",
  "Third text to analyze"
]
```

### Reddit Scraping (Mock)
```
POST /scrape
```
Simulates scraping Reddit data.

**Request Body:**
```json
{
  "subreddit": "UCLA",
  "post_limit": 10
}
```

### Analytics
```
GET /analytics
```
Returns analytics data about sentiment analysis results.

### Alerts
```
GET /alerts
```
Returns active alerts from the system.

### Update Alert Status
```
POST /alerts/{alert_id}/status
```
Updates the status of a specific alert.

**Request Body:**
```json
{
  "status": "resolved",
  "notes": "This alert has been resolved"
}
```

### System Status
```
GET /status
```
Returns detailed system status information.

## Important Notes

1. The endpoints `/predict`, `/predict/batch`, and `/scrape` require HTTP POST method.
2. The dashboard is accessible at port 8501.
3. Database status is displayed in the health check endpoint.
