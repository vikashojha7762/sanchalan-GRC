from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class PolicyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    policy_number: Optional[str] = None
    version: Optional[str] = None
    framework_id: Optional[int] = None
    control_id: Optional[int] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None


class PolicyResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    policy_number: Optional[str] = None
    version: Optional[str] = None
    status: str
    framework_id: Optional[int] = None
    control_id: Optional[int] = None
    owner_id: Optional[int] = None
    effective_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
