import logging
from typing import Dict, List, Any
from datetime import datetime, timezone
import json
import os

logger = logging.getLogger(__name__)

class AlertService:
    """
    Handle alerts and notifications
    """
    def __init__(self, config: Dict =[Any, Any]):
        self.config = config or {}
        self.alerts = []  # In-memory storage for demo
        
    def create_alert(self, content: Dict[str, Any], alert_type: str, severity: str) -> Dict[str, Any]:
        """Create a new alert"""
        alert = {
            'id': f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts)}",
            'content_id': content.get('post_id') or content.get('comment_id'),
            'content_text': content.get('title', '') + ' ' + content.get('body', '') + content.get('selftext', ''),
            'alert_type': alert_type,
            'severity': severity,
            'timestamp': datetime.now(timezone.utc),
            'subreddit': content.get('subreddit'),
            'author': content.get('author'),
            'status': 'active'
        }
        
        self.alerts.append(alert)
        logger.warning(f"Alert created: {alert_type} - {severity}")
        
        return alert
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [alert for alert in self.alerts if alert['status'] == 'active']
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        active_alerts = self.get_active_alerts()
        
        stats = {
            'total_active': len(active_alerts),
            'by_severity': {},
            'by_type': {},
            'recent_count': 0
        }
        
        for alert in active_alerts:
            severity = alert['severity']
            alert_type = alert['alert_type']
            
            stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1
            stats['by_type'][alert_type] = stats['by_type'].get(alert_type, 0) + 1
            
            # Count recent alerts (last hour)
            alert_time = alert['timestamp']
            if isinstance(alert_time, str):
                alert_time = datetime.fromisoformat(alert_time.replace('Z', '+00:00'))
            
            time_diff = datetime.now(timezone.utc) - alert_time
            if time_diff.total_seconds() < 3600:  # 1 hour
                stats['recent_count'] += 1
        
        return stats
    
    def update_alert_status(self, alert_id: str, status: str) -> bool:
        """Update alert status"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['status'] = status
                alert['updated_at'] = datetime.now(timezone.utc)
                return True
        return False