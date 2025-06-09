#!/bin/bash

# UCLA Sentiment Analysis - Quick Fix and Start Script
echo "🚀 UCLA Sentiment Analysis - Quick Fix Script"
echo "==============================================="

# Step 1: Stop any existing services on port 8081
echo "🛑 Stopping any existing services on port 8081..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || echo "   No services running on port 8081"

# Step 2: Fix file permissions
echo "📁 Fixing file permissions..."
chmod -R 755 ./model_cache 2>/dev/null || mkdir -p ./model_cache
chown -R $(whoami) ./model_cache 2>/dev/null || echo "   Permission fix skipped"

# Step 3: Download NLTK data if needed
echo "📥 Ensuring NLTK VADER lexicon is available..."
python3 -c "
import nltk
import os
nltk_data_dir = './nltk_data'
os.makedirs(nltk_data_dir, exist_ok=True)
nltk.data.path.append(nltk_data_dir)
try:
    nltk.data.find('vader_lexicon')
    print('✅ VADER lexicon already available')
except:
    try:
        nltk.download('vader_lexicon', download_dir=nltk_data_dir, quiet=True)
        print('✅ VADER lexicon downloaded successfully')
    except Exception as e:
        print(f'⚠️ VADER download failed: {e}')
        print('   Trying alternative download...')
        try:
            nltk.download('vader_lexicon', quiet=True)
            print('✅ VADER lexicon downloaded to default location')
        except:
            print('❌ Failed to download VADER lexicon')
"

# Step 4: Test VADER locally first
echo "🧪 Testing VADER sentiment analysis..."
python3 -c "
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    
    # Add local nltk_data to path
    import os
    nltk.data.path.insert(0, './nltk_data')
    
    analyzer = SentimentIntensityAnalyzer()
    test_text = 'UCLA is an amazing university!'
    scores = analyzer.polarity_scores(test_text)
    print(f'✅ VADER test successful!')
    print(f'   Text: {test_text}')
    print(f'   Scores: {scores}')
    
    # Determine sentiment
    compound = scores['compound']
    if compound >= 0.05:
        sentiment = 'positive'
    elif compound <= -0.05:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    print(f'   Sentiment: {sentiment}')
    
except Exception as e:
    print(f'❌ VADER test failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ VADER test failed. Exiting."
    exit 1
fi

echo ""
echo "✅ All checks passed! Starting the model service..."
echo ""
echo "🚀 Starting standalone model service on port 8081..."
echo "   - Service will be available at: http://localhost:8081"
echo "   - API documentation at: http://localhost:8081/docs"
echo "   - Press Ctrl+C to stop"
echo ""

# Step 5: Start the service
python3 standalone_model_service.py

echo ""
echo "🛑 Service stopped."
