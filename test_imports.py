#!/usr/bin/env python3

"""
Test script to verify import fixes
Tests all the main application imports to catch any issues
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def test_imports():
    """Test all critical imports"""
    print("🧪 Testing application imports...")
    
    try:
        # Test utils imports
        print("   Testing app.utils imports...")
        from app.utils import load_config, setup_logging, clean_text, format_datetime, calculate_sentiment_category
        print("   ✅ app.utils imports successful")
        
        # Test config module
        print("   Testing app.utils.config...")
        from app.utils.config import load_config
        config = load_config()
        print(f"   ✅ Config loaded: {config['app']['name']}")
        
        # Test service health
        print("   Testing app.utils.service_health...")
        from app.utils.service_health import check_service_health, check_all_services
        print("   ✅ Service health imports successful")
        
        # Test API imports (this was failing before)
        print("   Testing app.api imports...")
        from app.api.pydantic_models import SentimentRequest, SentimentResponse
        print("   ✅ Pydantic models imports successful")
        
        # Test the main API module (this should work now)
        print("   Testing main API module...")
        os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")
        from app.api.main_enhanced import app
        print("   ✅ Main API module imported successfully")
        
        print("\n🎉 All imports successful! The fix worked.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if all required files exist")
        print("2. Verify Python path configuration")
        print("3. Check for circular imports")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def test_config_functions():
    """Test configuration functions"""
    print("\n🔧 Testing configuration functions...")
    
    try:
        from app.utils.config import load_config
        
        # Test with no file
        config = load_config()
        print(f"   ✅ Default config loaded: {len(config)} sections")
        
        # Test with environment variables
        os.environ["API_HOST"] = "test_host"
        os.environ["API_PORT"] = "9999"
        config = load_config()
        
        assert config["api"]["host"] == "test_host"
        assert config["api"]["port"] == 9999
        print("   ✅ Environment variable overrides working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config test failed: {e}")
        return False

def test_helper_functions():
    """Test helper functions"""
    print("\n🛠️  Testing helper functions...")
    
    try:
        from app.utils.helpers import clean_text, format_datetime, calculate_sentiment_category
        from datetime import datetime, timezone
        
        # Test clean_text
        dirty_text = "Check out this link: https://example.com **bold text** and some `code`"
        clean = clean_text(dirty_text)
        print(f"   ✅ Text cleaning: '{dirty_text[:30]}...' -> '{clean[:30]}...'")
        
        # Test format_datetime
        now = datetime.now(timezone.utc)
        formatted = format_datetime(now)
        print(f"   ✅ Date formatting: {formatted}")
        
        # Test calculate_sentiment_category
        assert calculate_sentiment_category(0.1) == "positive"
        assert calculate_sentiment_category(-0.1) == "negative"
        assert calculate_sentiment_category(0.0) == "neutral"
        print("   ✅ Sentiment categorization working")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Helper test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🔍 Import Fix Verification Test")
    print("=" * 60)
    
    # Run tests
    imports_ok = test_imports()
    config_ok = test_config_functions()
    helpers_ok = test_helper_functions()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Config: {'✅ PASS' if config_ok else '❌ FAIL'}")
    print(f"   Helpers: {'✅ PASS' if helpers_ok else '❌ FAIL'}")
    print("=" * 60)
    
    if all([imports_ok, config_ok, helpers_ok]):
        print("🎉 All tests passed! Import issues are resolved.")
        print("\n💡 You can now start the services:")
        print("   • Gateway API: python -m app.api.main_enhanced")
        print("   • Or with Docker: docker-compose up -d gateway-api")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
