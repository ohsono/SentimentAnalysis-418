#!/usr/bin/env python3

"""
Test script for DistilBERT Model Service
Tests /predict/llm and /predict/llm/batch endpoints
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8081"

def test_model_service_health():
    """Test the health endpoint"""
    print("🔍 Testing Model Service Health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        print(f"✅ Health Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Service: {health_data.get('service')}")
            print(f"   Model Manager: {health_data.get('model_manager_available')}")
            print(f"   Loaded Models: {health_data.get('loaded_models')}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_predict_llm():
    """Test the /predict/llm endpoint"""
    print("\n🤖 Testing /predict/llm endpoint...")
    
    test_cases = [
        "I love this new course at UCLA!",
        "This homework is really difficult and stressful.",
        "The weather is okay today."
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {text[:50]}...")
        
        try:
            request_data = {
                "text": text,
                "model": "distilbert-sentiment",
                "include_probabilities": True
            }
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/predict/llm",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Sentiment: {result.get('sentiment')}")
                print(f"   ✅ Confidence: {result.get('confidence', 0):.3f}")
                print(f"   ✅ Response Time: {response_time:.1f}ms")
                
                if result.get('probabilities'):
                    probs = result['probabilities']
                    print(f"   📊 Probabilities: +{probs.get('positive', 0):.2f} -{probs.get('negative', 0):.2f} ={probs.get('neutral', 0):.2f}")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    return True

def test_predict_llm_batch():
    """Test the /predict/llm/batch endpoint"""
    print("\n📦 Testing /predict/llm/batch endpoint...")
    
    test_texts = [
        "UCLA has an amazing campus and great professors!",
        "I'm feeling overwhelmed with all these assignments.",
        "The library is a good place to study.",
        "This class is incredibly challenging but rewarding.",
        "I can't wait for graduation!"
    ]
    
    try:
        request_data = {
            "texts": test_texts,
            "model": "distilbert-sentiment",
            "include_probabilities": True
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/predict/llm/batch",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            summary = result.get('summary', {})
            
            print(f"✅ Batch processing completed")
            print(f"✅ Total texts processed: {len(results)}")
            print(f"✅ Successful predictions: {summary.get('successful', 0)}")
            print(f"✅ Total processing time: {response_time:.1f}ms")
            print(f"✅ Average time per text: {summary.get('average_time_per_text_ms', 0):.1f}ms")
            
            # Show sentiment distribution
            sentiment_dist = summary.get('sentiment_distribution', {})
            print(f"📊 Sentiment Distribution:")
            print(f"   Positive: {sentiment_dist.get('positive', 0)}")
            print(f"   Negative: {sentiment_dist.get('negative', 0)}")
            print(f"   Neutral: {sentiment_dist.get('neutral', 0)}")
            
            # Show first few results
            print(f"\n📋 Sample Results:")
            for i, res in enumerate(results[:3]):
                text_preview = test_texts[i][:30] + "..." if len(test_texts[i]) > 30 else test_texts[i]
                print(f"   {i+1}. '{text_preview}' → {res.get('sentiment')} ({res.get('confidence', 0):.3f})")
            
            return True
        else:
            print(f"❌ Batch prediction failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in batch prediction: {e}")
        return False

def test_models_endpoint():
    """Test the models endpoint"""
    print("\n🔧 Testing /models endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/models", timeout=10)
        
        if response.status_code == 200:
            models_data = response.json()
            print(f"✅ Models endpoint working")
            print(f"   Available: {models_data.get('available')}")
            print(f"   Model Type: {models_data.get('model_type')}")
            print(f"   Loaded Models: {models_data.get('loaded_models')}")
            
            models = models_data.get('models', {})
            print(f"📋 Available Models:")
            for key, info in models.items():
                print(f"   - {key}: {info.get('description', 'No description')}")
            
            return True
        else:
            print(f"❌ Models endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing models endpoint: {e}")
        return False

def test_metrics_endpoint():
    """Test the metrics endpoint"""
    print("\n📈 Testing /metrics endpoint...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics_data = response.json()
            print(f"✅ Metrics endpoint working")
            
            predictions = metrics_data.get('predictions', {})
            performance = metrics_data.get('performance', {})
            
            print(f"📊 Performance Metrics:")
            print(f"   Successful predictions: {predictions.get('successful', 0)}")
            print(f"   Success rate: {predictions.get('success_rate', 0):.1%}")
            print(f"   Average processing time: {performance.get('average_processing_time_ms', 0):.1f}ms")
            print(f"   Requests per second: {performance.get('requests_per_second', 0):.2f}")
            
            return True
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing metrics endpoint: {e}")
        return False

def run_comprehensive_test():
    """Run all tests for the DistilBERT model service"""
    print("=" * 70)
    print("🤖 DistilBERT Model Service - Comprehensive Test Suite")
    print("=" * 70)
    
    # Run tests
    health_test = test_model_service_health()
    llm_test = test_predict_llm() if health_test else False
    batch_test = test_predict_llm_batch() if health_test else False
    models_test = test_models_endpoint() if health_test else False
    metrics_test = test_metrics_endpoint() if health_test else False
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   Health Check: {'✅ PASS' if health_test else '❌ FAIL'}")
    print(f"   /predict/llm: {'✅ PASS' if llm_test else '❌ FAIL'}")
    print(f"   /predict/llm/batch: {'✅ PASS' if batch_test else '❌ FAIL'}")
    print(f"   /models: {'✅ PASS' if models_test else '❌ FAIL'}")
    print(f"   /metrics: {'✅ PASS' if metrics_test else '❌ FAIL'}")
    print("=" * 70)
    
    if all([health_test, llm_test, batch_test]):
        print("🎉 All core tests passed! DistilBERT Model Service is working correctly.")
        print("\n💡 Example Usage:")
        print("   # Single prediction")
        print(f"   curl -X POST {API_BASE_URL}/predict/llm \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"text\": \"I love UCLA!\", \"model\": \"distilbert-sentiment\"}'")
        print("\n   # Batch prediction")
        print(f"   curl -X POST {API_BASE_URL}/predict/llm/batch \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"texts\": [\"Great course!\", \"Too much work\"], \"model\": \"distilbert-sentiment\"}'")
        print(f"\n   # API Documentation: {API_BASE_URL}/docs")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
        if not health_test:
            print("\n🔧 Model Service Issues:")
            print("   • Start service: python model_services/distilbert_service.py")
            print("   • Or with Docker: docker-compose up -d model-service-api")
            print("   • Check logs: docker logs ucla_model_service")
    
    return all([health_test, llm_test, batch_test])

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
