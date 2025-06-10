#!/usr/bin/env python3

"""
Quick Function Validation Script
Checks basic functionality without starting the full service
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "worker"))

def check_imports():
    """Check if all critical modules can be imported"""
    print("📦 Checking Critical Imports")
    print("-" * 40)
    
    imports_to_test = [
        ("FastAPI", "fastapi", "FastAPI"),
        ("Uvicorn", "uvicorn", None),
        ("Pydantic", "pydantic", "BaseModel"),
        ("Redis", "redis", "Redis"),
        ("Pandas", "pandas", None),
        ("PRAW (Reddit)", "praw", "Reddit"),
        ("PostgreSQL", "psycopg2", None),
        ("Requests", "requests", None),
        ("Python-dotenv", "dotenv", "load_dotenv"),
    ]
    
    results = []
    for name, module, class_name in imports_to_test:
        try:
            imported_module = __import__(module)
            if class_name:
                getattr(imported_module, class_name)
            print(f"   ✅ {name}: Available")
            results.append((name, True, "Available"))
        except ImportError as e:
            print(f"   ❌ {name}: Missing - {e}")
            results.append((name, False, str(e)))
        except AttributeError as e:
            print(f"   ⚠️  {name}: Partial - {e}")
            results.append((name, False, str(e)))
    
    return results

def check_worker_modules():
    """Check worker-specific modules"""
    print("\n🔧 Checking Worker Modules")
    print("-" * 40)
    
    worker_modules = [
        ("Worker Config", "worker.config.worker_config", "WorkerConfig"),
        ("Worker Orchestrator", "worker.worker_orchestrator", "WorkerOrchestrator"),
        ("Pydantic Models", "worker.pydantic_models", "WorkerScrapeRequest"),
        ("Task Interface", "worker.utils.task_interface", "TaskInterface"),
    ]
    
    results = []
    for name, module_path, class_name in worker_modules:
        try:
            import importlib
            module = importlib.import_module(module_path)
            if class_name:
                cls = getattr(module, class_name)
            print(f"   ✅ {name}: Available")
            results.append((name, True, "Available"))
        except ImportError as e:
            print(f"   ❌ {name}: Cannot import - {e}")
            results.append((name, False, f"Import error: {e}"))
        except AttributeError as e:
            print(f"   ⚠️  {name}: Class missing - {e}")
            results.append((name, False, f"Attribute error: {e}"))
    
    return results

def check_configuration():
    """Check configuration files and environment"""
    print("\n⚙️ Checking Configuration")
    print("-" * 40)
    
    results = []
    
    # Check .env.scheduler file
    env_file = project_root / ".env.scheduler"
    if env_file.exists():
        print(f"   ✅ Environment file: Found")
        
        # Check for critical variables
        with open(env_file) as f:
            content = f.read()
            
        critical_vars = [
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET', 
            'POSTGRES_HOST',
            'POSTGRES_DB',
            'SCHEDULER_ENABLED'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if var not in content or f"{var}=" not in content:
                missing_vars.append(var)
        
        if not missing_vars:
            print(f"   ✅ Environment variables: All critical vars present")
            results.append(("Environment Variables", True, "All present"))
        else:
            print(f"   ⚠️  Environment variables: Missing {missing_vars}")
            results.append(("Environment Variables", False, f"Missing: {missing_vars}"))
    else:
        print(f"   ❌ Environment file: Not found")
        results.append(("Environment File", False, "File not found"))
    
    # Test worker config loading
    try:
        from worker.config.worker_config import config
        validation_result = config.validate_config()
        
        if validation_result:
            print(f"   ✅ Worker configuration: Valid")
            results.append(("Worker Config", True, "Configuration valid"))
        else:
            print(f"   ❌ Worker configuration: Invalid")
            results.append(("Worker Config", False, "Configuration invalid"))
    except Exception as e:
        print(f"   ❌ Worker configuration: Error - {e}")
        results.append(("Worker Config", False, f"Error: {e}"))
    
    return results

def check_file_structure():
    """Check required files and directories"""
    print("\n📁 Checking File Structure")
    print("-" * 40)
    
    required_items = [
        ("run_scheduled_worker.py", "file"),
        ("worker/", "dir"),
        ("worker/main.py", "file"),
        ("worker/worker_orchestrator.py", "file"),
        ("worker/config/", "dir"),
        ("worker/config/worker_config.py", "file"),
        ("worker/scrapers/", "dir"),
        ("worker/processors/", "dir"),
        ("worker/utils/", "dir"),
        ("app/", "dir"),
        ("test_pipeline_api.py", "file"),
        (".env.scheduler", "file"),
    ]
    
    results = []
    for item, item_type in required_items:
        path = project_root / item
        
        if item_type == "file":
            if path.exists() and path.is_file():
                print(f"   ✅ {item}: Found")
                results.append((item, True, "Found"))
            else:
                print(f"   ❌ {item}: Missing")
                results.append((item, False, "Missing"))
        elif item_type == "dir":
            if path.exists() and path.is_dir():
                print(f"   ✅ {item}: Found")
                results.append((item, True, "Found"))
            else:
                print(f"   ❌ {item}: Missing")
                results.append((item, False, "Missing"))
    
    return results

def check_data_directories():
    """Check and create data directories if needed"""
    print("\n💾 Checking Data Directories")
    print("-" * 40)
    
    data_dirs = [
        "worker/data",
        "worker/logs", 
        "worker/data/tasks",
        "worker/data/results",
        "worker/data/pipelines"
    ]
    
    results = []
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"   ✅ {dir_path}: Exists")
            results.append((dir_path, True, "Exists"))
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"   🔧 {dir_path}: Created")
                results.append((dir_path, True, "Created"))
            except Exception as e:
                print(f"   ❌ {dir_path}: Cannot create - {e}")
                results.append((dir_path, False, f"Cannot create: {e}"))
    
    return results

def test_basic_functionality():
    """Test basic functionality without starting services"""
    print("\n🧪 Testing Basic Functionality")
    print("-" * 40)
    
    results = []
    
    # Test WorkerOrchestrator instantiation
    try:
        from worker.worker_orchestrator import WorkerOrchestrator
        orchestrator = WorkerOrchestrator()
        print(f"   ✅ WorkerOrchestrator: Can instantiate")
        results.append(("WorkerOrchestrator", True, "Instantiation successful"))
    except Exception as e:
        print(f"   ❌ WorkerOrchestrator: Cannot instantiate - {e}")
        results.append(("WorkerOrchestrator", False, f"Instantiation failed: {e}"))
    
    # Test TaskInterface instantiation  
    try:
        from worker.utils.task_interface import TaskInterface
        task_interface = TaskInterface('worker/data/')
        print(f"   ✅ TaskInterface: Can instantiate")
        results.append(("TaskInterface", True, "Instantiation successful"))
    except Exception as e:
        print(f"   ❌ TaskInterface: Cannot instantiate - {e}")
        results.append(("TaskInterface", False, f"Instantiation failed: {e}"))
    
    # Test Pydantic models
    try:
        from worker.pydantic_models import WorkerScrapeRequest, PipelineRequest
        
        # Test WorkerScrapeRequest
        scrape_req = WorkerScrapeRequest(
            subreddit="test",
            post_limit=5,
            comment_limit=3
        )
        
        # Test PipelineRequest
        pipeline_req = PipelineRequest(
            subreddit="test",
            post_limit=5
        )
        
        print(f"   ✅ Pydantic Models: Working")
        results.append(("Pydantic Models", True, "Models can be instantiated"))
        
    except Exception as e:
        print(f"   ❌ Pydantic Models: Error - {e}")
        results.append(("Pydantic Models", False, f"Model error: {e}"))
    
    return results

def generate_summary_report(all_results):
    """Generate a summary report"""
    print("\n" + "=" * 80)
    print("📊 QUICK VALIDATION SUMMARY")
    print("=" * 80)
    
    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(
        len([r for r in results if r[1]]) 
        for results in all_results.values()
    )
    failed_tests = total_tests - passed_tests
    
    print(f"📈 Total Checks: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
    
    # Show failed tests
    if failed_tests > 0:
        print("\n❌ FAILED CHECKS:")
        print("-" * 40)
        for category, results in all_results.items():
            failed_in_category = [r for r in results if not r[1]]
            if failed_in_category:
                print(f"\n{category}:")
                for name, status, message in failed_in_category:
                    print(f"   • {name}: {message}")
    
    print("\n" + "=" * 80)
    
    return passed_tests, failed_tests

def main():
    """Main validation function"""
    print("⚡ Quick Function Validation")
    print("=" * 80)
    print(f"📁 Project Root: {project_root}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    
    # Run all checks
    all_results["Imports"] = check_imports()
    all_results["Worker Modules"] = check_worker_modules()
    all_results["Configuration"] = check_configuration()
    all_results["File Structure"] = check_file_structure()
    all_results["Data Directories"] = check_data_directories()
    all_results["Basic Functionality"] = test_basic_functionality()
    
    # Generate summary
    passed, failed = generate_summary_report(all_results)
    
    # Recommendations
    if failed > 0:
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Check .env.scheduler configuration")
        print("3. Ensure PostgreSQL and Redis are accessible")
        print("4. Run comprehensive validation for detailed API testing")
        print("\n🔧 Run full validation: python validation/comprehensive_validation.py")
    else:
        print("\n🎉 All basic checks passed!")
        print("🚀 Ready to run the comprehensive validation or start the service")
        print("\n🔧 Next steps:")
        print("   • Run comprehensive validation: python validation/comprehensive_validation.py")
        print("   • Start service: python run_scheduled_worker.py")
        print("   • Test API: python test_pipeline_api.py")

if __name__ == "__main__":
    main()
