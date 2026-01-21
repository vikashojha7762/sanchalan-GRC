from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FrameworkResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    category: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ControlGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    framework_id: int
    parent_group_id: Optional[int] = None
    order_index: Optional[int] = None
    is_active: bool
    controls_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ControlResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
    control_group_id: int
    status: str
    implementation_notes: Optional[str] = None
    evidence: Optional[str] = None
    order_index: Optional[int] = None
    is_active: bool

    class Config:
        from_attributes = True


class ControlTreeNode(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    type: str  # "group" or "control"
    children: Optional[List['ControlTreeNode']] = []

    class Config:
        from_attributes = True


# Update forward reference
ControlTreeNode.model_rebuild()


class ControlTreeResponse(BaseModel):
    framework_id: int
    framework_name: str
    tree: List[ControlTreeNode]
