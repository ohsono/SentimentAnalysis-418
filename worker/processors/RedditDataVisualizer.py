#!/usr/bin/env python3

import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RedditDataVisualizer:
    """Visualizes processed Reddit data"""
    
    def __init__(self):
        """Initialize the visualizer"""
        self.output_dir = 'visualizations'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('seaborn')
        sns.set_palette("husl")
    
    def visualize_data(self, data: Dict[str, Any]) -> None:
        """
        Create visualizations from the processed data
        
        Args:
            data: Dictionary containing processed data and statistics
        """
        try:
            # Create timestamp for filenames
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create activity timeline
            self._create_activity_timeline(data, timestamp)
            
            # Create metrics summary
            self._create_metrics_summary(data, timestamp)
            
            logger.info(f"Successfully created visualizations in {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Error creating visualizations: {e}")
            raise
    
    def _create_activity_timeline(self, data: Dict[str, Any], timestamp: str) -> None:
        """Create a timeline visualization of scraping activity"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Ensure we have valid data points
            if not all(key in data for key in ['start_time', 'end_time', 'new_posts_processed', 'total_comments_collected']):
                logger.warning("Missing required data for timeline visualization")
                return
            
            # Create time points for x-axis
            time_points = [data['start_time'], data['end_time']]
            post_points = [0, data['new_posts_processed']]
            comment_points = [0, data['total_comments_collected']]
            
            # Plot posts and comments over time
            plt.plot(time_points, post_points, marker='o', label='Posts')
            plt.plot(time_points, comment_points, marker='o', label='Comments')
            
            plt.title('Reddit Data Collection Timeline')
            plt.xlabel('Time')
            plt.ylabel('Count')
            plt.legend()
            plt.grid(True)
            
            # Format x-axis dates
            plt.gcf().autofmt_xdate()
            
            # Save the plot
            plt.savefig(os.path.join(self.output_dir, f'activity_timeline_{timestamp}.png'))
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating activity timeline: {e}")
            raise
    
    def _create_metrics_summary(self, data: Dict[str, Any], timestamp: str) -> None:
        """Create a summary visualization of key metrics"""
        try:
            plt.figure(figsize=(10, 6))
            
            # Prepare metrics for visualization
            metrics = {
                'Posts per Minute': data.get('posts_per_minute', 0),
                'Comments per Minute': data.get('comments_per_minute', 0),
                'Total Posts': data.get('new_posts_processed', 0),
                'Total Comments': data.get('total_comments_collected', 0)
            }
            
            # Create bar plot
            plt.bar(metrics.keys(), metrics.values())
            plt.title('Reddit Data Collection Metrics')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            # Add value labels on top of bars
            for i, v in enumerate(metrics.values()):
                plt.text(i, v, f'{v:.1f}', ha='center', va='bottom')
            
            # Save the plot
            plt.savefig(os.path.join(self.output_dir, f'metrics_summary_{timestamp}.png'))
            plt.close()
            
        except Exception as e:
            logger.error(f"Error creating metrics summary: {e}")
            raise
