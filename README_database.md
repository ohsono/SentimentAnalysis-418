# UCLA Sentiment Analysis Database Setup

## Files Created

1. **`database_models.py`** - Contains all database models and schema definitions
2. **`test_database.py`** - Test script to create tables and validate the database setup

## Setup Instructions

### 1. Copy files to your project directory
```bash
# Copy the files to your actual project location
cp ~/database_models.py /Volume/T7_touch/Projects/UCLA-MASDS/SentimentAnalysis-418/
cp ~/test_database.py /Volume/T7_touch/Projects/UCLA-MASDS/SentimentAnalysis-418/

# Navigate to your project directory
cd /Volume/T7_touch/Projects/UCLA-MASDS/SentimentAnalysis-418/
```

### 2. Install required Python packages
```bash
pip install sqlalchemy psycopg2-binary
# or if you're using conda:
conda install sqlalchemy psycopg2
```

### 3. Test your database connection
Before running the test, make sure:
- Your Cloud SQL instance is running
- Your IP is authorized in Cloud SQL
- The user `ucla_app_user` exists with the correct password

```bash
# Test the basic connection first
psql -h 34.169.131.162 -U ucla_app_user -d ucla_sentiment_dev

# If that works, run the test script
python test_database.py
```

### 4. Expected Output
The test script will:
- ✅ Test database connection
- 📊 Create all required tables
- 🔍 Verify indexes were created
- 📋 Display table schemas
- 💾 Insert sample test data
- 🔍 Run sample queries

## Database Tables Created

1. **`sentiment_analysis`** - Store sentiment analysis results
2. **`batch_processing`** - Track batch processing jobs
3. **`reddit_content`** - Store Reddit posts and comments
4. **`alert_events`** - Store mental health/safety alerts
5. **`system_metrics`** - Store system performance metrics
6. **`analytics_cache`** - Cache computed analytics

## Environment Variables

The script uses these environment variables:
- `DATABASE_URL` - Full PostgreSQL connection string
- `DB_ECHO` - Set to 'true' to enable SQL query logging

## Connection String Format

```bash
# Format:
postgresql://username:password@host:port/database

# Your Cloud SQL example:
postgresql://ucla_app_user:app_user_password_123@34.169.131.162:5432/ucla_sentiment_dev
```

## Integration with Docker Compose

Update your docker-compose-enhanced.yml services to use these models:

```yaml
services:
  api:
    environment:
      - DATABASE_URL=postgresql://ucla_app_user:app_user_password_123@34.169.131.162:5432/ucla_sentiment_dev
    volumes:
      - ./database_models.py:/app/database_models.py
```

## Troubleshooting

### Connection Issues
```bash
# Check if Cloud SQL instance is running
gcloud sql instances list

# Check if your IP is authorized
gcloud sql instances describe ucla-sentiment-postgres

# Test connection manually
psql -h 34.169.131.162 -U ucla_app_user -d ucla_sentiment_dev
```

### User Permission Issues
```bash
# Recreate user if needed
gcloud sql users delete ucla_app_user --instance=ucla-sentiment-postgres --quiet
gcloud sql users create ucla_app_user --instance=ucla-sentiment-postgres --password=app_user_password_123
```

### Python Import Issues
```bash
# Make sure SQLAlchemy is installed
pip install sqlalchemy psycopg2-binary

# Check if files are in the same directory
ls -la database_models.py test_database.py
```

## Next Steps

1. Copy files to project directory
2. Run the test script to create tables
3. Update your application code to import from `database_models.py`
4. Update docker-compose.yml to use Cloud SQL instead of local PostgreSQL
5. Run your application with the new database schema!
