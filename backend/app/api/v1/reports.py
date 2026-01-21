"""
Reports API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import Dict, Any, List
from app.db import get_db
from app.models import Gap, Control, Framework, User, GapStatus, GapSeverity
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/reports/risk-gap")
async def generate_risk_gap_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Generate Risk & Gap Report for the current user's company.
    
    Returns:
        Dictionary with summary and risks list
    """
    # Get company from user
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with a company"
        )
    
    company_id = current_user.company_id
    
    # Query gaps with joins to get control and framework information
    # Filter by company through identified_by user
    from app.models import ControlGroup
    gaps = (
        db.query(Gap)
        .join(User, Gap.identified_by_id == User.id)
        .join(Control, Gap.control_id == Control.id, isouter=True)
        .join(Framework, Gap.framework_id == Framework.id, isouter=True)
        .options(
            joinedload(Gap.remediations),
            joinedload(Gap.control).joinedload(Control.control_group)
        )
        .filter(
            User.company_id == company_id,
            Gap.status == GapStatus.IDENTIFIED,
            Gap.is_active == True
        )
        .order_by(
            desc(Gap.severity),
            desc(Gap.risk_score),
            desc(Gap.identified_date)
        )
        .all()
    )
    
    # Calculate summary statistics
    total_gaps = len(gaps)
    
    # Count by severity/risk
    high_risk = sum(1 for g in gaps if g.risk_score and g.risk_score >= 60)
    medium_risk = sum(1 for g in gaps if g.risk_score and 40 <= g.risk_score < 60)
    low_risk = sum(1 for g in gaps if g.risk_score and g.risk_score < 40)
    
    # Get unique controls count
    unique_controls = len(set(g.control_id for g in gaps if g.control_id))
    total_controls = unique_controls  # Use unique controls as total
    
    # Build risks list
    risks = []
    for gap in gaps:
        # Get control and framework info
        control = gap.control
        framework = gap.framework
        
        # Determine impacted area (default to control group or framework)
        impacted_area = "General"
        if control and control.control_group:
            impacted_area = control.control_group.name or "General"
        elif framework:
            impacted_area = framework.name or "General"
        
        # Get recommended action from remediation if available
        recommended_action = "Review and address the identified gap"
        if gap.remediations:
            # Get the first active remediation
            active_remediation = next(
                (r for r in gap.remediations if r.is_active),
                None
            )
            if active_remediation and active_remediation.action_plan:
                # Extract first action item
                action_lines = active_remediation.action_plan.split('\n')
                if action_lines:
                    recommended_action = action_lines[0].strip()
                    # Remove numbering if present
                    recommended_action = recommended_action.lstrip('1234567890. -')
        
        # Build risk description from gap description or root cause
        risk_description = gap.description or gap.root_cause or "Gap identified in control"
        if len(risk_description) > 200:
            risk_description = risk_description[:200] + "..."
        
        # Map severity enum to string
        severity_str = gap.severity.value.upper() if gap.severity else "MEDIUM"
        
        risk_item = {
            "framework": framework.name if framework else "Unknown Framework",
            "control_code": control.code if control else f"Control ID {gap.control_id}",
            "control_name": control.name if control else gap.title,
            "gap_status": "GAP",
            "severity": severity_str,
            "risk_score": int(gap.risk_score) if gap.risk_score else 50,
            "risk_description": risk_description,
            "impacted_area": impacted_area,
            "recommended_action": recommended_action
        }
        
        risks.append(risk_item)
    
    # Build response
    response = {
        "summary": {
            "total_controls": total_controls,
            "total_gaps": total_gaps,
            "high_risk": high_risk,
            "medium_risk": medium_risk,
            "low_risk": low_risk
        },
        "risks": risks
    }
    
    return response

