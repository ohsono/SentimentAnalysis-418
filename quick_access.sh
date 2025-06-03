#!/bin/bash

# Make this script executable
chmod +x "$0"

# Quick Access Script for Reorganized UCLA Sentiment Analysis Project
# This script makes all scripts executable and provides quick access commands

echo "🗂️  UCLA Sentiment Analysis - Project Quick Access"
echo "=================================================="

cd "$(dirname "$0")"

echo ""
echo "📂 Making all scripts executable..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x debug/*.sh 2>/dev/null || true
echo "✅ All scripts are now executable"

echo ""
echo "🚀 Quick Commands:"
echo "=================="
echo ""
echo "🔧 Setup & Deployment:"
echo "  ./scripts/quick_start.sh              # Quick start the entire system"
echo "  ./scripts/master_setup.sh             # Complete setup and configuration"
echo "  ./scripts/deploy_enhanced.sh          # Deploy enhanced version"
echo "  ./scripts/fix_and_restart.sh          # Fix issues and restart"
echo ""
echo "🧪 Testing & Diagnostics:"
echo "  ./debug/test_port_8888.sh            # Test API on port 8888"
echo "  ./scripts/check_docker_status.sh      # Check Docker container status"
echo "  ./debug/quick_status.sh              # Quick system status check"
echo "  python debug/comprehensive_api_test.py # Full API test suite"
echo ""
echo "🐳 Docker Commands:"
echo "  docker-compose up -d                  # 🚀 Main production setup"
echo "  docker-compose -f docker-compose.dev.yml up -d       # 🛠️  Development setup"
echo "  docker-compose -f docker-compose-enhanced.yml up -d  # 📈 Full featured setup"
echo "  ./debug/quick_docker_cleanup.sh      # 🧹 Clean old containers"
echo ""
echo "📊 Port 8888 Commands:"
echo "  curl http://localhost:8888/health     # Check API health"
echo "  curl http://localhost:8888/docs       # View API documentation"
echo "  ./debug/fix_port_8888.sh             # Fix port 8888 issues"
echo ""
echo "💡 Pro Tips:"
echo "  - All shell scripts moved to scripts/"
echo "  - All test files moved to debug/"
echo "  - API now runs on port 8888 (changed from 8080)"
echo "  - Check PROJECT_ORGANIZATION.md for full details"
echo ""

# Check current API status
echo "🔍 Current API Status:"
if curl -s http://localhost:8888/health > /dev/null 2>&1; then
    echo "✅ API is running on port 8888"
    echo "   Health: $(curl -s http://localhost:8888/health | head -c 100)..."
else
    echo "❌ API not responding on port 8888"
    echo "   💡 Try: ./debug/test_port_8888.sh"
fi

echo ""
echo "📋 Requirements Files (Cleaned Up):"
echo "  requirements_enhanced.txt              # 🚀 Main API + Worker (PRIMARY)"
echo "  requirements_model_service_enhanced.txt # 🤖 ML Enhanced"
echo "  requirements_model_service_minimal.txt  # 🤖 ML Minimal"
echo "  requirements-dev.txt                   # 🛠️  Development tools"
echo ""
echo "📚 Documentation:"
echo "  PROJECT_ORGANIZATION.md - File reorganization details"
echo "  REQUIREMENTS_CLEANUP.md - Requirements cleanup details"
echo "  DOCKER_CLEANUP.md       - Docker files & container cleanup"
echo "  CLEANUP_SUMMARY.md      - Complete cleanup summary"
echo "  README_ENHANCED.md      - Project overview"
echo "  IMPLEMENTATION_SUMMARY.md - Technical details"
