#!/usr/bin/env python3

"""
Scheduled Worker Service Runner
Run the worker service with scheduled scraping and data pipeline
"""

import os
import sys
import argparse
from pathlib import Path

def load_scheduler_env():
    """Load scheduler environment configuration"""
    env_file = Path(__file__).parent / ".env.scheduler"
    
    if env_file.exists():
        print("📋 Loading scheduler configuration...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    if key.startswith('SCHEDULER_') or key in ['SCRAPING_INTERVAL_MINUTES', 'AUTO_PIPELINE_ENABLED']:
                        print(f"   {key}={value}")
    else:
        print("⚠️ No .env.scheduler file found, using defaults")

def print_scheduler_info():
    """Print current scheduler configuration"""
    print("\n📅 Current Scheduler Configuration:")
    print("-" * 40)
    
    config_items = [
        ('SCHEDULER_ENABLED', 'true'),
        ('SCRAPING_INTERVAL_MINUTES', '30'),
        ('AUTO_PIPELINE_ENABLED', 'true'),
        ('RETRY_FAILED_TASKS', 'true'),
        ('MAX_TASK_RETRIES', '3'),
        ('CLEANUP_OLD_DATA_HOURS', '24'),
        ('DEFAULT_SUBREDDIT', 'UCLA'),
        ('DEFAULT_POST_LIMIT', '100'),
        ('DEFAULT_COMMENT_LIMIT', '50'),
    ]
    
    for key, default in config_items:
        value = os.getenv(key, default)
        print(f"   {key}: {value}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Scheduled Worker Service Runner')
    parser.add_argument('--config', choices=['default', 'scheduler', 'test'], 
                       default='scheduler',
                       help='Configuration to use (default, scheduler, test)')
    parser.add_argument('--interval', type=int, 
                       help='Override scraping interval in minutes')
    parser.add_argument('--no-scheduler', action='store_true',
                       help='Disable scheduler (manual tasks only)')
    parser.add_argument('--no-pipeline', action='store_true',
                       help='Disable automatic pipeline (scraping only)')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run in test mode with short intervals')
    
    args = parser.parse_args()
    
    print("🚀 Scheduled Worker Service Runner")
    print("=" * 50)
    
    # Load configuration
    if args.config == 'scheduler':
        load_scheduler_env()
    elif args.config == 'test':
        # Set test mode environment variables
        os.environ['SCHEDULER_ENABLED'] = 'true'
        os.environ['SCRAPING_INTERVAL_MINUTES'] = '2'  # 2 minutes for testing
        os.environ['AUTO_PIPELINE_ENABLED'] = 'true'
        os.environ['DEFAULT_POST_LIMIT'] = '5'  # Fewer posts for testing
        os.environ['DEFAULT_COMMENT_LIMIT'] = '3'  # Fewer comments for testing
        print("🧪 Test mode configuration loaded")
    
    # Apply command line overrides
    if args.interval:
        os.environ['SCRAPING_INTERVAL_MINUTES'] = str(args.interval)
        print(f"⏰ Override: Scraping interval set to {args.interval} minutes")
    
    if args.no_scheduler:
        os.environ['SCHEDULER_ENABLED'] = 'false'
        print("❌ Override: Scheduler disabled")
    
    if args.no_pipeline:
        os.environ['AUTO_PIPELINE_ENABLED'] = 'false'
        print("❌ Override: Auto pipeline disabled")
    
    if args.test_mode:
        os.environ['SCRAPING_INTERVAL_MINUTES'] = '1'  # 1 minute for quick testing
        os.environ['DEFAULT_POST_LIMIT'] = '3'
        os.environ['DEFAULT_COMMENT_LIMIT'] = '2'
        print("🧪 Test mode: Short intervals and limits set")
    
    # Print final configuration
    print_scheduler_info()
    
    # Start the worker service
    print("\n🚀 Starting Scheduled Worker Service")
    print("-" * 40)
    
    # Add worker directory to path
    worker_dir = Path(__file__).parent / "worker"
    if str(worker_dir) not in sys.path:
        sys.path.insert(0, str(worker_dir))
    
    try:
        from worker.main import app
        import uvicorn
        
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("WORKER_PORT", 8082))
        
        print(f"🌐 Host: {host}")
        print(f"🔌 Port: {port}")
        print(f"📊 Health endpoint: http://{host}:{port}/health")
        print(f"📖 API docs: http://{host}:{port}/docs")
        
        if os.getenv('SCHEDULER_ENABLED', 'true').lower() == 'true':
            interval = os.getenv('SCRAPING_INTERVAL_MINUTES', '30')
            print(f"⏰ Scheduled scraping: Every {interval} minutes")
            print(f"🔄 Auto pipeline: {os.getenv('AUTO_PIPELINE_ENABLED', 'true')}")
        else:
            print("📋 Manual task processing only")
        
        print("-" * 40)
        print("🎯 Service starting... Press Ctrl+C to stop")
        print("-" * 40)
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're in the project root directory")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Worker service stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting worker service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
