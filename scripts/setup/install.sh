#!/bin/bash
set -e

echo "Installing UCLA Sentiment Analysis..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download NLTK data
python -c "import nltk; nltk.download('vader_lexicon')"

echo "✅ Installation completed!"
echo ""
echo "Next steps:"
echo "1. cp .env.example .env"
echo "2. Edit .env with your Reddit API credentials"
echo "3. docker-compose up -d"
echo "4. Visit http://localhost:8501 for dashboard"
