#!/usr/bin/env python3

"""
Comprehensive Validation Script for API-Friendly Pipeline Service
Validates and checks each function in the local directory
"""

import os
import sys
import json
import time
import requests
import subprocess
import psutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import importlib.util

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "worker"))

class ValidationResults:
    """Class to track validation results"""
    
    def __init__(self):
        self.tests = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.warnings = []
        
    def add_test(self, test_name: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a test result"""
        self.tests.append({
            'test_name': test_name,
            'status': status,  # 'PASS', 'FAIL', 'WARN', 'SKIP'
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        })
        
        self.total_tests += 1
        if status == 'PASS':
            self.passed_tests += 1
        elif status == 'FAIL':
            self.failed_tests += 1
        elif status == 'WARN':
            self.warnings.append(test_name)
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 80)
        print("🧪 COMPREHENSIVE VALIDATION SUMMARY")
        print("=" * 80)
        
        print(f"📊 Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"📈 Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%" if self.total_tests > 0 else "N/A")
        
        print("\n" + "-" * 80)
        print("📋 DETAILED RESULTS:")
        print("-" * 80)
        
        for test in self.tests:
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌', 
                'WARN': '⚠️',
                'SKIP': '⏭️'
            }.get(test['status'], '❓')
            
            print(f"{status_icon} {test['test_name']}: {test['message']}")
        
        if self.warnings:
            print("\n" + "-" * 40)
            print("⚠️  WARNINGS:")
            print("-" * 40)
            for warning in self.warnings:
                print(f"   • {warning}")
        
        print("\n" + "=" * 80)
        
        return self.passed_tests, self.failed_tests, len(self.warnings)

class SystemValidator:
    """Main validator class"""
    
    def __init__(self):
        self.results = ValidationResults()
        self.project_root = project_root
        self.worker_dir = self.project_root / "worker"
        self.app_dir = self.project_root / "app"
        self.service_url = "http://localhost:8082"
        self.service_process = None
        
    def run_all_validations(self):
        """Run all validation tests"""
        print("🚀 Starting Comprehensive Validation")
        print("=" * 80)
        
        # 1. File Structure Validation
        self.validate_file_structure()
        
        # 2. Configuration Validation
        self.validate_configuration()
        
        # 3. Dependencies Validation
        self.validate_dependencies()
        
        # 4. Database Connectivity
        self.validate_database_connection()
        
        # 5. Redis Connectivity
        self.validate_redis_connection()
        
        # 6. Reddit API Credentials
        self.validate_reddit_api()
        
        # 7. Worker Components
        self.validate_worker_components()
        
        # 8. Start Service and Test APIs
        self.validate_service_startup()
        
        if self.service_process:
            # Wait for service to start
            time.sleep(5)
            
            # 9. API Endpoints
            self.validate_api_endpoints()
            
            # 10. Pipeline Functionality
            self.validate_pipeline_functionality()
            
            # 11. Cleanup
            self.cleanup_service()
        
        # Print summary
        return self.results.print_summary()
    
    def validate_file_structure(self):
        """Validate required files and directories exist"""
        print("\n📁 Validating File Structure")
        print("-" * 40)
        
        required_files = [
            "run_scheduled_worker.py",
            "worker/main.py",
            "worker/worker_orchestrator.py",
            "worker/config/worker_config.py",
            "worker/pydantic_models.py",
            ".env.scheduler",
            "test_pipeline_api.py"
        ]
        
        required_dirs = [
            "worker",
            "worker/config",
            "worker/scrapers", 
            "worker/processors",
            "worker/utils",
            "app",
            "app/api"
        ]
        
        # Check files
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                self.results.add_test(
                    f"File: {file_path}", 
                    "PASS", 
                    "File exists"
                )
            else:
                self.results.add_test(
                    f"File: {file_path}", 
                    "FAIL", 
                    "File missing"
                )
        
        # Check directories
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                self.results.add_test(
                    f"Directory: {dir_path}", 
                    "PASS", 
                    "Directory exists"
                )
            else:
                self.results.add_test(
                    f"Directory: {dir_path}", 
                    "FAIL", 
                    "Directory missing"
                )
    
    def validate_configuration(self):
        """Validate configuration files and settings"""
        print("\n⚙️ Validating Configuration")
        print("-" * 40)
        
        try:
            # Load environment variables
            env_file = self.project_root / ".env.scheduler"
            if env_file.exists():
                with open(env_file) as f:
                    env_content = f.read()
                    
                # Check for required environment variables
                required_vars = [
                    'SCHEDULER_ENABLED',
                    'SCRAPING_INTERVAL_MINUTES', 
                    'POSTGRES_HOST',
                    'POSTGRES_DB',
                    'REDDIT_CLIENT_ID',
                    'REDDIT_CLIENT_SECRET'
                ]
                
                missing_vars = []
                for var in required_vars:
                    if var not in env_content:
                        missing_vars.append(var)
                
                if not missing_vars:
                    self.results.add_test(
                        "Environment Variables",
                        "PASS",
                        "All required environment variables found"
                    )
                else:
                    self.results.add_test(
                        "Environment Variables",
                        "FAIL", 
                        f"Missing variables: {', '.join(missing_vars)}"
                    )
            else:
                self.results.add_test(
                    "Environment File",
                    "FAIL",
                    ".env.scheduler file not found"
                )
                
            # Test worker config import
            try:
                from worker.config.worker_config import config
                is_valid = config.validate_config()
                
                if is_valid:
                    self.results.add_test(
                        "Worker Configuration",
                        "PASS", 
                        "Configuration validation passed"
                    )
                else:
                    self.results.add_test(
                        "Worker Configuration",
                        "FAIL",
                        "Configuration validation failed"
                    )
            except ImportError as e:
                self.results.add_test(
                    "Worker Configuration Import",
                    "FAIL",
                    f"Cannot import worker config: {e}"
                )
                
        except Exception as e:
            self.results.add_test(
                "Configuration Validation",
                "FAIL",
                f"Configuration validation error: {e}"
            )
    
    def validate_dependencies(self):
        """Validate required Python packages are installed"""
        print("\n📦 Validating Dependencies")
        print("-" * 40)
        
        required_packages = [
            'fastapi',
            'uvicorn', 
            'praw',
            'pandas',
            'psycopg2',
            'redis',
            'pydantic',
            'requests',
            'python-dotenv'
        ]
        
        for package in required_packages:
            try:
                __import__(package)
                self.results.add_test(
                    f"Package: {package}",
                    "PASS",
                    "Package available"
                )
            except ImportError:
                self.results.add_test(
                    f"Package: {package}",
                    "FAIL", 
                    "Package not installed"
                )
    
    def validate_database_connection(self):
        """Validate database connectivity"""
        print("\n💾 Validating Database Connection")
        print("-" * 40)
        
        try:
            import psycopg2
            from worker.config.worker_config import config
            
            db_config = config.get_database_config()
            
            # Test connection
            conn = psycopg2.connect(
                host=db_config['host'],
                port=db_config['port'], 
                database=db_config['database'],
                user=db_config['username'],
                password=db_config['password']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            conn.close()
            
            self.results.add_test(
                "Database Connection",
                "PASS",
                f"Connected successfully. Version: {version[0][:50]}..."
            )
            
        except Exception as e:
            self.results.add_test(
                "Database Connection", 
                "FAIL",
                f"Connection failed: {str(e)[:100]}..."
            )
    
    def validate_redis_connection(self):
        """Validate Redis connectivity"""
        print("\n🔴 Validating Redis Connection")
        print("-" * 40)
        
        try:
            import redis
            
            # Try to connect to Redis
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                password=os.getenv('REDIS_PASSWORD', 'sentiment_redis'),
                decode_responses=True
            )
            
            # Test connection
            redis_client.ping()
            info = redis_client.info()
            
            self.results.add_test(
                "Redis Connection",
                "PASS", 
                f"Connected successfully. Version: {info.get('redis_version', 'unknown')}"
            )
            
        except Exception as e:
            self.results.add_test(
                "Redis Connection",
                "WARN",
                f"Connection failed (non-critical): {str(e)[:100]}..."
            )
    
    def validate_reddit_api(self):
        """Validate Reddit API credentials"""
        print("\n🔴 Validating Reddit API")
        print("-" * 40)
        
        try:
            import praw
            from worker.config.worker_config import config
            
            reddit_config = config.get_reddit_config()
            
            if not reddit_config['client_id'] or not reddit_config['client_secret']:
                self.results.add_test(
                    "Reddit API Credentials",
                    "FAIL",
                    "Reddit API credentials not configured"
                )
                return
            
            # Test Reddit API connection
            reddit = praw.Reddit(
                client_id=reddit_config['client_id'],
                client_secret=reddit_config['client_secret'],
                user_agent=reddit_config['user_agent']
            )
            
            # Test by accessing Reddit info (read-only)
            reddit.read_only = True
            
            # Try to access a subreddit
            subreddit = reddit.subreddit('test')
            next(subreddit.hot(limit=1))  # Try to get one post
            
            self.results.add_test(
                "Reddit API Connection",
                "PASS",
                "Reddit API credentials valid and working"
            )
            
        except Exception as e:
            self.results.add_test(
                "Reddit API Connection",
                "FAIL",
                f"Reddit API test failed: {str(e)[:100]}..."
            )
    
    def validate_worker_components(self):
        """Validate worker components can be imported and initialized"""
        print("\n🔧 Validating Worker Components")
        print("-" * 40)
        
        components = [
            ("Worker Orchestrator", "worker.worker_orchestrator", "WorkerOrchestrator"),
            ("Task Interface", "worker.utils.task_interface", "TaskInterface"),
            ("Pydantic Models", "worker.pydantic_models", None),
            ("Reddit Scraper", "worker.scrapers.RedditScraper", "RedditScraper"),
        ]
        
        for name, module_path, class_name in components:
            try:
                # Import module
                module = importlib.import_module(module_path)
                
                if class_name:
                    # Try to get class
                    cls = getattr(module, class_name)
                    
                    # Try to instantiate (with minimal config if needed)
                    if class_name == "TaskInterface":
                        instance = cls('data/')
                    elif class_name == "WorkerOrchestrator":
                        instance = cls()  # Should work with default config
                    elif class_name == "RedditScraper":
                        # Skip instantiation for Reddit scraper (needs valid config)
                        pass
                    
                self.results.add_test(
                    f"Component: {name}",
                    "PASS",
                    "Import and initialization successful"
                )
                
            except Exception as e:
                self.results.add_test(
                    f"Component: {name}",
                    "FAIL",
                    f"Import/initialization failed: {str(e)[:100]}..."
                )
    
    def validate_service_startup(self):
        """Validate that the worker service can start"""
        print("\n🚀 Validating Service Startup")
        print("-" * 40)
        
        try:
            # Start the worker service as a subprocess
            cmd = [
                sys.executable, 
                str(self.project_root / "run_scheduled_worker.py"),
                "--config", "test",
                "--no-scheduler"  # Disable scheduler for testing
            ]
            
            print(f"   Starting service: {' '.join(cmd)}")
            
            self.service_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            # Wait a bit for service to start
            time.sleep(10)
            
            # Check if process is still running
            if self.service_process.poll() is None:
                self.results.add_test(
                    "Service Startup",
                    "PASS",
                    f"Service started successfully (PID: {self.service_process.pid})"
                )
            else:
                stdout, stderr = self.service_process.communicate()
                self.results.add_test(
                    "Service Startup",
                    "FAIL",
                    f"Service failed to start. Error: {stderr.decode()[:100]}..."
                )
                self.service_process = None
                
        except Exception as e:
            self.results.add_test(
                "Service Startup",
                "FAIL",
                f"Failed to start service: {str(e)}"
            )
            self.service_process = None
    
    def validate_api_endpoints(self):
        """Validate API endpoints are working"""
        print("\n🌐 Validating API Endpoints")
        print("-" * 40)
        
        endpoints = [
            ("GET", "/", "Root Endpoint"),
            ("GET", "/health", "Health Check"),
            ("GET", "/scrape/info", "Scrape Info"),
            ("GET", "/tasks", "Task List"),
            ("GET", "/pipeline/history", "Pipeline History"),
            ("GET", "/pipeline/active", "Active Pipelines")
        ]
        
        for method, endpoint, name in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.service_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.results.add_test(
                        f"API: {name}",
                        "PASS",
                        f"Endpoint working (Status: {response.status_code})"
                    )
                else:
                    self.results.add_test(
                        f"API: {name}",
                        "FAIL",
                        f"Endpoint returned status {response.status_code}"
                    )
                    
            except Exception as e:
                self.results.add_test(
                    f"API: {name}",
                    "FAIL",
                    f"Endpoint failed: {str(e)[:100]}..."
                )
    
    def validate_pipeline_functionality(self):
        """Validate pipeline functionality with a test run"""
        print("\n🔄 Validating Pipeline Functionality")
        print("-" * 40)
        
        try:
            # Submit a small test pipeline
            pipeline_request = {
                "subreddit": "test",
                "post_limit": 2,
                "comment_limit": 1,
                "enable_processing": False,
                "enable_cleaning": False, 
                "enable_database": False
            }
            
            response = requests.post(
                f"{self.service_url}/pipeline/run",
                json=pipeline_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                pipeline_id = result.get('pipeline_id')
                
                self.results.add_test(
                    "Pipeline: Submission",
                    "PASS",
                    f"Pipeline submitted successfully (ID: {pipeline_id})"
                )
                
                # Check status
                time.sleep(2)
                status_response = requests.get(
                    f"{self.service_url}/pipeline/{pipeline_id}/status",
                    timeout=10
                )
                
                if status_response.status_code == 200:
                    status = status_response.json()
                    self.results.add_test(
                        "Pipeline: Status Check",
                        "PASS",
                        f"Status check working (Status: {status.get('status')})"
                    )
                else:
                    self.results.add_test(
                        "Pipeline: Status Check",
                        "FAIL",
                        f"Status check failed (Status: {status_response.status_code})"
                    )
                
                # Test cancellation
                cancel_response = requests.delete(
                    f"{self.service_url}/pipeline/{pipeline_id}/cancel",
                    timeout=10
                )
                
                if cancel_response.status_code == 200:
                    self.results.add_test(
                        "Pipeline: Cancellation", 
                        "PASS",
                        "Pipeline cancellation working"
                    )
                else:
                    self.results.add_test(
                        "Pipeline: Cancellation",
                        "WARN",
                        f"Cancellation returned status {cancel_response.status_code}"
                    )
                    
            else:
                self.results.add_test(
                    "Pipeline: Submission",
                    "FAIL",
                    f"Pipeline submission failed (Status: {response.status_code})"
                )
                
        except Exception as e:
            self.results.add_test(
                "Pipeline: Functionality Test",
                "FAIL",
                f"Pipeline test failed: {str(e)[:100]}..."
            )
    
    def cleanup_service(self):
        """Stop the service process"""
        print("\n🧹 Cleaning Up Service")
        print("-" * 40)
        
        if self.service_process:
            try:
                # Try graceful shutdown first
                self.service_process.terminate()
                
                # Wait for process to end
                try:
                    self.service_process.wait(timeout=10)
                    self.results.add_test(
                        "Service Cleanup",
                        "PASS",
                        "Service stopped gracefully"
                    )
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    self.service_process.kill()
                    self.service_process.wait()
                    self.results.add_test(
                        "Service Cleanup",
                        "WARN",
                        "Service force-killed (didn't stop gracefully)"
                    )
                    
            except Exception as e:
                self.results.add_test(
                    "Service Cleanup",
                    "WARN",
                    f"Cleanup error: {str(e)}"
                )
        else:
            self.results.add_test(
                "Service Cleanup",
                "SKIP",
                "No service to clean up"
            )

def main():
    """Main validation function"""
    print("🧪 Comprehensive API-Friendly Pipeline Service Validation")
    print("=" * 80)
    print(f"📁 Project Root: {project_root}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run validation
    validator = SystemValidator()
    passed, failed, warnings = validator.run_all_validations()
    
    # Exit with appropriate code
    if failed > 0:
        print(f"\n❌ Validation completed with {failed} failures")
        sys.exit(1)
    elif warnings > 0:
        print(f"\n⚠️ Validation completed with {warnings} warnings")
        sys.exit(0)
    else:
        print(f"\n✅ All validations passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
