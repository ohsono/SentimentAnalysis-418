#!/usr/bin/env python3

"""
Test script for the Worker API Service
This script tests the Reddit scraping functionality
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8082"

def test_api_health():
    """Test the health endpoint"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Service: {health_data.get('service')}")
            print(f"   Redis Status: {health_data.get('redis_status')}")
            print(f"   Worker Status: {health_data.get('worker_status')}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_scrape_info():
    """Test the scrape info endpoint (GET /scrape)"""
    print("\n🔍 Testing Scrape Info Endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/scrape")
        print(f"✅ Scrape Info Status: {response.status_code}")
        if response.status_code == 200:
            info_data = response.json()
            print(f"   Method: {info_data.get('method')}")
            print(f"   Description: {info_data.get('description')}")
            return True
        else:
            print(f"❌ Scrape info failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_reddit_scraping(subreddit="python", post_limit=3):
    """Test Reddit scraping functionality"""
    print(f"\n🚀 Testing Reddit Scraping (r/{subreddit})...")
    
    # Prepare the request data
    scrape_request = {
        "subreddit": subreddit,
        "post_limit": post_limit,
        "comment_limit": 2,
        "sort_by": "hot",
        "time_filter": "week"
    }
    
    try:
        # Submit scraping task
        print(f"📤 Submitting scraping task...")
        response = requests.post(
            f"{API_BASE_URL}/scrape",
            json=scrape_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"✅ Scrape Submission Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"   Task ID: {task_id}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            
            # Check task status
            if task_id:
                print(f"\n🔍 Checking task status...")
                time.sleep(2)  # Wait a bit
                
                status_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Task Status: {status_data.get('status')}")
                    print(f"   Message: {status_data.get('message')}")
                    
                    if status_data.get('result'):
                        print(f"   Result: {json.dumps(status_data.get('result'), indent=2)}")
                else:
                    print(f"❌ Failed to get task status: {status_response.text}")
            
            return True
        else:
            print(f"❌ Scraping failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_list_tasks():
    """Test listing tasks"""
    print(f"\n📋 Testing Task List...")
    try:
        response = requests.get(f"{API_BASE_URL}/tasks")
        print(f"✅ Task List Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            tasks = result.get("tasks", [])
            print(f"   Total tasks shown: {result.get('total_shown', 0)}")
            print(f"   Redis connected: {result.get('redis_connected')}")
            
            for i, task in enumerate(tasks[:3]):  # Show first 3 tasks
                print(f"   Task {i+1}: {task.get('task_id', 'Unknown')} - {task.get('status', 'Unknown')}")
            
            return True
        else:
            print(f"❌ Task list failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 UCLA Sentiment Analysis - Worker API Test Suite")
    print("=" * 60)
    
    # Run tests
    health_ok = test_api_health()
    info_ok = test_scrape_info()
    
    if health_ok and info_ok:
        scrape_ok = test_reddit_scraping()
        list_ok = test_list_tasks()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print(f"   Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"   Scrape Info: {'✅ PASS' if info_ok else '❌ FAIL'}")
        print(f"   Reddit Scraping: {'✅ PASS' if scrape_ok else '❌ FAIL'}")
        print(f"   Task List: {'✅ PASS' if list_ok else '❌ FAIL'}")
        print("=" * 60)
        
        if all([health_ok, info_ok, scrape_ok, list_ok]):
            print("🎉 All tests passed! Worker API is functioning correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
    else:
        print("\n❌ Basic connectivity tests failed. Is the worker service running?")
        print("💡 Try running: docker-compose up -d")
        print("💡 Or: python run_worker_local.py")

if __name__ == "__main__":
    main()
