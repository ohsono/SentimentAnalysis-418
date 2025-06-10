#!/usr/bin/env python3

"""
Simple Validation Runner
Quick way to run all validations
"""

import subprocess
import sys
from pathlib import Path

def run_validation(script_name, description):
    """Run a validation script"""
    print(f"\n🔄 {description}")
    print("-" * 50)
    
    script_path = Path("validation") / script_name
    if not script_path.exists():
        print(f"❌ {script_name} not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(script_path)], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all available validations"""
    print("🧪 API-Friendly Pipeline Service - Validation Runner")
    print("=" * 60)
    
    validations = [
        ("quick_validation.py", "Quick Basic Validation"),
        ("database_validation.py", "Database Connectivity"),
        ("reddit_scraper_validation.py", "Reddit API Validation")
    ]
    
    passed = 0
    total = len(validations)
    
    for script, description in validations:
        if run_validation(script, description):
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Validation Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All validations passed! Ready to deploy.")
    elif passed > 0:
        print("⚠️ Some validations passed. Check failures above.")
    else:
        print("❌ All validations failed. Check configuration.")
    
    print("\n💡 For detailed validation, run: python3 validation/master_validation.py")

if __name__ == "__main__":
    main()
