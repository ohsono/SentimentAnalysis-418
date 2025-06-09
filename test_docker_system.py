#!/usr/bin/env python3

"""
Test Script for Deployed UCLA Sentiment Analysis Docker System
Tests all services in the deployed Docker environment
"""

import requests
import json
import time
import sys

def test_service_health(service_name, url, timeout=10):
    """Test service health endpoint"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            print(f"   ✅ {service_name}: Healthy")
            return True
        else:
            print(f"   ❌ {service_name}: Unhealthy (status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ {service_name}: Connection failed - {e}")
        return False

def test_model_service():
    """Test model service functionality"""
    print("\n🤖 Testing Model Service (Port 8081)")
    print("-" * 40)
    
    base_url = "http://localhost:8081"
    
    # Test 1: Health check
    if not test_service_health("Model Service", base_url):
        return False
    
    # Test 2: Your original request
    print("\n   Testing your original request...")
    test_data = {
        "text": "testtesttset",
        "model_name": "vader", 
        "return_confidence": True
    }
    
    try:
        response = requests.post(f"{base_url}/predict", json=test_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Original request successful!")
            print(f"      Sentiment: {result.get('sentiment')}")
            print(f"      Confidence: {result.get('confidence')}")
            print(f"      Model: {result.get('model_used')}")
            return True
        else:
            print(f"   ❌ Original request failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Original request failed: {e}")
        return False

def test_gateway_service():
    """Test gateway service functionality"""
    print("\n🌐 Testing Gateway Service (Port 8080)")
    print("-" * 40)
    
    base_url = "http://localhost:8080"
    
    # Test 1: Health check
    if not test_service_health("Gateway Service", base_url):
        return False
    
    # Test 2: Prediction through gateway
    print("\n   Testing prediction through gateway...")
    test_data = {
        "text": "UCLA is an amazing university!",
        "include_probabilities": True
    }
    
    try:
        response = requests.post(f"{base_url}/predict", json=test_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Gateway prediction successful!")
            print(f"      Sentiment: {result.get('sentiment')}")
            print(f"      Confidence: {result.get('confidence')}")
            return True
        else:
            print(f"   ❌ Gateway prediction failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Gateway prediction failed: {e}")
        return False

def test_worker_service():
    """Test worker service functionality"""
    print("\n👷 Testing Worker Service (Port 8082)")
    print("-" * 40)
    
    base_url = "http://localhost:8082"
    
    # Test 1: Health check
    if not test_service_health("Worker Service", base_url):
        return False
    
    # Test 2: List tasks
    print("\n   Testing task listing...")
    try:
        response = requests.get(f"{base_url}/tasks", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Task listing successful!")
            print(f"      Tasks shown: {result.get('total_shown', 0)}")
            return True
        else:
            print(f"   ❌ Task listing failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Task listing failed: {e}")
        return False

def test_dashboard_service():
    """Test dashboard service"""
    print("\n📈 Testing Dashboard Service (Port 8501)")
    print("-" * 40)
    
    try:
        response = requests.get("http://localhost:8501", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Dashboard: Accessible")
            return True
        else:
            print(f"   ❌ Dashboard: Not accessible (status: {response.status_code})")
            return False
    except Exception as e:
        print(f"   ❌ Dashboard: Connection failed - {e}")
        return False

def test_complete_pipeline():
    """Test the complete sentiment analysis pipeline"""
    print("\n🔄 Testing Complete Pipeline")
    print("-" * 40)
    
    # Test through gateway (complete pipeline)
    print("\n   Testing complete pipeline through gateway...")
    
    test_cases = [
        {"text": "UCLA is the best university!", "expected": "positive"},
        {"text": "I hate this assignment so much", "expected": "negative"},
        {"text": "The weather is okay today", "expected": "neutral"}
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            response = requests.post(
                "http://localhost:8080/predict", 
                json={"text": test_case["text"], "include_probabilities": True},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                sentiment = result.get('sentiment')
                confidence = result.get('confidence', 0)
                
                print(f"   Test {i}: '{test_case['text'][:30]}...'")
                print(f"           → {sentiment} (confidence: {confidence:.3f})")
                
                if sentiment == test_case["expected"]:
                    print(f"           ✅ Expected sentiment detected")
                    success_count += 1
                else:
                    print(f"           ⚠️ Expected {test_case['expected']}, got {sentiment}")
                    success_count += 0.5  # Partial credit
            else:
                print(f"   Test {i}: ❌ Failed - {response.status_code}")
                
        except Exception as e:
            print(f"   Test {i}: ❌ Error - {e}")
    
    success_rate = success_count / len(test_cases)
    print(f"\n   Pipeline success rate: {success_rate:.1%}")
    
    return success_rate > 0.5

def main():
    """Main test function"""
    print("🧪 UCLA Sentiment Analysis - Docker System Test")
    print("=" * 60)
    print("Testing deployed Docker services...")
    
    # Wait for services to be fully ready
    print("\n⏳ Waiting for services to be ready...")
    time.sleep(5)
    
    results = {}
    
    # Test all services
    results['model'] = test_model_service()
    results['gateway'] = test_gateway_service()
    results['worker'] = test_worker_service()
    results['dashboard'] = test_dashboard_service()
    results['pipeline'] = test_complete_pipeline()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name.title()} Service: {status}")
    
    print(f"\n🎯 Overall Score: {passed}/{total} ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("   Your UCLA Sentiment Analysis system is fully operational!")
        print("\n🔗 Service URLs:")
        print("   📊 Gateway API:    http://localhost:8080")
        print("   📚 API Docs:       http://localhost:8080/docs") 
        print("   🤖 Model Service:  http://localhost:8081")
        print("   👷 Worker Service: http://localhost:8082")
        print("   📈 Dashboard:      http://localhost:8501")
        
        print("\n✨ Your original request now works:")
        print("   curl -X POST 'http://localhost:8081/predict' \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"text\": \"testtesttset\", \"model_name\": \"vader\", \"return_confidence\": true}'")
        
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        print("   Check service logs with: docker-compose -f docker-compose.fixed.yml logs -f")
        print("   Some services may still be starting up. Wait a few minutes and retry.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
