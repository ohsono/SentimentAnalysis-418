#!/bin/bash

# Enhanced Setup Script for API-Friendly Pipeline Service
echo "🚀 Setting up API-Friendly Pipeline Service"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "run_scheduled_worker.py" ]; then
    echo "❌ Please run this script from the project root directory"
    echo "   (The directory containing run_scheduled_worker.py)"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create virtual environment (recommended)
read -p "🤔 Create virtual environment? (recommended) [y/N]: " create_venv
if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
    echo "💡 Activate with: source venv/bin/activate (Linux/Mac) or venv\Scripts\activate (Windows)"
    
    # Activate virtual environment
    source venv/bin/activate 2>/dev/null || echo "⚠️ Please manually activate venv"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements_pipeline.txt" ]; then
    pip3 install -r requirements_pipeline.txt
else
    echo "⚠️ requirements_pipeline.txt not found, installing essential packages..."
    pip3 install fastapi uvicorn praw pandas redis psycopg2-binary python-dotenv
fi

# Download NLTK data
echo "📚 Downloading NLTK data..."
python3 -c "
import nltk
try:
    nltk.download('vader_lexicon', quiet=True)
    print('✅ NLTK data downloaded')
except Exception as e:
    print(f'⚠️ NLTK download failed: {e}')
"

# Create data directories
echo "📁 Creating data directories..."
mkdir -p worker/data/tasks
mkdir -p worker/data/results
mkdir -p worker/data/pipelines
mkdir -p worker/logs

# Set permissions
echo "🔐 Setting permissions..."
chmod +x run_scheduled_worker.py 2>/dev/null || echo "⚠️ Could not set execute permission"
find validation -name "*.py" -exec chmod +x {} \; 2>/dev/null || echo "⚠️ Could not set validation script permissions"

# Test basic imports
echo "🧪 Testing basic imports..."
python3 -c "
import sys
try:
    import fastapi, uvicorn, praw, pandas, redis, psycopg2
    print('✅ All critical packages imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('💡 Run: pip3 install -r requirements_pipeline.txt')
    sys.exit(1)
" && echo "🎉 Import test passed!" || echo "⚠️ Some imports failed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔄 Next steps:"
echo "1. Configure Reddit API credentials in .env.scheduler"
echo "2. Verify database connection settings"
echo "3. Run validation: python3 validation/quick_validation.py"
echo "4. Start service: python3 run_scheduled_worker.py"
echo ""
echo "📖 For more help, see VALIDATION_SUMMARY.md"
