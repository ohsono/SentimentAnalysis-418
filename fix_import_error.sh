#!/bin/bash

# Import Error Fix Script
# Fixes the get_setting import error and tests the solution

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Import Error Fix Script${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "${YELLOW}🔍 Problem Identified:${NC}"
echo -e "   ImportError: cannot import name 'get_setting' from 'app.utils.config'"
echo -e "   The 'get_setting' function doesn't exist in config.py"

echo -e "\n${YELLOW}🔧 Applying Fix:${NC}"
echo -e "   ✅ Removed 'get_setting' import from app/utils/__init__.py"
echo -e "   ✅ Updated __all__ list to exclude 'get_setting'"

echo -e "\n${BLUE}🧪 Testing the fix...${NC}"

# Test Python imports
if python3 test_imports.py; then
    echo -e "\n${GREEN}✅ Import fix successful!${NC}"
    
    echo -e "\n${BLUE}🚀 Your application should now start properly.${NC}"
    echo -e "\n${YELLOW}💡 Quick Start Commands:${NC}"
    echo -e "   # Start all services"
    echo -e "   ${GREEN}docker-compose up -d${NC}"
    echo -e ""
    echo -e "   # Or start individual services:"
    echo -e "   ${GREEN}docker-compose up -d postgres redis${NC}"
    echo -e "   ${GREEN}python run_distilbert_service.py${NC}      # Model service"
    echo -e "   ${GREEN}python run_worker_local.py${NC}           # Worker service" 
    echo -e "   ${GREEN}python -m app.api.main_enhanced${NC}      # Gateway API"
    
    echo -e "\n${BLUE}📊 Test All Services:${NC}"
    echo -e "   ${GREEN}python test_comprehensive.py${NC}         # Full system test"
    echo -e "   ${GREEN}python test_distilbert_service.py${NC}    # Model service test"
    echo -e "   ${GREEN}python test_worker_api.py${NC}            # Worker service test"
    
    echo -e "\n${BLUE}🌐 Service Endpoints (once running):${NC}"
    echo -e "   • Gateway API: http://localhost:8080/docs"
    echo -e "   • Model Service: http://localhost:8081/docs" 
    echo -e "   • Worker Service: http://localhost:8082/docs"
    echo -e "   • Dashboard: http://localhost:8501"
    
    echo -e "\n${GREEN}🎉 Import issues resolved! You can now start your UCLA Sentiment Analysis system.${NC}"
    
else
    echo -e "\n${RED}❌ Import test failed. There may be additional issues.${NC}"
    
    echo -e "\n${YELLOW}🔧 Additional Troubleshooting:${NC}"
    echo -e "   1. Check Python path: ${GREEN}export PYTHONPATH=\$PWD${NC}"
    echo -e "   2. Install dependencies: ${GREEN}pip install -r requirements_enhanced.txt${NC}"
    echo -e "   3. Check for missing files in app/utils/"
    echo -e "   4. Verify all Docker containers are stopped: ${GREEN}docker-compose down${NC}"
    
    echo -e "\n${BLUE}📝 Manual Import Test:${NC}"
    echo -e "   Try this in Python:"
    echo -e "   ${YELLOW}>>> from app.utils import load_config${NC}"
    echo -e "   ${YELLOW}>>> from app.api.main_enhanced import app${NC}"
    
    exit 1
fi

echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}  Import Fix Complete${NC}"
echo -e "${BLUE}============================================${NC}"
