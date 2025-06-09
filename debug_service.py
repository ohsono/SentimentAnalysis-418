#!/usr/bin/env python3

"""
Debug UCLA Sentiment Analysis Service
Quick diagnostic to see what's wrong
"""

import requests
import subprocess
import os
import sys
import importlib.util

def check_port_8081():
    """Check what's running on port 8081"""
    print("🔍 Checking port 8081...")
    
    try:
        # Check if anything responds
        response = requests.get("http://localhost:8081/", timeout=5)
        print(f"✅ Service responding on port 8081 (status: {response.status_code})")
        
        # Try to get service info
        try:
            data = response.json()
            print(f"   Service: {data.get('service', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")
        except:
            print(f"   Response (first 200 chars): {response.text[:200]}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Nothing responding on port 8081")
        return False
    except Exception as e:
        print(f"❌ Error checking port 8081: {e}")
        return False

def test_current_service():
    """Test the current service with your original request"""
    print("\n🧪 Testing current service with original request...")
    
    test_data = {
        "text": "testtesttset",
        "model_name": "distilbert-sentiment",
        "return_confidence": True
    }
    
    try:
        response = requests.post(
            "http://localhost:8081/predict",
            json=test_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Original request now works!")
        else:
            print("❌ Original request still failing")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

def check_dependencies():
    """Check if required dependencies are available"""
    print("\n📦 Checking dependencies...")
    
    deps = {
        "requests": "for testing API",
        "nltk": "for VADER sentiment",
        "torch": "for transformer models",
        "transformers": "for HuggingFace models",
        "fastapi": "for API service",
        "uvicorn": "for running service"
    }
    
    for dep, description in deps.items():
        try:
            importlib.import_module(dep)
            print(f"✅ {dep} - {description}")
        except ImportError:
            print(f"❌ {dep} - {description} (MISSING)")

def check_processes():
    """Check what python processes are running"""
    print("\n🔍 Checking running Python processes...")
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        python_procs = [line for line in lines if 'python' in line.lower() and '8081' in line]
        
        if python_procs:
            print("Python processes using port 8081:")
            for proc in python_procs:
                print(f"   {proc}")
        else:
            print("No Python processes found using port 8081")
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")

def check_docker():
    """Check if Docker containers are running"""
    print("\n🐳 Checking Docker containers...")
    
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            if '8081' in result.stdout:
                print("Docker containers using port 8081:")
                lines = result.stdout.split('\n')
                for line in lines:
                    if '8081' in line:
                        print(f"   {line}")
            else:
                print("No Docker containers using port 8081")
        else:
            print("Docker not running or not accessible")
    except FileNotFoundError:
        print("Docker command not found")
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")

def test_vader_locally():
    """Test if VADER works locally"""
    print("\n🧪 Testing VADER locally...")
    
    try:
        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer
        
        # Try to find VADER
        try:
            nltk.data.find('vader_lexicon')
            print("✅ VADER lexicon found")
        except:
            print("⚠️ VADER lexicon not found, trying to download...")
            try:
                nltk.download('vader_lexicon', quiet=True)
                print("✅ VADER lexicon downloaded")
            except Exception as e:
                print(f"❌ Failed to download VADER: {e}")
                return
        
        # Test VADER
        analyzer = SentimentIntensityAnalyzer()
        test_text = "testtesttset"
        scores = analyzer.polarity_scores(test_text)
        
        print(f"✅ VADER works! Test text '{test_text}':")
        print(f"   Scores: {scores}")
        
        # Determine sentiment like the service would
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
            
        print(f"   Predicted sentiment: {sentiment}")
        
    except ImportError:
        print("❌ NLTK not available")
    except Exception as e:
        print(f"❌ VADER test failed: {e}")

def main():
    """Run all diagnostics"""
    print("🔧 UCLA Sentiment Analysis Service Diagnostics")
    print("=" * 50)
    
    # Check current state
    service_running = check_port_8081()
    
    if service_running:
        test_current_service()
    
    check_dependencies()
    check_processes()
    check_docker()
    test_vader_locally()
    
    print("\n💡 Next steps:")
    if not service_running:
        print("1. No service is running on port 8081")
        print("   Try: python3 -m model_services.fixed_model_service")
        print("   Or: python3 -m model_services.lightweight_model_service")
    else:
        print("1. Service is running - check the test results above")
        print("2. If it's still failing, try stopping and restarting:")
        print("   docker-compose down")
        print("   python3 -m model_services.fixed_model_service")

if __name__ == "__main__":
    main()
