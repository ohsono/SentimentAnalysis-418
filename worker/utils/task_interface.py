#!/usr/bin/env python3

"""
Task Interface for Worker Communication
Simple file-based communication between web service and worker
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import asyncio

logger = logging.getLogger(__name__)

class TaskInterface:
    """Interface for submitting tasks to and getting results from workers"""
    
    def __init__(self, worker_data_dir: Path):
        self.worker_data_dir = Path(worker_data_dir)
        self.task_dir = self.worker_data_dir / "tasks"
        self.results_dir = self.worker_data_dir / "results"
        
        # Ensure directories exist
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def submit_task(self, task_type: str, task_data: Dict[str, Any]) -> str:
        """
        Submit a task to the worker
        
        Args:
            task_type: Type of task ('scrape_reddit', 'process_data', 'generate_report')
            task_data: Task parameters
            
        Returns:
            Task ID
        """
        task_id = f"{task_type}_{int(time.time())}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'submitted_by': 'web_service',
            **task_data
        }
        
        try:
            task_file = self.task_dir / f"{task_id}.json"
            with open(task_file, 'w') as f:
                json.dump(task, f, indent=2)
            
            logger.info(f"Submitted task {task_id} of type {task_type}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a task
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result or None if not available
        """
        try:
            # Check for completed result
            result_file = self.results_dir / f"{task_id}_result.json"
            if result_file.exists():
                with open(result_file, 'r') as f:
                    result = json.load(f)
                return result
            
            # Check for error result
            error_file = self.results_dir / f"{task_id}_error.json"
            if error_file.exists():
                with open(error_file, 'r') as f:
                    result = json.load(f)
                return result
            
            # Check if still processing
            processing_file = self.task_dir / f"{task_id}_processing.json"
            if processing_file.exists():
                return {
                    'status': 'processing',
                    'message': 'Task is still being processed'
                }
            
            # Check if task exists but not started
            task_file = self.task_dir / f"{task_id}.json"
            if task_file.exists():
                return {
                    'status': 'queued',
                    'message': 'Task is queued for processing'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting task result: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_task_status(self, task_id: str) -> str:
        """
        Get the status of a task
        
        Returns: 'queued', 'processing', 'completed', 'error', 'not_found'
        """
        result = self.get_task_result(task_id)
        if result is None:
            return 'not_found'
        return result.get('status', 'unknown')
    
    def list_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent tasks and their statuses"""
        tasks = []
        
        try:
            # Get all task files
            all_files = []
            all_files.extend(self.task_dir.glob("*.json"))
            all_files.extend(self.results_dir.glob("*_result.json"))
            all_files.extend(self.results_dir.glob("*_error.json"))
            
            # Sort by modification time
            all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file_path in all_files[:limit]:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    task_info = {
                        'task_id': data.get('id', file_path.stem),
                        'type': data.get('type', 'unknown'),
                        'status': data.get('status', 'unknown'),
                        'created_at': data.get('created_at'),
                        'file_path': str(file_path)
                    }
                    
                    tasks.append(task_info)
                    
                except Exception as e:
                    logger.warning(f"Error reading task file {file_path}: {e}")
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old task and result files"""
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            cleaned_count = 0
            
            # Clean task files
            for task_file in self.task_dir.glob("*.json"):
                if task_file.stat().st_mtime < cutoff_time:
                    task_file.unlink()
                    cleaned_count += 1
            
            # Clean result files
            for result_file in self.results_dir.glob("*.json"):
                if result_file.stat().st_mtime < cutoff_time:
                    result_file.unlink()
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old task files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
            return 0
    
    def get_worker_health(self) -> Dict[str, Any]:
        """Get worker health status"""
        try:
            health_file = self.worker_data_dir / "worker_health.json"
            if health_file.exists():
                with open(health_file, 'r') as f:
                    health_data = json.load(f)
                
                # Check if health data is recent (within last 10 minutes)
                health_time = datetime.fromisoformat(health_data['timestamp'].replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                age_minutes = (current_time - health_time).total_seconds() / 60
                
                if age_minutes > 10:
                    health_data['status'] = 'stale'
                    health_data['age_minutes'] = age_minutes
                
                return health_data
            else:
                return {
                    'status': 'unknown',
                    'message': 'Worker health file not found'
                }
                
        except Exception as e:
            logger.error(f"Error getting worker health: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

# Factory function for easy import
def create_task_interface(worker_data_dir: str = "worker/data") -> TaskInterface:
    """Create a task interface instance"""
    return TaskInterface(Path(worker_data_dir))
