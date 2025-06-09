#!/usr/bin/env python3
import requests
import json
import time

def test_model_service():
    base_url = "http://localhost:8081"
    
    print("🧪 Testing UCLA Sentiment Analysis Model Service")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Service is healthy")
        else:
            print(f"⚠️ Service health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test prediction endpoint
    test_data = {
        "text": "UCLA is an amazing university!",
        "model_name": "vader",  # Start with VADER
        "return_confidence": True
    }
    
    try:
        print(f"\n🔮 Testing prediction with: '{test_data['text']}'")
        response = requests.post(
            f"{base_url}/predict", 
            json=test_data, 
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Prediction successful!")
            print(f"   Sentiment: {result.get('sentiment')}")
            print(f"   Confidence: {result.get('confidence')}")
            print(f"   Model: {result.get('model_used')}")
        else:
            print(f"❌ Prediction failed: {response.text}")
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")

if __name__ == "__main__":
    test_model_service()
