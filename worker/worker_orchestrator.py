#!/usr/bin/env python3

"""
Worker Orchestrator for UCLA Sentiment Analysis
Manages and coordinates worker processes for scraping and processing
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import time

# Add worker directory to path
sys.path.append(str(Path(__file__).parent))

from config.worker_config import config
from scrapers.RedditScraper import RedditScraper, load_config
from processors.RedditDataProcessor import RedditDataProcessor

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.WORKER_CONFIG['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOGS_DIR / 'worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WorkerOrchestrator:
    """Orchestrates worker processes for data collection and processing"""
    
    def __init__(self):
        self.config = config
        self.running = False
        self.workers = {}
        self.task_queue = asyncio.Queue()
        self.results = {}
        
        # Create task directories
        self.task_dir = self.config.DATA_DIR / "tasks"
        self.results_dir = self.config.DATA_DIR / "results"
        self.task_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("Worker orchestrator initialized")
    
    async def start(self):
        """Start the worker orchestrator"""
        self.running = True
        logger.info("Starting worker orchestrator...")
        
        # Start task processors
        tasks = [
            asyncio.create_task(self._task_processor()),
            asyncio.create_task(self._file_watcher()),
            asyncio.create_task(self._health_checker())
        ]
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the worker orchestrator"""
        self.running = False
        logger.info("Stopping worker orchestrator...")
        
        # Wait for tasks to complete
        await asyncio.sleep(1)
        logger.info("Worker orchestrator stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False
    
    async def _task_processor(self):
        """Process tasks from the queue"""
        logger.info("Task processor started")
        
        while self.running:
            try:
                # Check for new tasks
                task = await asyncio.wait_for(self.task_queue.get(), timeout=5.0)
                await self._execute_task(task)
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in task processor: {e}")
                await asyncio.sleep(5)
    
    async def _file_watcher(self):
        """Watch for task files in the task directory"""
        logger.info("File watcher started")
        
        while self.running:
            try:
                # Check for new task files
                for task_file in self.task_dir.glob("*.json"):
                    if task_file.stem.endswith("_processing"):
                        continue
                    
                    try:
                        # Load and process task
                        with open(task_file, 'r') as f:
                            task_data = json.load(f)
                        
                        # Mark as processing
                        processing_file = task_file.with_name(f"{task_file.stem}_processing.json")
                        task_file.rename(processing_file)
                        
                        # Queue the task
                        await self.task_queue.put({
                            'task_file': processing_file,
                            'data': task_data
                        })
                        
                        logger.info(f"Queued task from {task_file.name}")
                        
                    except Exception as e:
                        logger.error(f"Error processing task file {task_file}: {e}")
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                await asyncio.sleep(5)
    
    async def _health_checker(self):
        """Periodic health check and status update"""
        logger.info("Health checker started")
        
        while self.running:
            try:
                # Create health status
                status = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'status': 'running',
                    'queue_size': self.task_queue.qsize(),
                    'active_workers': len(self.workers),
                    'config_valid': self.config.validate_config()
                }
                
                # Save health status
                health_file = self.config.DATA_DIR / "worker_health.json"
                with open(health_file, 'w') as f:
                    json.dump(status, f, indent=2)
                
                logger.debug(f"Health check: {status}")
                
                await asyncio.sleep(self.config.WORKER_CONFIG['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Error in health checker: {e}")
                await asyncio.sleep(60)
    
    async def _execute_task(self, task_info: Dict[str, Any]):
        """Execute a specific task"""
        task_file = task_info['task_file']
        task_data = task_info['data']
        task_type = task_data.get('type', 'unknown')
        
        logger.info(f"Executing task: {task_type}")
        
        try:
            if task_type == 'scrape_reddit':
                result = await self._scrape_reddit_task(task_data)
            elif task_type == 'process_data':
                result = await self._process_data_task(task_data)
            elif task_type == 'generate_report':
                result = await self._generate_report_task(task_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Save result
            result_file = self.results_dir / f"{task_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Remove processing file
            task_file.unlink()
            
            logger.info(f"Task {task_type} completed successfully")
            
        except Exception as e:
            logger.error(f"Error executing task {task_type}: {e}")
            
            # Save error result
            error_result = {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'task_data': task_data
            }
            
            error_file = self.results_dir / f"{task_file.stem}_error.json"
            with open(error_file, 'w') as f:
                json.dump(error_result, f, indent=2)
            
            # Remove processing file
            task_file.unlink()
    
    async def _scrape_reddit_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Reddit scraping task"""
        logger.info("Starting Reddit scraping task")
        
        # Prepare scraper config
        scraper_config = {
            **self.config.get_reddit_config(),
            'subreddit': task_data.get('subreddit', 'UCLA'),
            'post_limit': task_data.get('post_limit', 100),
            'comment_limit': task_data.get('comment_limit', 50),
            'data_dir': str(self.config.DATA_DIR)
        }
        
        # Validate Reddit config
        if not scraper_config['client_id'] or not scraper_config['client_secret']:
            raise ValueError("Reddit API credentials not configured")
        
        # Initialize and run scraper
        scraper = RedditScraper(scraper_config)
        
        # Run scraping synchronously (PRAW is synchronous)
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, scraper.scrape_subreddit)
        
        result = {
            'status': 'completed',
            'type': 'scrape_reddit',
            'stats': stats,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_data': task_data
        }
        
        logger.info(f"Reddit scraping completed: {stats}")
        return result
    
    async def _process_data_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data processing task"""
        logger.info("Starting data processing task")
        
        # Initialize processor
        processor = RedditDataProcessor(self.config.get_processing_config())
        
        # For now, return a placeholder result
        # In a real implementation, you would load data and process it
        result = {
            'status': 'completed',
            'type': 'process_data',
            'message': 'Data processing completed',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_data': task_data
        }
        
        logger.info("Data processing completed")
        return result
    
    async def _generate_report_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute report generation task"""
        logger.info("Starting report generation task")
        
        # Placeholder for report generation
        result = {
            'status': 'completed',
            'type': 'generate_report',
            'message': 'Report generation completed',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_data': task_data
        }
        
        logger.info("Report generation completed")
        return result
    
    async def queue_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """Queue a new task"""
        task_id = f"{task_type}_{int(time.time())}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'created_at': datetime.now(timezone.utc).isoformat(),
            **task_data
        }
        
        # Save task file
        task_file = self.task_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        logger.info(f"Queued task {task_id}")
        return task_id

def main():
    """Main function for worker orchestrator"""
    parser = argparse.ArgumentParser(description='UCLA Sentiment Analysis Worker')
    parser.add_argument('--validate-config', action='store_true', 
                       help='Validate configuration and exit')
    parser.add_argument('--queue-task', type=str, 
                       help='Queue a task (scrape_reddit, process_data, generate_report)')
    parser.add_argument('--subreddit', type=str, default='UCLA',
                       help='Subreddit for scraping tasks')
    parser.add_argument('--post-limit', type=int, default=100,
                       help='Post limit for scraping tasks')
    
    args = parser.parse_args()
    
    # Validate configuration
    if args.validate_config:
        config.print_config_summary()
        if config.validate_config():
            print("✅ Configuration is valid")
            sys.exit(0)
        else:
            print("❌ Configuration is invalid")
            sys.exit(1)
    
    # Queue a task
    if args.queue_task:
        orchestrator = WorkerOrchestrator()
        
        task_data = {
            'subreddit': args.subreddit,
            'post_limit': args.post_limit
        }
        
        # Create task file directly
        task_id = f"{args.queue_task}_{int(time.time())}"
        task = {
            'id': task_id,
            'type': args.queue_task,
            'created_at': datetime.now(timezone.utc).isoformat(),
            **task_data
        }
        
        task_file = orchestrator.task_dir / f"{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        print(f"✅ Queued task: {task_id}")
        sys.exit(0)
    
    # Start orchestrator
    print("🚀 Starting UCLA Sentiment Analysis Worker...")
    config.print_config_summary()
    
    if not config.validate_config():
        print("❌ Configuration validation failed")
        sys.exit(1)
    
    orchestrator = WorkerOrchestrator()
    asyncio.run(orchestrator.start())

if __name__ == "__main__":
    main()
