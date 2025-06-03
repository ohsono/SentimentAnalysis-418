#!/bin/bash
set -e

echo "Installing UCLA Sentiment Analysis dependencies..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Download NLTK data
python -c "import nltk; nltk.download('vader_lexicon')"

echo "Dependencies installed successfully!"
