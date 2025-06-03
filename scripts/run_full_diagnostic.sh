#!/bin/bash

# Complete Diagnostic and Test Script
# Checks Docker status, then runs API tests

set -e

echo "🔍 UCLA Sentiment Analysis - Complete Diagnostic & Test Suite"
echo "=" * 70

cd ~/Project/UCLA-MASDS/SentimentAnalysis-418

# Make scripts executable
chmod +x check_docker_status.sh
chmod +x comprehensive_api_test.py
chmod +x robust_build.sh

echo "📊 Step 1: Checking Docker container status..."
./check_docker_status.sh

echo ""
echo "🧪 Step 2: Running comprehensive API tests..."
python3 comprehensive_api_test.py

echo ""
echo "✅ Diagnostic and testing complete!"
