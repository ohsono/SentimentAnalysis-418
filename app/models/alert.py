from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Optional

class AlertSeverity(str, Enum):
    """
    What this does:
    - Defines the 4 levels of alert severity
    - CRITICAL: Immediate danger (suicide, violence)
    - HIGH: Serious concern (depression, harassment)
    - MEDIUM: Moderate concern (anxiety, stress)
    - LOW: Minor issues (general complaints)
    """
    CRITICAL = "critical"  # Requires immediate intervention
    HIGH = "high"         # Requires attention within 1 hour
    MEDIUM = "medium"     # Requires attention within 24 hours
    LOW = "low"          # For monitoring/trends


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"

class Alert(BaseModel):
    """
    What this does:
    - Structures all alert information
    - Tracks the lifecycle of an alert from creation to resolution
    - Links alerts back to original Reddit content
    """

    id: str
    content_id: str
    content_text: str
    alert_type: str
    severity: AlertSeverity
    keywords_found: List[str]
    timestamp: datetime
    subreddit: str
    author: str
    status: AlertStatus = AlertStatus.ACTIVE
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
