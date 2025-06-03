#!/bin/bash

# Master Script - Complete UCLA Sentiment Analysis Setup
# This script handles everything from build to test

echo "🎯 UCLA Sentiment Analysis API - Master Setup Script"
echo "=================================================================="
echo "This script will:"
echo "1. Fix Docker build issues"
echo "2. Build and start all services" 
echo "3. Test API functionality"
echo "4. Provide next steps"
echo ""

cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

# Make all scripts executable
echo "📋 Making scripts executable..."
chmod +x fix_and_restart.sh
chmod +x comprehensive_api_test.py
chmod +x quick_test.py
chmod +x check_docker_status.sh
chmod +x robust_build.sh

# Ask user what they want to do
echo ""
echo "🤔 What would you like to do?"
echo "1. 🔨 Full rebuild and restart (recommended if API not working)"
echo "2. 🚀 Quick restart (if images already built)"
echo "3. 🧪 Test existing API (if already running)"
echo "4. 🔍 Check Docker status only"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🔨 Running full rebuild and restart..."
        ./fix_and_restart.sh
        
        echo ""
        echo "🧪 Running quick functionality test..."
        python3 quick_test.py
        ;;
        
    2)
        echo ""
        echo "🚀 Quick restart of services..."
        docker-compose -f docker-compose-enhanced.yml down
        docker-compose -f docker-compose-enhanced.yml up -d
        
        echo "⏳ Waiting for services to start..."
        sleep 30
        
        echo ""
        echo "🧪 Testing API..."
        python3 quick_test.py
        ;;
        
    3)
        echo ""
        echo "🧪 Testing existing API..."
        python3 quick_test.py
        
        echo ""
        echo "💡 For comprehensive tests, run:"
        echo "   python3 comprehensive_api_test.py"
        ;;
        
    4)
        echo ""
        echo "🔍 Checking Docker status..."
        ./check_docker_status.sh
        ;;
        
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "📚 Available commands for future use:"
echo "  ./fix_and_restart.sh       - Complete rebuild and restart"
echo "  python3 quick_test.py      - Quick API functionality test"
echo "  python3 comprehensive_api_test.py - Full test suite"
echo "  ./check_docker_status.sh   - Check Docker container status"
echo ""
echo "🌐 If everything is working, access your API at:"
echo "  • http://localhost:8080/docs (Interactive documentation)"
echo "  • http://localhost:8080/health (Health check)"
echo "  • http://localhost:8080 (API info)"
echo ""
echo "✅ Setup script complete!"
