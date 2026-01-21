from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Company Update Schema
class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


# Department Schema
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    company_id: int
    is_active: bool

    class Config:
        from_attributes = True


# Role Schema
class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# Framework Schema
class FrameworkCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None


class FrameworkResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# ISO 27001 Control Configuration Schema
class ControlCreate(BaseModel):
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    order_index: Optional[int] = None


class ControlGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    order_index: Optional[int] = None
    controls: Optional[List[ControlCreate]] = []


class ISO27001ControlsConfig(BaseModel):
    control_groups: List[ControlGroupCreate]


# Policy Upload Schema
class PolicyUpload(BaseModel):
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    policy_number: Optional[str] = None
    version: Optional[str] = None
    framework_id: Optional[int] = None
    control_id: Optional[int] = None


class PolicyUploadResponse(BaseModel):
    id: int
    title: str
    policy_number: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


# Gap Analysis Schema
class GapAnalysisRequest(BaseModel):
    framework_id: Optional[int] = None
    run_ai_analysis: bool = True


class GapInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    severity: str
    status: str
    control_id: Optional[int] = None
    risk_score: Optional[float] = None
    root_cause: Optional[str] = None
    identified_date: datetime

    class Config:
        from_attributes = True


class GapAnalysisResponse(BaseModel):
    status: str
    message: str
    gaps_identified: int
    analysis_id: Optional[str] = None
    gaps: Optional[List[GapInfo]] = []


# Control Selection Schema
class ControlSelectionRequest(BaseModel):
    framework: str
    controls: List[int]
    framework_id: Optional[int] = None  # Optional framework ID for more accurate matching


class ControlSelectionResponse(BaseModel):
    message: str
    framework_id: int
    controls_count: int


# Onboarding Status Schema
class OnboardingStatus(BaseModel):
    company_configured: bool
    departments_configured: bool
    roles_configured: bool
    frameworks_configured: bool
    controls_configured: bool
    policies_uploaded: bool
    gap_analysis_completed: bool
    completion_percentage: int
    current_step: str
