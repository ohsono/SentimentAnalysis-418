#!/usr/bin/env python3

"""
Enhanced Worker Orchestrator for UCLA Sentiment Analysis
Manages scheduled scraping and sequential data processing pipeline
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import time

# Add worker directory to path
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

from config.worker_config import config
from scrapers.RedditScraper import RedditScraper, load_config
from processors.RedditDataProcessor import RedditDataProcessor

try:
    from app.database.postgres_manager import DatabaseManager, POSTGRES_AVAILABLE
except ImportError:
    POSTGRES_AVAILABLE = False
    DatabaseManager = None
    logging.warning("Database manager not available - running without database integration")

# Custom JSON encoder for datetime objects
class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Helper function to convert datetime objects to strings
def serialize_datetime_objects(obj):
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_datetime_objects(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_objects(item) for item in obj]
    else:
        return obj

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
    """Enhanced orchestrator with scheduled scraping and data pipeline"""
    
    def __init__(self):
        self.config = config
        self.running = False
        self.workers = {}
        self.task_queue = asyncio.Queue()
        self.results = {}
        self.scheduler_config = self.config.get_scheduler_config()
        self.db_manager = None
        
        # Scheduling state
        self.last_scheduled_scrape = None
        self.pipeline_running = False
        self.task_stats = {
            'total_scrapes': 0,
            'successful_scrapes': 0,
            'failed_scrapes': 0,
            'total_pipeline_runs': 0,
            'last_pipeline_success': None,
            'last_pipeline_failure': None
        }
        
        # Pipeline management
        self.active_pipelines = {}
        self.pipeline_history = []
        self.max_history_items = 100
        self.pipeline_counter = 0
        
        # Create task directories
        self.task_dir = self.config.DATA_DIR / "tasks"
        self.results_dir = self.config.DATA_DIR / "results"
        self.pipelines_dir = self.config.DATA_DIR / "pipelines"
        self.task_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.pipelines_dir.mkdir(exist_ok=True)
        
        logger.info("Enhanced worker orchestrator initialized")
        if self.scheduler_config['enabled']:
            logger.info(f"Scheduler enabled - scraping every {self.scheduler_config['scraping_interval_minutes']} minutes")
        else:
            logger.info("Scheduler disabled - manual task processing only")
    
    async def start(self):
        """Start the enhanced worker orchestrator"""
        self.running = True
        logger.info("Starting enhanced worker orchestrator...")
        
        # Initialize database manager if available
        if POSTGRES_AVAILABLE and DatabaseManager:
            try:
                self.db_manager = DatabaseManager()
                await self.db_manager.initialize()
                logger.info("Database manager initialized")
            except Exception as e:
                logger.error(f"Failed to initialize database manager: {e}")
                self.db_manager = None
        
        # Start task processors
        tasks = [
            asyncio.create_task(self._task_processor()),
            asyncio.create_task(self._file_watcher()),
            asyncio.create_task(self._health_checker())
        ]
        
        # Start scheduler if enabled
        if self.scheduler_config['enabled']:
            tasks.append(asyncio.create_task(self._scheduler()))
            logger.info("Scheduler started")
        
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
        
        # Close database manager if initialized
        if self.db_manager:
            try:
                await self.db_manager.close()
                logger.info("Database manager closed")
            except Exception as e:
                logger.error(f"Error closing database manager: {e}")
        
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
                # Check for new task files (excluding macOS hidden files)
                for task_file in self.task_dir.glob("*.json"):
                    # Skip macOS hidden files and processing files
                    if (task_file.name.startswith('._') or 
                        task_file.name.startswith('.DS_Store') or 
                        task_file.stem.endswith("_processing")):
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
                        # Try to clean up the problematic file
                        try:
                            if task_file.exists():
                                task_file.unlink()
                                logger.info(f"Removed problematic task file: {task_file.name}")
                        except:
                            pass
                
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
                    'config_valid': self.config.validate_config(),
                    'scheduler_enabled': self.scheduler_config['enabled'],
                    'pipeline_running': self.pipeline_running,
                    'task_stats': self.task_stats.copy(),
                    'last_scheduled_scrape': self.last_scheduled_scrape,
                    'next_scheduled_scrape': self._get_next_scheduled_scrape().isoformat() if self.scheduler_config['enabled'] else None,
                    'database_connected': self.db_manager is not None
                }
                
                # Save health status
                health_file = self.config.DATA_DIR / "worker_health.json"
                with open(health_file, 'w') as f:
                    json.dump(status, f, indent=2, cls=DateTimeJSONEncoder)
                
                logger.debug(f"Health check: {status}")
                
                await asyncio.sleep(self.config.WORKER_CONFIG['health_check_interval'])
                
            except Exception as e:
                logger.error(f"Error in health checker: {e}")
                await asyncio.sleep(60)
    
    async def _scheduler(self):
        """Scheduled task runner for automatic scraping"""
        logger.info(f"Scheduler started - running every {self.scheduler_config['scraping_interval_minutes']} minutes")
        
        while self.running:
            try:
                # Calculate next scheduled time
                now = datetime.now(timezone.utc)
                next_run = self._get_next_scheduled_scrape()
                
                # Wait until next scheduled time
                if now < next_run:
                    sleep_seconds = (next_run - now).total_seconds()
                    logger.info(f"Next scheduled scrape in {sleep_seconds/60:.1f} minutes at {next_run.isoformat()}")
                    await asyncio.sleep(min(sleep_seconds, 60))  # Check every minute
                    continue
                
                # Time to run scheduled scrape
                logger.info("Starting scheduled scraping pipeline")
                await self._run_scheduled_pipeline()
                
                # Update last run time
                self.last_scheduled_scrape = now.isoformat()
                
                # Small delay before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                await asyncio.sleep(60)
    
    def _get_next_scheduled_scrape(self) -> datetime:
        """Calculate the next scheduled scrape time"""
        now = datetime.now(timezone.utc)
        interval_minutes = self.scheduler_config['scraping_interval_minutes']
        
        if self.last_scheduled_scrape:
            try:
                last_run = datetime.fromisoformat(self.last_scheduled_scrape)
                next_run = last_run + timedelta(minutes=interval_minutes)
            except (ValueError, TypeError):
                # If parsing fails, schedule for next interval from now
                next_run = now + timedelta(minutes=interval_minutes)
        else:
            # First run - schedule for next interval
            next_run = now + timedelta(minutes=interval_minutes)
        
        # If next run is in the past, schedule for now + interval
        if next_run <= now:
            next_run = now + timedelta(minutes=interval_minutes)
        
        return next_run
    
    async def _run_scheduled_pipeline(self):
        """Run the complete data pipeline: scraping -> processing -> cleaning -> database loading"""
        if self.pipeline_running:
            logger.warning("Pipeline already running, skipping scheduled run")
            return
        
        self.pipeline_running = True
        pipeline_start = datetime.now(timezone.utc)
        
        try:
            logger.info("🚀 Starting automated data pipeline")
            self.task_stats['total_pipeline_runs'] += 1
            
            # Step 1: Scraping
            logger.info("📊 Step 1: Running Reddit scraping")
            scrape_result = await self._run_scheduled_scrape()
            
            if not scrape_result['success']:
                logger.error("Scraping failed, aborting pipeline")
                return
            
            # Step 2: Data Processing (if auto pipeline is enabled)
            if self.scheduler_config['auto_pipeline_enabled']:
                logger.info("⚙️ Step 2: Processing scraped data")
                process_result = await self._run_data_processing()
                
                # Step 3: Data Cleaning
                logger.info("🧹 Step 3: Cleaning and organizing data")
                clean_result = await self._run_data_cleaning()
                
                # Step 4: Database Loading
                if self.db_manager:
                    logger.info("💾 Step 4: Loading data to database")
                    db_result = await self._run_database_loading()
                else:
                    logger.warning("Database manager not available, skipping database loading")
                    db_result = {'success': False, 'message': 'Database not available'}
            
            # Pipeline completed successfully
            pipeline_duration = (datetime.now(timezone.utc) - pipeline_start).total_seconds()
            logger.info(f"✅ Pipeline completed successfully in {pipeline_duration:.1f} seconds")
            self.task_stats['last_pipeline_success'] = datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            self.task_stats['last_pipeline_failure'] = datetime.now(timezone.utc).isoformat()
        
        finally:
            self.pipeline_running = False
    
    async def _run_scheduled_scrape(self) -> Dict[str, Any]:
        """Run a scheduled Reddit scraping task"""
        try:
            self.task_stats['total_scrapes'] += 1
            
            # Prepare scraper config
            scraper_config = {
                **self.config.get_reddit_config(),
                'subreddit': self.config.get_scraping_config()['default_subreddit'],
                'post_limit': self.config.get_scraping_config()['default_post_limit'],
                'comment_limit': self.config.get_scraping_config()['default_comment_limit'],
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
            
            # Serialize the stats to handle datetime objects
            serialized_stats = serialize_datetime_objects(stats)
            
            logger.info(f"Scraping completed: {serialized_stats['new_posts_processed']} new posts, {serialized_stats['total_comments_collected']} comments")
            
            self.task_stats['successful_scrapes'] += 1
            
            return {
                'success': True,
                'stats': serialized_stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scheduled scraping failed: {e}")
            self.task_stats['failed_scrapes'] += 1
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def execute_pipeline_api(self, pipeline_request: Dict[str, Any]) -> str:
        """Execute pipeline via API call"""
        self.pipeline_counter += 1
        pipeline_id = f"pipeline_{int(time.time())}_{self.pipeline_counter}"
        
        # Create pipeline state
        pipeline_state = {
            'pipeline_id': pipeline_id,
            'status': 'queued',
            'current_step': None,
            'progress': 0.0,
            'steps_completed': [],
            'steps_failed': [],
            'started_at': None,
            'completed_at': None,
            'estimated_completion': None,
            'result': None,
            'error': None,
            'logs': [],
            'request': pipeline_request,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Store pipeline state
        self.active_pipelines[pipeline_id] = pipeline_state
        
        # Schedule pipeline execution
        asyncio.create_task(self._execute_api_pipeline(pipeline_id))
        
        logger.info(f"Pipeline {pipeline_id} queued for execution")
        return pipeline_id
    
    async def _execute_api_pipeline(self, pipeline_id: str):
        """Execute a single pipeline instance"""
        pipeline_state = self.active_pipelines.get(pipeline_id)
        if not pipeline_state:
            logger.error(f"Pipeline {pipeline_id} not found")
            return
        
        try:
            # Update status to running
            pipeline_state['status'] = 'running'
            pipeline_state['started_at'] = datetime.now(timezone.utc).isoformat()
            pipeline_state['current_step'] = 'initializing'
            pipeline_state['progress'] = 5.0
            self._log_pipeline(pipeline_id, "Pipeline execution started")
            
            request = pipeline_state['request']
            total_steps = sum([
                1,  # scraping (always)
                1 if request.get('enable_processing', True) else 0,
                1 if request.get('enable_cleaning', True) else 0,
                1 if request.get('enable_database', True) else 0
            ])
            
            step_progress = 100.0 / total_steps
            current_progress = 10.0
            
            # Step 1: Scraping (always executed)
            pipeline_state['current_step'] = 'scraping'
            pipeline_state['progress'] = current_progress
            self._log_pipeline(pipeline_id, "Starting Reddit scraping")
            
            scrape_result = await self._run_api_scrape(request)
            
            if scrape_result['success']:
                pipeline_state['steps_completed'].append('scraping')
                current_progress += step_progress
                pipeline_state['progress'] = min(current_progress, 95.0)
                self._log_pipeline(pipeline_id, f"Scraping completed: {scrape_result['stats']['new_posts_processed']} posts")
            else:
                pipeline_state['steps_failed'].append('scraping')
                raise Exception(f"Scraping failed: {scrape_result.get('error', 'Unknown error')}")
            
            # Step 2: Data Processing (optional)
            if request.get('enable_processing', True):
                pipeline_state['current_step'] = 'processing'
                pipeline_state['progress'] = current_progress
                self._log_pipeline(pipeline_id, "Starting data processing")
                
                process_result = await self._run_data_processing()
                
                if process_result['success']:
                    pipeline_state['steps_completed'].append('processing')
                    current_progress += step_progress
                    pipeline_state['progress'] = min(current_progress, 95.0)
                    self._log_pipeline(pipeline_id, "Data processing completed")
                else:
                    pipeline_state['steps_failed'].append('processing')
                    self._log_pipeline(pipeline_id, f"Data processing failed: {process_result.get('error', 'Unknown error')}")
                    # Continue with next step even if processing fails
            
            # Step 3: Data Cleaning (optional)
            if request.get('enable_cleaning', True):
                pipeline_state['current_step'] = 'cleaning'
                pipeline_state['progress'] = current_progress
                self._log_pipeline(pipeline_id, "Starting data cleaning")
                
                clean_result = await self._run_data_cleaning()
                
                if clean_result['success']:
                    pipeline_state['steps_completed'].append('cleaning')
                    current_progress += step_progress
                    pipeline_state['progress'] = min(current_progress, 95.0)
                    self._log_pipeline(pipeline_id, "Data cleaning completed")
                else:
                    pipeline_state['steps_failed'].append('cleaning')
                    self._log_pipeline(pipeline_id, f"Data cleaning failed: {clean_result.get('error', 'Unknown error')}")
            
            # Step 4: Database Loading (optional)
            if request.get('enable_database', True):
                pipeline_state['current_step'] = 'database'
                pipeline_state['progress'] = current_progress
                self._log_pipeline(pipeline_id, "Starting database loading")
                
                db_result = await self._run_database_loading()
                
                if db_result['success']:
                    pipeline_state['steps_completed'].append('database')
                    current_progress += step_progress
                    pipeline_state['progress'] = 100.0
                    self._log_pipeline(pipeline_id, "Database loading completed")
                else:
                    pipeline_state['steps_failed'].append('database')
                    self._log_pipeline(pipeline_id, f"Database loading failed: {db_result.get('error', 'Unknown error')}")
            
            # Pipeline completed
            pipeline_state['status'] = 'completed'
            pipeline_state['current_step'] = None
            pipeline_state['progress'] = 100.0
            pipeline_state['completed_at'] = datetime.now(timezone.utc).isoformat()
            
            # Compile results
            pipeline_state['result'] = {
                'scraping': scrape_result,
                'processing': process_result if request.get('enable_processing', True) else {'skipped': True},
                'cleaning': clean_result if request.get('enable_cleaning', True) else {'skipped': True},
                'database': db_result if request.get('enable_database', True) else {'skipped': True},
                'total_steps': total_steps,
                'completed_steps': len(pipeline_state['steps_completed']),
                'failed_steps': len(pipeline_state['steps_failed'])
            }
            
            self._log_pipeline(pipeline_id, "Pipeline execution completed successfully")
            logger.info(f"Pipeline {pipeline_id} completed successfully")
            
        except Exception as e:
            # Pipeline failed
            pipeline_state['status'] = 'failed'
            pipeline_state['error'] = str(e)
            pipeline_state['completed_at'] = datetime.now(timezone.utc).isoformat()
            self._log_pipeline(pipeline_id, f"Pipeline execution failed: {str(e)}")
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
        
        finally:
            # Move to history and clean up
            await self._finalize_pipeline(pipeline_id)
    
    async def _run_api_scrape(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Run scraping for API pipeline"""
        try:
            # Prepare scraper config from request
            scraper_config = {
                **self.config.get_reddit_config(),
                'subreddit': request.get('subreddit', 'UCLA'),
                'post_limit': request.get('post_limit', 100),
                'comment_limit': request.get('comment_limit', 50),
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
            
            # Serialize the stats to handle datetime objects
            serialized_stats = serialize_datetime_objects(stats)
            
            return {
                'success': True,
                'stats': serialized_stats,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"API scraping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _log_pipeline(self, pipeline_id: str, message: str):
        """Add log entry to pipeline state"""
        if pipeline_id in self.active_pipelines:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = f"[{timestamp}] {message}"
            self.active_pipelines[pipeline_id]['logs'].append(log_entry)
            # Keep only last 50 log entries
            if len(self.active_pipelines[pipeline_id]['logs']) > 50:
                self.active_pipelines[pipeline_id]['logs'] = self.active_pipelines[pipeline_id]['logs'][-50:]
    
    async def _finalize_pipeline(self, pipeline_id: str):
        """Move completed pipeline to history and save state"""
        if pipeline_id not in self.active_pipelines:
            return
        
        pipeline_state = self.active_pipelines[pipeline_id]
        
        # Add to history
        self.pipeline_history.append({
            'pipeline_id': pipeline_id,
            'status': pipeline_state['status'],
            'started_at': pipeline_state['started_at'],
            'completed_at': pipeline_state['completed_at'],
            'duration_seconds': self._calculate_duration(pipeline_state),
            'steps_completed': len(pipeline_state['steps_completed']),
            'steps_failed': len(pipeline_state['steps_failed']),
            'error': pipeline_state.get('error'),
            'request_summary': {
                'subreddit': pipeline_state['request'].get('subreddit', 'UCLA'),
                'post_limit': pipeline_state['request'].get('post_limit', 100),
                'enable_processing': pipeline_state['request'].get('enable_processing', True),
                'enable_cleaning': pipeline_state['request'].get('enable_cleaning', True),
                'enable_database': pipeline_state['request'].get('enable_database', True)
            }
        })
        
        # Keep only last N history items
        if len(self.pipeline_history) > self.max_history_items:
            self.pipeline_history = self.pipeline_history[-self.max_history_items:]
        
        # Save detailed pipeline state to file
        try:
            pipeline_file = self.pipelines_dir / f"{pipeline_id}.json"
            with open(pipeline_file, 'w') as f:
                json.dump(pipeline_state, f, indent=2, cls=DateTimeJSONEncoder)
        except Exception as e:
            logger.error(f"Failed to save pipeline state: {e}")
        
        # Remove from active pipelines
        del self.active_pipelines[pipeline_id]
    
    def _calculate_duration(self, pipeline_state: Dict[str, Any]) -> float:
        """Calculate pipeline duration in seconds"""
        try:
            if pipeline_state['started_at'] and pipeline_state['completed_at']:
                started = datetime.fromisoformat(pipeline_state['started_at'])
                completed = datetime.fromisoformat(pipeline_state['completed_at'])
                return (completed - started).total_seconds()
        except Exception:
            pass
        return 0.0
    
    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a pipeline"""
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id].copy()
        
        # Check if in history
        for pipeline in self.pipeline_history:
            if pipeline['pipeline_id'] == pipeline_id:
                # Try to load detailed state from file
                try:
                    pipeline_file = self.pipelines_dir / f"{pipeline_id}.json"
                    if pipeline_file.exists():
                        with open(pipeline_file, 'r') as f:
                            return json.load(f)
                except Exception:
                    pass
                # Return summary from history
                return pipeline
        
        return None
    
    def get_pipeline_history(self, limit: int = 20) -> Dict[str, Any]:
        """Get pipeline execution history"""
        recent_pipelines = self.pipeline_history[-limit:] if self.pipeline_history else []
        
        # Calculate statistics
        total_executions = len(self.pipeline_history)
        successful_executions = len([p for p in self.pipeline_history if p['status'] == 'completed'])
        failed_executions = len([p for p in self.pipeline_history if p['status'] == 'failed'])
        
        # Calculate average duration
        durations = [p['duration_seconds'] for p in self.pipeline_history if p.get('duration_seconds', 0) > 0]
        average_duration_minutes = (sum(durations) / len(durations) / 60.0) if durations else 0.0
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'average_duration_minutes': average_duration_minutes,
            'recent_executions': recent_pipelines,
            'active_pipelines': len(self.active_pipelines),
            'next_scheduled': self._get_next_scheduled_scrape().isoformat() if self.scheduler_config['enabled'] else None
        }
    
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        if pipeline_id in self.active_pipelines:
            pipeline_state = self.active_pipelines[pipeline_id]
            if pipeline_state['status'] in ['queued', 'running']:
                pipeline_state['status'] = 'cancelled'
                pipeline_state['completed_at'] = datetime.now(timezone.utc).isoformat()
                pipeline_state['error'] = 'Pipeline cancelled by user request'
                self._log_pipeline(pipeline_id, "Pipeline cancelled by user request")
                
                # Move to history
                asyncio.create_task(self._finalize_pipeline(pipeline_id))
                
                logger.info(f"Pipeline {pipeline_id} cancelled")
                return True
        
        return False
    
    def get_active_pipelines(self) -> Dict[str, Dict[str, Any]]:
        """Get all currently active pipelines"""
        return {pid: state.copy() for pid, state in self.active_pipelines.items()}
    
    async def _run_data_processing(self) -> Dict[str, Any]:
        """Run data processing on scraped data"""
        try:
            # Initialize processor
            processor = RedditDataProcessor(self.config.get_processing_config())
            
            # TODO: Implement actual data processing
            # For now, return a placeholder result
            logger.info("Data processing completed (placeholder)")
            
            return {
                'success': True,
                'message': 'Data processing completed',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _run_data_cleaning(self) -> Dict[str, Any]:
        """Run data cleaning and organization"""
        try:
            # Clean up old data if configured
            cleanup_hours = self.scheduler_config.get('cleanup_old_data_hours', 24)
            
            # TODO: Implement data cleaning logic
            # - Remove duplicate posts/comments
            # - Clean up old temporary files
            # - Organize data by date/subreddit
            
            logger.info(f"Data cleaning completed (cleanup window: {cleanup_hours} hours)")
            
            return {
                'success': True,
                'message': f'Data cleaning completed',
                'cleanup_hours': cleanup_hours,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data cleaning failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _run_database_loading(self) -> Dict[str, Any]:
        """Load processed data into database"""
        try:
            if not self.db_manager:
                return {
                    'success': False,
                    'error': 'Database manager not available',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            
            # TODO: Implement database loading logic
            # - Load recent posts and comments from parquet files
            # - Run sentiment analysis on new content
            # - Store results in database
            # - Update analytics tables
            
            logger.info("Database loading completed (placeholder)")
            
            return {
                'success': True,
                'message': 'Database loading completed',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database loading failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
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
            
            # Serialize datetime objects before saving
            serialized_result = serialize_datetime_objects(result)
            
            # Save result
            result_file = self.results_dir / f"{task_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(serialized_result, f, indent=2, cls=DateTimeJSONEncoder)
            
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
                'task_data': serialize_datetime_objects(task_data)
            }
            
            error_file = self.results_dir / f"{task_file.stem}_error.json"
            with open(error_file, 'w') as f:
                json.dump(error_result, f, indent=2, cls=DateTimeJSONEncoder)
            
            # Remove processing file
            if task_file.exists():
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
        
        # Serialize the stats to handle datetime objects
        serialized_stats = serialize_datetime_objects(stats)
        
        result = {
            'status': 'completed',
            'type': 'scrape_reddit',
            'stats': serialized_stats,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'task_data': serialize_datetime_objects(task_data)
        }
        
        logger.info(f"Reddit scraping completed: {serialized_stats}")
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
