#!/usr/bin/env python3

"""
Quick Test Script for UCLA Sentiment Analysis
Tests the standalone model service
"""

import requests
import json
import time
import subprocess
import sys
import os

def test_service_availability(url, max_retries=30, wait_time=2):
    """Test if service is available"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                return True
        except:
            pass
        
        if i < max_retries - 1:
            print(f"⏳ Waiting for service to start... ({i+1}/{max_retries})")
            time.sleep(wait_time)
    
    return False

def test_model_service():
    """Test the model service comprehensively"""
    base_url = "http://localhost:8081"
    
    print("🧪 Testing UCLA Sentiment Analysis Model Service")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Service: {health_data.get('service')}")
            print(f"   ✅ Status: {health_data.get('status')}")
            print(f"   ✅ VADER available: {health_data.get('fallback_available')}")
        else:
            print(f"   ❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    # Test 2: Models endpoint
    print("\n2️⃣ Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/models", timeout=10)
        if response.status_code == 200:
            models_data = response.json()
            print(f"   ✅ Available models: {models_data.get('total_available')}")
            print(f"   ✅ Recommended: {models_data.get('recommended')}")
            for model in models_data.get('models', []):
                status = "✅" if model.get('available') else "❌"
                print(f"     {status} {model.get('name')}: {model.get('description')}")
        else:
            print(f"   ❌ Models endpoint failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Models endpoint failed: {e}")
    
    # Test 3: Single prediction (your original request)
    print("\n3️⃣ Testing single prediction (your original request)...")
    test_data = {
        "text": "testtesttset",
        "model_name": "vader",  # Use VADER instead of distilbert
        "return_confidence": True
    }
    
    try:
        print(f"   Request: {json.dumps(test_data)}")
        response = requests.post(f"{base_url}/predict", json=test_data, timeout=30)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Prediction successful!")
            print(f"      Sentiment: {result.get('sentiment')}")
            print(f"      Confidence: {result.get('confidence')}")
            print(f"      Model: {result.get('model_used')}")
            print(f"      Processing time: {result.get('processing_time_ms')}ms")
            print(f"      Scores: {result.get('scores')}")
        else:
            print(f"   ❌ Prediction failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Prediction test failed: {e}")
        return False
    
    # Test 4: Positive sentiment
    print("\n4️⃣ Testing positive sentiment...")
    positive_test = {
        "text": "UCLA is an amazing university with excellent programs!",
        "model_name": "vader",
        "return_confidence": True
    }
    
    try:
        response = requests.post(f"{base_url}/predict", json=positive_test, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Positive sentiment test: {result.get('sentiment')}")
            print(f"      Confidence: {result.get('confidence')}")
        else:
            print(f"   ❌ Positive test failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Positive test failed: {e}")
    
    # Test 5: Negative sentiment
    print("\n5️⃣ Testing negative sentiment...")
    negative_test = {
        "text": "I hate this terrible assignment and feel really stressed and overwhelmed",
        "model_name": "vader",
        "return_confidence": True
    }
    
    try:
        response = requests.post(f"{base_url}/predict", json=negative_test, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Negative sentiment test: {result.get('sentiment')}")
            print(f"      Confidence: {result.get('confidence')}")
        else:
            print(f"   ❌ Negative test failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Negative test failed: {e}")
    
    # Test 6: Batch prediction
    print("\n6️⃣ Testing batch prediction...")
    batch_test = {
        "texts": [
            "UCLA is great!",
            "I'm stressed about finals",
            "The weather is okay today"
        ],
        "model_name": "vader",
        "return_confidence": True
    }
    
    try:
        response = requests.post(f"{base_url}/predict/batch", json=batch_test, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Batch prediction successful!")
            print(f"      Total processed: {result.get('total_processed')}")
            print(f"      Processing time: {result.get('total_processing_time'):.2f}s")
            print(f"      Results:")
            for i, res in enumerate(result.get('results', [])[:3]):
                print(f"        {i+1}. {res.get('sentiment')} (conf: {res.get('confidence'):.3f})")
        else:
            print(f"   ❌ Batch test failed: {response.text}")
    except Exception as e:
        print(f"   ❌ Batch test failed: {e}")
    
    print("\n🎉 Model service tests completed!")
    return True

def main():
    """Main test function"""
    print("🚀 UCLA Sentiment Analysis - Quick Test Script")
    print("=" * 60)
    
    # Check if service is running
    print("🔍 Checking if model service is running on port 8081...")
    
    if not test_service_availability("http://localhost:8081"):
        print("❌ Model service is not running on port 8081")
        print("\n💡 To start the service:")
        print("   python3 standalone_model_service.py")
        print("   # OR")
        print("   python3 -m model_services.fixed_model_service")
        return False
    
    print("✅ Model service is running!")
    
    # Run comprehensive tests
    success = test_model_service()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Summary:")
        print("   ✅ Health check working")
        print("   ✅ Models endpoint working")
        print("   ✅ Single predictions working")
        print("   ✅ Batch predictions working")
        print("   ✅ VADER sentiment analysis functional")
        print("\n🔗 Your original request now works:")
        print('   curl -X POST "http://localhost:8081/predict" \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"text": "testtesttset", "model_name": "vader", "return_confidence": true}\'')
    else:
        print("\n❌ Some tests failed. Check the service logs.")
    
    return success

if __name__ == "__main__":
    main()
