"""
Gap Analysis API endpoints.
Separate from onboarding - can be called anytime after onboarding.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from app.db import get_db
from app.api.v1.auth import get_current_user
from app.models import User, ControlSelection, Framework, Control, Policy
from app.services.gap_analysis_service import run_gap_analysis_for_control, get_selected_controls
from app.services.pinecone_service import query_similar_policies
from app.services.ai_service import generate_gap_analysis
from datetime import datetime

router = APIRouter()


@router.post("/run")
async def run_gap_analysis(
    framework_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run AI gap analysis for selected frameworks and controls.
    This endpoint can be called anytime after onboarding.
    
    Args:
        framework_id: Optional framework ID to filter analysis. If not provided, analyzes all selected frameworks.
    
    Returns:
        Dictionary with analysis results organized by framework.
    """
    company = current_user.company
    
    if not company:
        raise HTTPException(
            status_code=400,
            detail="User must be associated with a company"
        )
    
    # PART 1 & 2: Use get_selected_controls helper function
    # Get list of frameworks to analyze
    if framework_id:
        # Single framework
        frameworks_to_analyze = [framework_id]
    else:
        # All frameworks with control selections
        control_selections = db.query(ControlSelection).filter(
            ControlSelection.company_id == company.id
        ).all()
        frameworks_to_analyze = list(set([cs.framework_id for cs in control_selections]))
    
    if not frameworks_to_analyze:
        print(f"[Gap Analysis API] No control selections found for company {company.id}")
        return {
            "framework_id": None,
            "framework_name": None,
            "results": [],
            "warning": "No controls selected during onboarding. Please select controls before running gap analysis.",
            "total_controls": 0,
            "gaps_identified": 0
        }
    
    # PART 6: TABULAR GAP RESPONSE (UI READY)
    # Organize by framework with tabular format
    framework_results_map = {}
    total_controls = 0
    total_gaps = 0
    
    for fw_id in frameworks_to_analyze:
        framework = db.query(Framework).filter(Framework.id == fw_id).first()
        if not framework:
            print(f"[Gap Analysis API] Framework {fw_id} not found, skipping")
            continue
        
        framework_name = framework.name
        framework_id = framework.id
        
        # PART 2: Use get_selected_controls helper function
        controls = get_selected_controls(db, company.id, framework_id)
        
        if not controls:
            print(f"[Gap Analysis API] No selected controls for framework {framework_id} (company {company.id})")
            # Add warning but continue to other frameworks
            if framework_id not in framework_results_map:
                framework_results_map[framework_id] = {
                    "framework": framework_name,
                    "results": []
                }
            continue
        
        if framework_id not in framework_results_map:
            framework_results_map[framework_id] = {
                "framework": framework_name,
                "results": []
            }
        
        print(f"[Gap Analysis API] Analyzing {len(controls)} selected controls for framework {framework_name} (ID: {framework_id})")
        
        # Run analysis for each selected control
        for control in controls:
            control_id = control.id
            total_controls += 1
            print(f"[Gap Analysis API] Analyzing control: {control.code or control.name} (ID: {control_id})")
            
            try:
                # PART 1: Run gap analysis for this control (now returns error status instead of raising)
                result = run_gap_analysis_for_control(
                    control_id=control_id,
                    company_id=company.id,
                    user_id=current_user.id,
                    db=db
                )
                
                # PART 5: Handle ERROR status from gap analysis service
                if result.get("status") == "ERROR":
                    print(f"[Gap Analysis API] Control {control_id} returned ERROR status: {result.get('reason')}")
                    framework_results_map[framework_id]["results"].append({
                        "control_id": control_id,
                        "control_code": result.get("control_code") or f"Control ID {control_id}",
                        "status": "ERROR",
                        "severity": None,
                        "risk_score": 0,
                        "reason": result.get("reason", "Control not found in database")
                    })
                    continue
                
                # Format result in tabular format
                gap_identified = result.get("gap_identified", False)
                if gap_identified:
                    total_gaps += 1
                
                # PART 7: RETURN RESULTS TO UI (NO AUTO REDIRECT)
                # Format response to match exact specification
                control_code = result.get("control_code") or control.code or ""
                
                # Get reason - prefer missing requirements if available
                reason = result.get("reason", "")
                if not reason:
                    missing_reqs = result.get("missing_requirements", [])
                    if missing_reqs:
                        reason = ", ".join(missing_reqs[:2])  # Limit to 2 requirements for brevity
                    else:
                        reason = "Control requirement not fully covered" if gap_identified else "Control requirements fully covered"
                
                # Format severity to uppercase
                severity = result.get("severity", "medium")
                if severity:
                    severity = severity.upper()
                
                # Get risk score
                risk_score = result.get("risk_score", 0)
                if not gap_identified:
                    risk_score = 100  # Compliant = 100% (no risk)
                
                # Create tabular result entry matching exact specification
                control_result = {
                    "control_code": control_code,  # PART 7: Use control_code (not combined control)
                    "status": result.get("status", "GAP" if gap_identified else "COMPLIANT"),
                    "severity": severity if gap_identified else None,
                    "risk_score": int(risk_score),  # PART 7: Use risk_score (not risk)
                    "reason": reason
                }
                
                framework_results_map[framework_id]["results"].append(control_result)
                
            except Exception as e:
                import traceback
                print(f"[Gap Analysis API] Error analyzing control {control_id}: {str(e)}")
                print(f"[Gap Analysis API] Traceback:\n{traceback.format_exc()}")
                
                # PART 5: SAFE GAP ANALYSIS RESPONSE - Never crash, return ERROR status
                control_code = control.code if control else f"Control ID {control_id}"
                
                framework_results_map[framework_id]["results"].append({
                    "control_id": control_id,
                    "control_code": control_code,
                    "status": "ERROR",
                    "severity": None,
                    "risk_score": 0,
                    "reason": f"Error analyzing control: {str(e)}"
                })
                continue
    
    # Convert to list format (one entry per framework)
    frameworks_list = list(framework_results_map.values())
    
    # Calculate gaps from results
    calculated_gaps = 0
    for fw in frameworks_list:
        for result in fw.get("results", []):
            if result.get("status") == "GAP":
                calculated_gaps += 1
    
    print(f"[Gap Analysis API] Summary: {total_controls} controls analyzed, {calculated_gaps} gaps identified")
    
    # Always include summary totals
    response_data = {
        "total_controls": total_controls,
        "gaps_identified": calculated_gaps or total_gaps,
        "total_gaps": calculated_gaps or total_gaps
    }
    
    # PART 4: Never return silent zero results
    if total_controls == 0:
        print(f"[Gap Analysis API] WARNING: No controls were analyzed!")
        # Return warning for each framework that had no controls
        for fw_id, fw_data in framework_results_map.items():
            if len(fw_data.get("results", [])) == 0:
                framework = db.query(Framework).filter(Framework.id == fw_id).first()
                return {
                    "framework_id": fw_id,
                    "framework_name": framework.name if framework else "Unknown",
                    "results": [],
                    "warning": "Gap analysis ran but no controls were analyzed. Check control selections.",
                    "total_controls": 0,
                    "gaps_identified": 0
                }
        # Fallback if no frameworks in map
        return {
            "framework_id": None,
            "framework_name": None,
            "results": [],
            "warning": "Gap analysis ran but no controls were analyzed. Check control selections.",
            "total_controls": 0,
            "gaps_identified": 0
        }
    
    # If only one framework, return single framework format with totals
    if len(frameworks_list) == 1:
        response_data.update(frameworks_list[0])
        return response_data
    
    # Multiple frameworks - return list with totals
    response_data["frameworks"] = frameworks_list
    return response_data

