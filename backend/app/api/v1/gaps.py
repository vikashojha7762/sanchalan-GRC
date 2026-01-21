from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.db import get_db
from app.models import Gap, Remediation, GapSeverity, GapStatus, RemediationStatus, User
from app.api.v1.auth import get_current_user
from app.schemas.gap import GapResponse, GapUpdate, RemediationCreate, RemediationResponse

router = APIRouter()


@router.get("", response_model=List[GapResponse])
async def get_gaps(
    framework_id: Optional[int] = None,
    control_id: Optional[int] = None,
    severity: Optional[str] = None,
    gap_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all gaps with optional filtering.
    """
    # Get all gaps (company filtering can be added if needed)
    query = db.query(Gap).filter(Gap.is_active == True)
    
    # Apply filters
    if framework_id:
        query = query.filter(Gap.framework_id == framework_id)
    
    if control_id:
        query = query.filter(Gap.control_id == control_id)
    
    if severity:
        try:
            severity_enum = GapSeverity(severity.lower())
            query = query.filter(Gap.severity == severity_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {severity}"
            )
    
    if gap_status:
        try:
            status_enum = GapStatus(gap_status.lower())
            query = query.filter(Gap.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {gap_status}"
            )
    
    gaps = query.order_by(Gap.identified_date.desc()).all()
    return gaps


@router.patch("/{gap_id}", response_model=GapResponse)
async def update_gap(
    gap_id: int,
    gap_update: GapUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a gap.
    """
    gap = db.query(Gap).filter(Gap.id == gap_id, Gap.is_active == True).first()
    
    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gap not found"
        )
    
    # Update fields
    if gap_update.title is not None:
        gap.title = gap_update.title
    if gap_update.description is not None:
        gap.description = gap_update.description
    if gap_update.severity is not None:
        try:
            gap.severity = GapSeverity(gap_update.severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity: {gap_update.severity}"
            )
    if gap_update.status is not None:
        try:
            gap.status = GapStatus(gap_update.status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {gap_update.status}"
            )
    if gap_update.assigned_to_id is not None:
        gap.assigned_to_id = gap_update.assigned_to_id
    if gap_update.risk_score is not None:
        gap.risk_score = gap_update.risk_score
    if gap_update.impact is not None:
        gap.impact = gap_update.impact
    if gap_update.root_cause is not None:
        gap.root_cause = gap_update.root_cause
    if gap_update.target_remediation_date is not None:
        gap.target_remediation_date = gap_update.target_remediation_date
    
    # Update status to IN_REMEDIATION if remediations exist
    if gap_update.status == GapStatus.IN_REMEDIATION.value:
        gap.status = GapStatus.IN_REMEDIATION
    
    db.commit()
    db.refresh(gap)
    
    return gap


@router.post("/{gap_id}/remediations", response_model=RemediationResponse, status_code=status.HTTP_201_CREATED)
async def create_remediation(
    gap_id: int,
    remediation_data: RemediationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a remediation for a gap.
    """
    # Verify gap exists
    gap = db.query(Gap).filter(Gap.id == gap_id, Gap.is_active == True).first()
    
    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gap not found"
        )
    
    # Create remediation
    remediation = Remediation(
        title=remediation_data.title,
        description=remediation_data.description,
        action_plan=remediation_data.action_plan,
        status=RemediationStatus.PLANNED,
        gap_id=gap_id,
        assigned_to_id=remediation_data.assigned_to_id or current_user.id,
        target_completion_date=remediation_data.target_completion_date,
        is_active=True
    )
    db.add(remediation)
    
    # Update gap status to IN_REMEDIATION
    if gap.status == GapStatus.IDENTIFIED:
        gap.status = GapStatus.IN_REMEDIATION
    
    db.commit()
    db.refresh(remediation)
    
    return remediation
