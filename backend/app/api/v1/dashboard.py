from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db import get_db
from app.models import (
    Framework, Control, Policy, Gap, Remediation,
    GapSeverity, GapStatus, RemediationStatus, User
)
from app.api.v1.auth import get_current_user
from app.schemas.dashboard import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary statistics.
    """
    company_id = current_user.company_id
    
    # Total frameworks
    total_frameworks = db.query(func.count(Framework.id)).filter(
        Framework.is_active == True
    ).scalar()
    
    # Total controls
    total_controls = db.query(func.count(Control.id)).filter(
        Control.is_active == True
    ).scalar()
    
    # Total policies (for company)
    total_policies = db.query(func.count(Policy.id)).join(
        User, Policy.owner_id == User.id
    ).filter(
        User.company_id == company_id,
        Policy.is_active == True
    ).scalar()
    
    # Total gaps (for company through framework)
    from app.models import ControlGroup
    total_gaps = db.query(func.count(Gap.id)).join(
        Framework, Gap.framework_id == Framework.id, isouter=True
    ).filter(
        Gap.is_active == True
    ).scalar()
    
    # Gaps by severity
    gaps_by_severity = {}
    for severity in GapSeverity:
        count = db.query(func.count(Gap.id)).filter(
            Gap.severity == severity,
            Gap.is_active == True
        ).scalar()
        gaps_by_severity[severity.value] = count
    
    # Gaps by status
    gaps_by_status = {}
    for gap_status in GapStatus:
        count = db.query(func.count(Gap.id)).filter(
            Gap.status == gap_status,
            Gap.is_active == True
        ).scalar()
        gaps_by_status[gap_status.value] = count
    
    # Total remediations
    total_remediations = db.query(func.count(Remediation.id)).filter(
        Remediation.is_active == True
    ).scalar()
    
    # Remediations by status
    remediations_by_status = {}
    for rem_status in RemediationStatus:
        count = db.query(func.count(Remediation.id)).filter(
            Remediation.status == rem_status,
            Remediation.is_active == True
        ).scalar()
        remediations_by_status[rem_status.value] = count
    
    # Calculate compliance score (simplified: based on closed gaps vs total gaps)
    closed_gaps = gaps_by_status.get("closed", 0)
    compliance_score = None
    if total_gaps > 0:
        compliance_score = round((closed_gaps / total_gaps) * 100, 2)
    
    # Recent gaps (last 5)
    recent_gaps = db.query(Gap).filter(
        Gap.is_active == True
    ).order_by(Gap.identified_date.desc()).limit(5).all()
    
    recent_gaps_list = [
        {
            "id": gap.id,
            "title": gap.title,
            "severity": gap.severity.value,
            "status": gap.status.value,
            "identified_date": gap.identified_date.isoformat()
        }
        for gap in recent_gaps
    ]
    
    # Recent policies (last 5)
    recent_policies = db.query(Policy).join(
        User, Policy.owner_id == User.id
    ).filter(
        User.company_id == company_id,
        Policy.is_active == True
    ).order_by(Policy.created_at.desc()).limit(5).all()
    
    recent_policies_list = [
        {
            "id": policy.id,
            "title": policy.title,
            "status": policy.status.value,
            "created_at": policy.created_at.isoformat()
        }
        for policy in recent_policies
    ]
    
    return DashboardSummary(
        total_frameworks=total_frameworks,
        total_controls=total_controls,
        total_policies=total_policies,
        total_gaps=total_gaps,
        gaps_by_severity=gaps_by_severity,
        gaps_by_status=gaps_by_status,
        total_remediations=total_remediations,
        remediations_by_status=remediations_by_status,
        compliance_score=compliance_score,
        recent_gaps=recent_gaps_list,
        recent_policies=recent_policies_list
    )
