from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class GapResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    framework_id: Optional[int] = None
    control_id: Optional[int] = None
    policy_id: Optional[int] = None
    identified_by_id: Optional[int] = None
    assigned_to_id: Optional[int] = None
    risk_score: Optional[float] = None
    impact: Optional[str] = None
    root_cause: Optional[str] = None
    identified_date: datetime
    target_remediation_date: Optional[datetime] = None
    actual_remediation_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GapUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    assigned_to_id: Optional[int] = None
    risk_score: Optional[float] = None
    impact: Optional[str] = None
    root_cause: Optional[str] = None
    target_remediation_date: Optional[datetime] = None


class RemediationCreate(BaseModel):
    title: str
    description: Optional[str] = None
    action_plan: Optional[str] = None
    assigned_to_id: Optional[int] = None
    target_completion_date: Optional[datetime] = None


class RemediationResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    action_plan: Optional[str] = None
    status: str
    gap_id: int
    assigned_to_id: Optional[int] = None
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    verification_notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
