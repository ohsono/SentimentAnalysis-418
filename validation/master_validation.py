#!/usr/bin/env python3

"""
Master Validation Script
Runs all validation scripts and provides comprehensive reporting
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

def run_validation_script(script_name, description):
    """Run a validation script and capture results"""
    print(f"\n🔄 Running {description}")
    print("=" * 80)
    
    script_path = current_dir / script_name
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return {
            'script': script_name,
            'description': description,
            'return_code': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out after 5 minutes")
        return {
            'script': script_name,
            'description': description,
            'return_code': -1,
            'stdout': '',
            'stderr': 'Script timed out',
            'success': False
        }
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return {
            'script': script_name,
            'description': description,
            'return_code': -1,
            'stdout': '',
            'stderr': str(e),
            'success': False
        }

def save_results(results, output_file):
    """Save validation results to file"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'project_root': str(project_root),
        'total_validations': len(results),
        'successful_validations': len([r for r in results if r['success']]),
        'failed_validations': len([r for r in results if not r['success']]),
        'validations': results
    }
    
    try:
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Detailed results saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False

def print_master_summary(results):
    """Print comprehensive summary of all validations"""
    print("\n" + "=" * 100)
    print("🏆 MASTER VALIDATION SUMMARY")
    print("=" * 100)
    
    total = len(results)
    successful = len([r for r in results if r['success']])
    failed = total - successful
    
    print(f"📊 Total Validations: {total}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(successful/total*100):.1f}%" if total > 0 else "N/A")
    
    print("\n" + "-" * 100)
    print("📋 VALIDATION BREAKDOWN:")
    print("-" * 100)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {result['description']}")
        if not result['success'] and result['stderr']:
            print(f"    Error: {result['stderr'][:150]}...")
    
    if failed == 0:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("🚀 Your API-friendly pipeline service is ready for production!")
        print("\n📋 System Status: READY ✅")
        print("   • All components validated")
        print("   • Configuration verified")
        print("   • Dependencies satisfied")
        print("   • Services operational")
        
        print("\n💡 Next Steps:")
        print("   • Start the service: python run_scheduled_worker.py")
        print("   • Test API endpoints: python test_pipeline_api.py")
        print("   • Monitor with health checks: curl http://localhost:8082/health")
        print("   • Run your first pipeline!")
        
    else:
        print(f"\n⚠️ {failed} VALIDATION(S) FAILED")
        print("🔧 System Status: NEEDS ATTENTION")
        
        print("\n🔍 Failed Validations:")
        for result in results:
            if not result['success']:
                print(f"   ❌ {result['description']}")
                if result['stderr']:
                    print(f"      Error: {result['stderr'][:200]}...")
        
        print("\n💡 Recommended Actions:")
        
        # Provide specific recommendations based on failures
        failed_scripts = [r['script'] for r in results if not r['success']]
        
        if 'quick_validation.py' in failed_scripts:
            print("   1. 📦 Install missing dependencies: pip install -r requirements.txt")
            print("   2. ⚙️ Check configuration files (.env.scheduler)")
        
        if 'database_validation.py' in failed_scripts:
            print("   3. 💾 Verify PostgreSQL server is running and accessible")
            print("   4. 🔐 Check database credentials and permissions")
        
        if 'reddit_scraper_validation.py' in failed_scripts:
            print("   5. 🔑 Verify Reddit API credentials")
            print("   6. 🌐 Test internet connectivity to Reddit")
        
        if 'comprehensive_validation.py' in failed_scripts:
            print("   7. 🚀 Check if required services (Redis, PostgreSQL) are running")
            print("   8. 🔧 Review service startup logs")
        
        print("\n🔄 Re-run validations after fixing issues:")
        print("   python validation/master_validation.py")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Master Validation for API-Friendly Pipeline Service')
    parser.add_argument('--quick-only', action='store_true',
                       help='Run only quick validation (no service startup)')
    parser.add_argument('--skip-comprehensive', action='store_true',
                       help='Skip comprehensive validation (service startup test)')
    parser.add_argument('--output', type=str, default='validation_results.json',
                       help='Output file for detailed results')
    
    args = parser.parse_args()
    
    print("🏗️ Master Validation for API-Friendly Pipeline Service")
    print("=" * 100)
    print(f"📁 Project Root: {project_root}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📄 Results will be saved to: {args.output}")
    
    results = []
    
    # Define validation scripts in order of execution
    validations = [
        ('quick_validation.py', 'Quick Function Validation'),
        ('database_validation.py', 'Database Connectivity Validation'),
        ('reddit_scraper_validation.py', 'Reddit Scraper Validation'),
    ]
    
    if not args.quick_only and not args.skip_comprehensive:
        validations.append(('comprehensive_validation.py', 'Comprehensive Service Validation'))
    
    # Run each validation
    for script, description in validations:
        result = run_validation_script(script, description)
        results.append(result)
        
        # If a critical validation fails, ask if user wants to continue
        if not result['success'] and script in ['quick_validation.py', 'database_validation.py']:
            print(f"\n⚠️ Critical validation '{description}' failed.")
            if input("Continue with remaining validations? [y/N]: ").lower() != 'y':
                print("🛑 Validation stopped by user.")
                break
    
    # Save detailed results
    output_path = current_dir / args.output
    save_results(results, output_path)
    
    # Print master summary
    print_master_summary(results)
    
    # Exit with appropriate code
    failed_count = len([r for r in results if not r['success']])
    sys.exit(0 if failed_count == 0 else 1)

if __name__ == "__main__":
    main()
