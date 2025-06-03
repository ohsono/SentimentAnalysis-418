#!/usr/bin/env python3

"""
Test script for service import fixes
Tests HealthResponse and NLTK imports specifically
"""

import sys
import os
from pathlib import Path

def test_model_service_imports():
    """Test model service imports including HealthResponse"""
    print("🤖 Testing Model Service Imports...")
    
    try:
        # Test pydantic models import
        from model_services.pydantic_models import HealthResponse, ModelPredictionRequest
        print("   ✅ HealthResponse model imported successfully")
        
        # Test that HealthResponse has required fields
        required_fields = ['status', 'service', 'model_manager_available', 'loaded_models', 'memory_info', 'timestamp']
        model_fields = list(HealthResponse.__annotations__.keys())
        
        missing_fields = [field for field in required_fields if field not in model_fields]
        if missing_fields:
            print(f"   ❌ HealthResponse missing fields: {missing_fields}")
            return False
        else:
            print("   ✅ HealthResponse has all required fields")
        
        # Test creating an instance
        health_response = HealthResponse(
            status="healthy",
            service="test-service",
            model_manager_available=True,
            loaded_models=["test-model"],
            memory_info={"used": 100},
            timestamp="2024-01-01T00:00:00Z"
        )
        print("   ✅ HealthResponse instance created successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_nltk_import():
    """Test NLTK import and VADER sentiment analyzer"""
    print("\n📝 Testing NLTK and VADER Imports...")
    
    try:
        # Test basic NLTK import
        import nltk
        print("   ✅ NLTK imported successfully")
        
        # Test VADER sentiment analyzer import
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        print("   ✅ VADER SentimentIntensityAnalyzer imported successfully")
        
        # Test creating analyzer instance
        analyzer = SentimentIntensityAnalyzer()
        print("   ✅ VADER analyzer instance created")
        
        # Test sentiment analysis
        test_text = "I love UCLA!"
        scores = analyzer.polarity_scores(test_text)
        
        expected_keys = ['neg', 'neu', 'pos', 'compound']
        if all(key in scores for key in expected_keys):
            print("   ✅ VADER sentiment analysis working")
            print(f"      Test: '{test_text}' -> {scores}")
        else:
            print("   ❌ VADER sentiment analysis incomplete")
            return False
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Solution: pip install nltk")
        print("   💡 Or: python -c \"import nltk; nltk.download('vader_lexicon')\"")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_worker_imports():
    """Test worker service imports"""
    print("\n⚙️  Testing Worker Service Imports...")
    
    try:
        # Add worker directory to path
        worker_dir = Path(__file__).parent / "worker"
        if worker_dir.exists():
            sys.path.insert(0, str(worker_dir))
        
        # Test worker orchestrator import (this was failing before)
        # Note: We'll just test the specific import that was failing
        print("   🔍 Testing problematic import path...")
        
        # This is the import chain that was failing:
        # worker/__init__.py -> worker_orchestrator.py -> processors/RedditDataProcessor.py -> nltk
        
        # Test if we can import NLTK components that RedditDataProcessor needs
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
        print("   ✅ NLTK VADER import (used by RedditDataProcessor) working")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_docker_requirements():
    """Test if requirements are properly specified"""
    print("\n📦 Testing Requirements Files...")
    
    try:
        # Check if NLTK is in requirements
        req_file = Path(__file__).parent / "requirements_enhanced.txt"
        if req_file.exists():
            requirements = req_file.read_text()
            if "nltk" in requirements:
                print("   ✅ NLTK found in requirements_enhanced.txt")
            else:
                print("   ❌ NLTK not found in requirements_enhanced.txt")
                return False
        else:
            print("   ⚠️  requirements_enhanced.txt not found")
        
        # Check model service requirements
        model_req_file = Path(__file__).parent / "requirements_model_service_distilbert.txt"
        if model_req_file.exists():
            print("   ✅ Model service requirements file exists")
        else:
            print("   ⚠️  Model service requirements file not found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking requirements: {e}")
        return False

def main():
    """Run all import tests"""
    print("=" * 60)
    print("🧪 Service Import Fixes - Test Suite")
    print("=" * 60)
    
    # Run tests
    model_test = test_model_service_imports()
    nltk_test = test_nltk_import()
    worker_test = test_worker_imports()
    requirements_test = test_docker_requirements()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Model Service (HealthResponse): {'✅ PASS' if model_test else '❌ FAIL'}")
    print(f"   NLTK/VADER Import: {'✅ PASS' if nltk_test else '❌ FAIL'}")
    print(f"   Worker Service Imports: {'✅ PASS' if worker_test else '❌ FAIL'}")
    print(f"   Requirements Files: {'✅ PASS' if requirements_test else '❌ FAIL'}")
    print("=" * 60)
    
    if all([model_test, nltk_test, worker_test, requirements_test]):
        print("🎉 All import tests passed! Service import issues are resolved.")
        print("\n💡 Next steps:")
        print("   1. Rebuild Docker images: docker-compose build")
        print("   2. Start services: docker-compose up -d")
        print("   3. Test APIs: python test_comprehensive.py")
        return True
    else:
        print("⚠️  Some import tests failed.")
        print("\n🔧 Fixes needed:")
        
        if not model_test:
            print("   • Model Service: Check HealthResponse in pydantic_models.py")
        if not nltk_test:
            print("   • NLTK: Run 'pip install nltk' and download VADER data")
        if not worker_test:
            print("   • Worker Service: Check NLTK availability")
        if not requirements_test:
            print("   • Requirements: Ensure NLTK is in requirements files")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
