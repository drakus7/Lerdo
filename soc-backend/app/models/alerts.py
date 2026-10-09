from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum
from uuid import UUID

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class AlertStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    escalated = "escalated"
    closed = "closed"

class Alert(BaseModel):
    """What an alert looks like when returned to the client."""
    id: UUID
    timestamp: datetime
    severity: Severity
    category: str
    mitre_technique: str
    status: AlertStatus
    assigned_analyst: str
    rule_name: str

class AlertUpdateStatus(BaseModel):
    """Body for PATCH /alerts/{id}/status"""
    status: AlertStatus

class AlertAssign(BaseModel):
    """Body for PATCH /alerts/{id}/assign"""
    assigned_analyst: str