from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.db import get_db
from app.models import Framework, ControlGroup, Control
from app.api.v1.auth import get_current_user
from app.models import User
from app.schemas.framework import (
    FrameworkResponse,
    ControlGroupResponse,
    ControlResponse,
    ControlTreeNode,
    ControlTreeResponse
)
from app.utils.seed_iso27001 import seed_iso27001

router = APIRouter()


@router.get("", response_model=List[FrameworkResponse])
async def get_frameworks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active frameworks.
    """
    frameworks = db.query(Framework).filter(Framework.is_active == True).order_by(Framework.name).all()
    return frameworks


@router.get("/{framework_id}/control-groups", response_model=List[ControlGroupResponse])
async def get_control_groups(
    framework_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all control groups for a specific framework.
    """
    # Verify framework exists
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framework not found"
        )
    
    # Get control groups with control counts
    control_groups = db.query(
        ControlGroup,
        func.count(Control.id).label('controls_count')
    ).outerjoin(
        Control, ControlGroup.id == Control.control_group_id
    ).filter(
        ControlGroup.framework_id == framework_id,
        ControlGroup.is_active == True
    ).group_by(ControlGroup.id).order_by(ControlGroup.order_index, ControlGroup.code).all()
    
    result = []
    for group, count in control_groups:
        group_dict = {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "code": group.code,
            "framework_id": group.framework_id,
            "parent_group_id": group.parent_group_id,
            "order_index": group.order_index,
            "is_active": group.is_active,
            "controls_count": count or 0
        }
        result.append(ControlGroupResponse(**group_dict))
    
    return result


@router.get("/{framework_id}/controls", response_model=List[ControlResponse])
async def get_controls(
    framework_id: int,
    control_group_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all controls for a specific framework.
    Optionally filter by control_group_id.
    """
    # Verify framework exists
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framework not found"
        )
    
    # Build query
    query = db.query(Control).join(
        ControlGroup, Control.control_group_id == ControlGroup.id
    ).filter(
        ControlGroup.framework_id == framework_id,
        Control.is_active == True
    )
    
    if control_group_id:
        query = query.filter(Control.control_group_id == control_group_id)
    
    controls = query.order_by(ControlGroup.order_index, Control.order_index, Control.code).all()
    
    return controls


@router.get("/iso27001/control-tree", response_model=ControlTreeResponse)
async def get_iso27001_control_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the complete control tree for ISO 27001 framework.
    Returns hierarchical structure of control groups and controls.
    """
    # Find ISO 27001 framework
    framework = db.query(Framework).filter(
        Framework.name.ilike("%ISO 27001%")
    ).first()
    
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ISO 27001 framework not found"
        )
    
    # Get all control groups for this framework
    control_groups = db.query(ControlGroup).filter(
        ControlGroup.framework_id == framework.id,
        ControlGroup.is_active == True
    ).order_by(ControlGroup.order_index, ControlGroup.code).all()
    
    # Get all controls for this framework
    controls = db.query(Control).join(
        ControlGroup, Control.control_group_id == ControlGroup.id
    ).filter(
        ControlGroup.framework_id == framework.id,
        Control.is_active == True
    ).order_by(Control.order_index, Control.code).all()
    
    # Build tree structure
    # Group controls by control_group_id
    controls_by_group = {}
    for control in controls:
        if control.control_group_id not in controls_by_group:
            controls_by_group[control.control_group_id] = []
        controls_by_group[control.control_group_id].append(control)
    
    # Build tree nodes
    tree = []
    for group in control_groups:
        # Create control group node
        group_node = ControlTreeNode(
            id=group.id,
            name=group.name,
            code=group.code,
            description=group.description,
            type="group",
            children=[]
        )
        
        # Add controls as children
        if group.id in controls_by_group:
            for control in controls_by_group[group.id]:
                control_node = ControlTreeNode(
                    id=control.id,
                    name=control.name,
                    code=control.code,
                    description=control.description,
                    type="control",
                    children=[]
                )
                group_node.children.append(control_node)
        
        tree.append(group_node)
    
    return ControlTreeResponse(
        framework_id=framework.id,
        framework_name=framework.name,
        tree=tree
    )


@router.post("/seed/iso27001", response_model=FrameworkResponse, status_code=status.HTTP_201_CREATED)
async def seed_iso27001_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Seed ISO 27001:2022 framework with control groups A.5, A.6, A.7, A.8.
    This endpoint creates the framework and all controls if they don't exist.
    """
    framework = seed_iso27001(db)
    db.refresh(framework)
    return framework
