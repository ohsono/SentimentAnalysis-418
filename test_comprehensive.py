#!/usr/bin/env python3

"""
Comprehensive test script for UCLA Sentiment Analysis
Tests both database connectivity and worker API functionality
"""

import requests
import json
import time
import psycopg2
import os
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8082"
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'sentiment_db',
    'user': 'sentiment_user',
    'password': 'sentiment_password'
}

def test_database_connection():
    """Test PostgreSQL database connection and schema"""
    print("🔍 Testing Database Connection...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Database connected: {version[:50]}...")
        
        # Check if required tables exist
        tables_to_check = [
            'sentiment_analysis_results',
            'sentiment_alerts', 
            'reddit_posts',
            'reddit_comments',
            'system_metrics',
            'analytics_cache'
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Found {len(existing_tables)} tables in database")
        
        missing_tables = [table for table in tables_to_check if table not in existing_tables]
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("✅ All required tables exist")
        
        # Test configuration data
        cursor.execute("SELECT cache_key FROM analytics_cache WHERE cache_key = 'system_config';")
        if cursor.fetchone():
            print("✅ System configuration found in analytics_cache")
        else:
            print("⚠️  System configuration not found")
        
        # Show table row counts
        print("\n📈 Table Row Counts:")
        for table in existing_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} rows")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_worker_api():
    """Test worker API endpoints"""
    print("\n🔍 Testing Worker API...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   Redis Status: {health_data.get('redis_status')}")
            print(f"   Worker Status: {health_data.get('worker_status')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test GET /scrape endpoint
        response = requests.get(f"{API_BASE_URL}/scrape", timeout=10)
        if response.status_code == 200:
            print("✅ GET /scrape endpoint working")
        else:
            print(f"❌ GET /scrape failed: {response.status_code}")
            return False
        
        # Test POST /scrape endpoint with a small request
        print("\n🚀 Testing Reddit scraping...")
        scrape_request = {
            "subreddit": "test",
            "post_limit": 2,
            "comment_limit": 1,
            "sort_by": "hot"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/scrape",
            json=scrape_request,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ Scraping task submitted successfully")
            print(f"   Task ID: {task_id}")
            print(f"   Status: {result.get('status')}")
            
            # Check task status
            if task_id:
                time.sleep(2)  # Wait a bit
                status_response = requests.get(f"{API_BASE_URL}/tasks/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Task Status: {status_data.get('status')}")
                    print("✅ Task status endpoint working")
                else:
                    print(f"⚠️  Task status check failed: {status_response.status_code}")
        else:
            print(f"❌ Scraping request failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return False
        
        # Test tasks list endpoint
        response = requests.get(f"{API_BASE_URL}/tasks", timeout=10)
        if response.status_code == 200:
            tasks_data = response.json()
            print(f"✅ Tasks list endpoint working")
            print(f"   Total tasks shown: {tasks_data.get('total_shown', 0)}")
        else:
            print(f"❌ Tasks list failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to worker API. Is it running?")
        print("💡 Start it with: python run_worker_local.py")
        return False
    except Exception as e:
        print(f"❌ Worker API test failed: {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible"""
    print("\n📚 Testing API Documentation...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API documentation accessible at /docs")
            return True
        else:
            print(f"⚠️  API docs not accessible: {response.status_code}")
            return False
    except:
        print("⚠️  API docs not accessible")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("=" * 70)
    print("🧪 UCLA Sentiment Analysis - Comprehensive Test Suite")
    print("=" * 70)
    
    # Run tests
    db_test = test_database_connection()
    api_test = test_worker_api()
    docs_test = test_api_docs()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary:")
    print(f"   Database Connection: {'✅ PASS' if db_test else '❌ FAIL'}")
    print(f"   Worker API: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"   API Documentation: {'✅ PASS' if docs_test else '❌ FAIL'}")
    print("=" * 70)
    
    if all([db_test, api_test]):
        print("🎉 All critical tests passed! System is ready for Reddit scraping.")
        print("\n💡 Quick Start Commands:")
        print("   • Submit a scraping task:")
        print(f"     curl -X POST {API_BASE_URL}/scrape -H 'Content-Type: application/json' \\")
        print("       -d '{\"subreddit\": \"UCLA\", \"post_limit\": 5}'")
        print("   • View API docs:")
        print(f"     Open {API_BASE_URL}/docs in your browser")
        print("   • Check system health:")
        print(f"     curl {API_BASE_URL}/health")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
        if not db_test:
            print("\n🔧 Database Issues:")
            print("   • Run: ./fix_all_issues.sh")
            print("   • Or: docker-compose up -d postgres")
            
        if not api_test:
            print("\n🔧 Worker API Issues:")
            print("   • Start worker: python run_worker_local.py")
            print("   • Or start all services: docker-compose up -d")
    
    return all([db_test, api_test])

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)
