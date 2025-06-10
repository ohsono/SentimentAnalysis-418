#!/usr/bin/env python3

"""
Validation Overview Script
Shows available validation options and provides quick access
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
current_dir = Path(__file__).parent
project_root = current_dir.parent

def print_banner():
    """Print validation banner"""
    print("🧪 API-Friendly Pipeline Service - Validation Suite")
    print("=" * 80)
    print(f"📁 Project: {project_root.name}")
    print(f"📍 Location: {project_root}")
    print(f"⏰ Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def show_validation_options():
    """Show available validation options"""
    print("🚀 Available Validation Scripts:")
    print("-" * 50)
    
    validations = [
        {
            'file': 'master_validation.py',
            'name': '🏆 Master Validation',
            'description': 'Complete system validation (RECOMMENDED)',
            'duration': '5-10 minutes',
            'command': 'python validation/master_validation.py'
        },
        {
            'file': 'quick_validation.py', 
            'name': '⚡ Quick Validation',
            'description': 'Fast basic checks without service startup',
            'duration': '30 seconds',
            'command': 'python validation/quick_validation.py'
        },
        {
            'file': 'database_validation.py',
            'name': '💾 Database Validation', 
            'description': 'PostgreSQL connectivity and functionality',
            'duration': '1-2 minutes',
            'command': 'python validation/database_validation.py'
        },
        {
            'file': 'reddit_scraper_validation.py',
            'name': '🕷️ Reddit Scraper Validation',
            'description': 'Reddit API and scraping functionality',
            'duration': '2-3 minutes',
            'command': 'python validation/reddit_scraper_validation.py'
        },
        {
            'file': 'comprehensive_validation.py',
            'name': '🔧 Comprehensive Validation',
            'description': 'Full service startup and API testing',
            'duration': '5-8 minutes',
            'command': 'python validation/comprehensive_validation.py'
        }
    ]
    
    for i, validation in enumerate(validations, 1):
        file_path = current_dir / validation['file']
        exists = "✅" if file_path.exists() else "❌"
        
        print(f"{i}. {validation['name']} {exists}")
        print(f"   📝 {validation['description']}")
        print(f"   ⏱️ Duration: {validation['duration']}")
        print(f"   💻 Command: {validation['command']}")
        print()

def show_quick_commands():
    """Show quick command options"""
    print("⚡ Quick Commands:")
    print("-" * 30)
    print("1. 🚀 Run Master Validation")
    print("2. ⚡ Run Quick Validation Only")
    print("3. 💾 Test Database Only")
    print("4. 🕷️ Test Reddit Scraper Only")
    print("5. 🔧 Full Service Testing")
    print("6. 📖 View Validation README")
    print("7. 🚪 Exit")
    print()

def run_command(cmd):
    """Run a validation command"""
    print(f"🔄 Running: {cmd}")
    print("-" * 80)
    
    try:
        os.system(f"cd {project_root} && {cmd}")
    except KeyboardInterrupt:
        print("\n⏹️ Command interrupted by user")
    except Exception as e:
        print(f"❌ Error running command: {e}")

def show_readme():
    """Show README content"""
    readme_path = current_dir / "README.md"
    
    if readme_path.exists():
        print("📖 Validation README:")
        print("-" * 50)
        with open(readme_path) as f:
            content = f.read()
            # Show first part of README
            lines = content.split('\n')
            for line in lines[:100]:  # Show first 100 lines
                print(line)
            if len(lines) > 100:
                print("\n... (truncated, see validation/README.md for full content)")
    else:
        print("❌ README.md not found")

def interactive_mode():
    """Run interactive validation selection"""
    while True:
        print_banner()
        show_validation_options()
        show_quick_commands()
        
        try:
            choice = input("Select an option (1-7): ").strip()
            
            if choice == '1':
                run_command("python validation/master_validation.py")
            elif choice == '2':
                run_command("python validation/quick_validation.py")
            elif choice == '3':
                run_command("python validation/database_validation.py")
            elif choice == '4':
                run_command("python validation/reddit_scraper_validation.py")
            elif choice == '5':
                run_command("python validation/comprehensive_validation.py")
            elif choice == '6':
                show_readme()
                input("\nPress Enter to continue...")
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-7.")
                input("Press Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validation Overview and Quick Access')
    parser.add_argument('--list', action='store_true',
                       help='List available validations and exit')
    parser.add_argument('--run', choices=['master', 'quick', 'database', 'reddit', 'comprehensive'],
                       help='Run specific validation directly')
    
    args = parser.parse_args()
    
    if args.list:
        print_banner()
        show_validation_options()
        return
    
    if args.run:
        commands = {
            'master': 'python validation/master_validation.py',
            'quick': 'python validation/quick_validation.py', 
            'database': 'python validation/database_validation.py',
            'reddit': 'python validation/reddit_scraper_validation.py',
            'comprehensive': 'python validation/comprehensive_validation.py'
        }
        run_command(commands[args.run])
        return
    
    # Interactive mode
    interactive_mode()

if __name__ == "__main__":
    main()
