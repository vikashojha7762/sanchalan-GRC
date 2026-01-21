"""
Gap Analysis Service.
Orchestrates the gap analysis workflow using AI and Pinecone.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import re
from app.models import (
    Framework, ControlGroup, Control, Policy, Gap, Remediation,
    GapSeverity, GapStatus, RemediationStatus, PolicyStatus, ControlSelection
)
from app.services.ai_service import get_embedding, generate_gap_analysis, extract_control_requirements
from app.services.pinecone_service import query_similar_policies, index_policy_embedding, query_knowledge_base_chunks
from app.core.config import settings

# PART 5: STRICT SIMILARITY RULES
SIMILARITY_MIN = 0.72  # Minimum similarity threshold for AI analysis
AUTO_COMPLIANT = 0.85  # Minimum similarity threshold for auto-compliant status


def calculate_risk_score(max_similarity: float) -> int:
    """
    FIX 3: Dynamic risk score calculation.
    risk_score = min(100, int((1 - max_similarity) * 100))
    If similarity is unavailable, default to 90.
    """
    if max_similarity > 0:
        return min(100, int((1 - max_similarity) * 100))
    else:
        return 90  # Default when similarity unavailable


def calculate_severity_from_risk(risk_score: int) -> tuple:
    """
    FIX 4: Calculate severity based on risk score.
    - HIGH if risk_score >= 75
    - MEDIUM if risk_score >= 40
    - LOW otherwise
    """
    if risk_score >= 75:
        return (GapSeverity.HIGH, "HIGH")
    elif risk_score >= 40:
        return (GapSeverity.MEDIUM, "MEDIUM")
    else:
        return (GapSeverity.LOW, "LOW")


def get_selected_controls(db: Session, company_id: int, framework_id: int) -> List[Control]:
    """
    Get selected controls for a company and framework from ControlSelection table.
    
    Args:
        db: Database session
        company_id: ID of the company
        framework_id: ID of the framework
    
    Returns:
        List of Control objects that were selected during onboarding
    """
    selection = (
        db.query(ControlSelection)
        .filter(
            ControlSelection.company_id == company_id,
            ControlSelection.framework_id == framework_id
        )
        .first()
    )
    
    if not selection or not selection.selected_control_ids:
        print(f"[Gap Analysis] No control selection found for company {company_id}, framework {framework_id}")
        return []
    
    # Handle both list and JSON array formats
    control_ids = selection.selected_control_ids
    if isinstance(control_ids, str):
        import json
        control_ids = json.loads(control_ids)
    
    if not isinstance(control_ids, list) or len(control_ids) == 0:
        print(f"[Gap Analysis] Empty or invalid selected_control_ids for company {company_id}, framework {framework_id}")
        return []
    
    print(f"[Gap Analysis] Found {len(control_ids)} selected controls for framework {framework_id}")
    
    # FIX 7: Deduplicate control IDs to prevent processing same control multiple times
    unique_control_ids = list(set(control_ids))
    if len(unique_control_ids) != len(control_ids):
        print(f"[Gap Analysis] Deduplicated {len(control_ids)} -> {len(unique_control_ids)} unique control IDs")
    
    controls = (
        db.query(Control)
        .filter(Control.id.in_(unique_control_ids))
        .all()
    )
    
    print(f"[Gap Analysis] Retrieved {len(controls)} controls from database")
    return controls


def get_approved_policies(db: Session, company_id: int, framework_id: int) -> List[Policy]:
    """
    Get only approved policies for a company and framework.
    Policies are linked to company through User (owner_id -> User.company_id).
    
    Args:
        db: Database session
        company_id: ID of the company
        framework_id: ID of the framework
    
    Returns:
        List of approved Policy objects for the company and framework
    """
    from app.models import User
    
    policies = (
        db.query(Policy)
        .join(User, Policy.owner_id == User.id)
        .filter(
            User.company_id == company_id,
            Policy.framework_id == framework_id,
            Policy.status == PolicyStatus.APPROVED,
            Policy.is_active == True
        )
        .all()
    )
    
    print(f"[Gap Analysis] Found {len(policies)} approved policies for company {company_id}, framework {framework_id}")
    return policies


def get_approved_policies_for_control(db: Session, company_id: int, framework_id: int, control_id: int) -> List[Policy]:
    """
    FIX 1: Get approved policies scoped to a specific control.
    This ensures each control is evaluated independently.
    
    Args:
        db: Database session
        company_id: ID of the company
        framework_id: ID of the framework
        control_id: ID of the control
    
    Returns:
        List of approved Policy objects mapped to this specific control
    """
    from app.models import User
    
    policies = (
        db.query(Policy)
        .join(User, Policy.owner_id == User.id)
        .filter(
            User.company_id == company_id,
            Policy.framework_id == framework_id,
            Policy.control_id == control_id,  # Control-specific filter
            Policy.status == PolicyStatus.APPROVED,
            Policy.is_active == True
        )
        .all()
    )
    
    print(f"[Gap Analysis] Found {len(policies)} approved policies for control {control_id} (company {company_id}, framework {framework_id})")
    return policies


def decompose_control_requirements(control_name: str, control_description: str) -> List[str]:
    """
    Decompose control into atomic mandatory requirements.
    If requirements are not explicitly listed, derive them from description.
    
    Args:
        control_name: Name of the control
        control_description: Description of the control
    
    Returns:
        List of atomic mandatory requirements
    """
    requirements = []
    
    # Try to extract requirements using AI
    try:
        requirements = extract_control_requirements(control_name, control_description)
        if requirements:
            print(f"[Gap Analysis] Extracted {len(requirements)} requirements from control description")
            return requirements
    except Exception as e:
        print(f"[Gap Analysis] ⚠️ Error extracting requirements via AI: {str(e)}")
    
    # Fallback: Pattern-based extraction from description
    if control_description:
        # Look for numbered lists or bullet points
        lines = control_description.split('\n')
        for line in lines:
            line = line.strip()
            # Match numbered items (1., 2., etc.) or bullet points (-, •, *)
            if re.match(r'^[\d\.\-\•\*]\s+', line) or re.match(r'^[a-z]\)\s+', line):
                requirement = re.sub(r'^[\d\.\-\•\*a-z\)]\s+', '', line).strip()
                if requirement and len(requirement) > 10:  # Filter out very short items
                    requirements.append(requirement)
        
        # If no structured list found, try to split by common separators
        if not requirements:
            # Split by semicolons, periods followed by capital letters, or "and"/"or"
            parts = re.split(r'[;\.](?=\s+[A-Z])|(?:\s+and\s+|\s+or\s+)', control_description)
            for part in parts:
                part = part.strip()
                if part and len(part) > 15 and not part.lower().startswith('the'):
                    # Clean up common prefixes
                    part = re.sub(r'^(ensure|must|shall|should|requires?|includes?|covers?)\s+', '', part, flags=re.IGNORECASE)
                    if part and len(part) > 10:
                        requirements.append(part)
    
    # If still no requirements, use the control name and description as a single requirement
    if not requirements:
        requirements = [f"{control_name}: {control_description[:200]}" if control_description else control_name]
    
    print(f"[Gap Analysis] Using {len(requirements)} requirement(s) for analysis")
    return requirements


def run_gap_analysis_for_framework(
    framework_id: int,
    company_id: int,
    user_id: int,
    db: Session,
    limit_controls: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run gap analysis for all controls in a framework.
    
    Args:
        framework_id: ID of the framework to analyze
        company_id: ID of the company
        user_id: ID of the user running the analysis
        db: Database session
        limit_controls: Optional limit on number of controls to analyze (for testing)
    
    Returns:
        Dictionary with analysis results:
        - total_controls: int
        - gaps_identified: int
        - gaps_created: int
        - analysis_id: str
    """
    # Get framework
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if not framework:
        raise ValueError(f"Framework {framework_id} not found")
    
    # Get all controls for this framework
    controls = db.query(Control).join(
        ControlGroup, Control.control_group_id == ControlGroup.id
    ).filter(
        ControlGroup.framework_id == framework_id,
        Control.is_active == True
    ).order_by(ControlGroup.order_index, Control.order_index).all()
    
    if limit_controls:
        controls = controls[:limit_controls]
    
    total_controls = len(controls)
    gaps_identified = 0
    gaps_created = 0
    
    # Iterate through each control
    for control in controls:
        try:
            # Step 1: Prepare control text for analysis
            control_text = f"{control.name}\n\n{control.description or ''}"
            
            # Step 2: Search Pinecone for similar policies (primary search)
            similar_policies = query_similar_policies(
                query_text=control_text,
                top_k=10,  # Increased from 5 to 10
                filter_metadata={"company_id": company_id} if company_id else None
            )
            
            # Step 2b: Fallback search if no results
            if len(similar_policies) == 0:
                similar_policies = query_similar_policies(
                    query_text=control.name,  # Just control name
                    top_k=10,
                    filter_metadata={"company_id": company_id} if company_id else None
                )
            
            # Step 3: Classify with OpenAI
            gap_analysis = generate_gap_analysis(
                control_name=control.name,
                control_description=control.description or "",
                similar_policies=similar_policies,
                framework_name=framework.name
            )
            
            # Step 4: Store Gap + Remediation if gap identified
            if gap_analysis.get("gap_identified", False):
                gaps_identified += 1
                
                # Map severity string to enum
                severity_map = {
                    "low": GapSeverity.LOW,
                    "medium": GapSeverity.MEDIUM,
                    "high": GapSeverity.HIGH,
                    "critical": GapSeverity.CRITICAL
                }
                severity = severity_map.get(
                    gap_analysis.get("severity", "medium").lower(),
                    GapSeverity.MEDIUM
                )
                
                # Create Gap
                gap = Gap(
                    title=f"Gap in {control.code or control.name}",
                    description=gap_analysis.get("gap_description", "Gap identified"),
                    severity=severity,
                    status=GapStatus.IDENTIFIED,
                    framework_id=framework_id,
                    control_id=control.id,
                    identified_by_id=user_id,
                    risk_score=gap_analysis.get("risk_score", 50.0),
                    root_cause="AI-identified gap based on control analysis",
                    identified_date=datetime.utcnow(),
                    is_active=True
                )
                db.add(gap)
                db.flush()
                
                # Create Remediation with suggestions
                remediation_suggestions = gap_analysis.get("remediation_suggestions", [])
                if remediation_suggestions:
                    action_plan = "\n".join([
                        f"{idx + 1}. {suggestion}"
                        for idx, suggestion in enumerate(remediation_suggestions)
                    ])
                else:
                    action_plan = "Review and implement control requirements"
                
                remediation = Remediation(
                    title=f"Remediation for {control.code or control.name}",
                    description="AI-generated remediation plan",
                    action_plan=action_plan,
                    status=RemediationStatus.PLANNED,
                    gap_id=gap.id,
                    assigned_to_id=user_id,
                    is_active=True
                )
                db.add(remediation)
                gaps_created += 1
                
        except Exception as e:
            # Log error but continue with next control
            print(f"Error analyzing control {control.id}: {str(e)}")
            continue
    
    # Commit all gaps and remediations
    db.commit()
    
    analysis_id = f"gap_analysis_{framework_id}_{company_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    return {
        "total_controls": total_controls,
        "gaps_identified": gaps_identified,
        "gaps_created": gaps_created,
        "analysis_id": analysis_id,
        "framework_id": framework_id,
        "framework_name": framework.name
    }


def run_gap_analysis_for_control(
    control_id: int,
    company_id: int,
    user_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Run gap analysis for a single control.
    
    Args:
        control_id: ID of the control to analyze
        company_id: ID of the company
        user_id: ID of the user running the analysis
        db: Database session
    
    Returns:
        Dictionary with analysis results
    """
    # PART 1: VALIDATE CONTROL IDS BEFORE GAP ANALYSIS
    # First, get framework from control_group to validate control belongs to framework
    # We need to validate control exists and belongs to the correct framework
    control = db.query(Control).join(
        ControlGroup, Control.control_group_id == ControlGroup.id
    ).filter(
        Control.id == control_id
    ).first()
    
    if not control:
        print(f"[Gap Analysis] ⚠️ Control {control_id} not found in database")
        # Return error result instead of raising exception
        return {
            "control_id": control_id,
            "control_code": None,
            "control_name": None,
            "gap_identified": False,
            "status": "ERROR",
            "severity": None,
            "risk_score": 0,
            "reason": "Control not found in database",
            "gap_created": False,
            "gap_id": None,
            "similar_policies_found": 0,
            "max_similarity_score": 0.0,
            "similarity_scores": [],
            "matched_policy_titles": [],
            "missing_requirements": [],
            "control_requirements": [],
            "decision_reason": "Control not found in database"
        }
    
    # Get framework
    control_group = db.query(ControlGroup).filter(
        ControlGroup.id == control.control_group_id
    ).first()
    
    if not control_group:
        print(f"[Gap Analysis] ⚠️ Control group not found for control {control_id}")
        return {
            "control_id": control_id,
            "control_code": control.code,
            "control_name": control.name,
            "gap_identified": False,
            "status": "ERROR",
            "severity": None,
            "risk_score": 0,
            "reason": "Control group not found for this control",
            "gap_created": False,
            "gap_id": None,
            "similar_policies_found": 0,
            "max_similarity_score": 0.0,
            "similarity_scores": [],
            "matched_policy_titles": [],
            "missing_requirements": [],
            "control_requirements": [],
            "decision_reason": "Control group not found"
        }
    
    framework = db.query(Framework).filter(
        Framework.id == control_group.framework_id
    ).first()
    
    if not framework:
        print(f"[Gap Analysis] ⚠️ Framework not found for control {control_id}")
        return {
            "control_id": control_id,
            "control_code": control.code,
            "control_name": control.name,
            "gap_identified": False,
            "status": "ERROR",
            "severity": None,
            "risk_score": 0,
            "reason": "Framework not found for this control",
            "gap_created": False,
            "gap_id": None,
            "similar_policies_found": 0,
            "max_similarity_score": 0.0,
            "similarity_scores": [],
            "matched_policy_titles": [],
            "missing_requirements": [],
            "control_requirements": [],
            "decision_reason": "Framework not found"
        }
    
    # FIX 1: CONTROL-SCOPED POLICY CHECK
    # Check approved policies at control level (not framework level)
    # This ensures each control is evaluated independently
    approved_policies_for_control = get_approved_policies_for_control(db, company_id, framework.id, control_id)
    
    # FIX 2: REMOVE EARLY RETURNS - Use flags instead
    # Initialize hard rule flags - these will be checked later, but we continue execution
    hard_rule_failed = False
    hard_rule_reason = None
    
    if not approved_policies_for_control:
        print(f"[Gap Analysis] ⚠️ HARD RULE FLAG: No approved policies found for control {control_id}")
        hard_rule_failed = True
        hard_rule_reason = "No approved policies found for this control"
    else:
        print(f"[Gap Analysis] Found {len(approved_policies_for_control)} approved policies for control {control_id}")
    
    # Step 1: Prepare control text and decompose requirements
    control_text = f"{control.name}\n\n{control.description or ''}"
    print(f"\n[Gap Analysis] ===== Analyzing Control: {control.name} =====")
    print(f"[Gap Analysis] Control ID: {control_id}")
    print(f"[Gap Analysis] Framework: {framework.name} (ID: {framework.id})")
    print(f"[Gap Analysis] Control text length: {len(control_text)} characters")
    
    # STEP 1: CONTROL REQUIREMENT DECOMPOSITION (MANDATORY)
    control_requirements = decompose_control_requirements(control.name, control.description or "")
    print(f"[Gap Analysis] Control Requirements ({len(control_requirements)}):")
    for idx, req in enumerate(control_requirements, 1):
        print(f"  {idx}. {req}")
    
    # Step 1: Prepare control text and decompose requirements
    control_text = f"{control.name}\n\n{control.description or ''}"
    print(f"\n[Gap Analysis] ===== Analyzing Control: {control.name} =====")
    print(f"[Gap Analysis] Control ID: {control_id}")
    print(f"[Gap Analysis] Framework: {framework.name} (ID: {framework.id})")
    print(f"[Gap Analysis] Control text length: {len(control_text)} characters")
    
    # STEP 1: CONTROL REQUIREMENT DECOMPOSITION (MANDATORY)
    control_requirements = decompose_control_requirements(control.name, control.description or "")
    print(f"[Gap Analysis] Control Requirements ({len(control_requirements)}):")
    for idx, req in enumerate(control_requirements, 1):
        print(f"  {idx}. {req}")
    
    # Step 2: Search Pinecone for similar policies
    # CRITICAL: Filter by framework_id, control_id, and APPROVED status
    print(f"[Gap Analysis] Searching Pinecone for APPROVED policies (framework={framework.id}, control={control_id})...")
    
    filter_metadata = {
        "company_id": company_id,
        "framework_id": framework.id,
        "control_id": control_id,  # PART 3: Control-specific matching
        "status": "approved"  # ONLY APPROVED policies
    } if company_id else {
        "framework_id": framework.id,
        "control_id": control_id,
        "status": "approved"
    }
    
    # STEP 2: STRICT SIMILARITY THRESHOLDS
    # Use SIMILARITY_MIN constant for consistency
    similar_policies = query_similar_policies(
        query_text=control_text,
        top_k=8,
        filter_metadata=filter_metadata,
        similarity_threshold=SIMILARITY_MIN  # PART 5: Use constant
    )
    print(f"[Gap Analysis] Found {len(similar_policies)} similar policies (after {SIMILARITY_MIN} threshold filter)")
    
    # Log similarity scores and policy details
    if similar_policies:
        print(f"[Gap Analysis] Policy matches (similarity >= {SIMILARITY_MIN}):")
        for idx, policy in enumerate(similar_policies, 1):
            chunk_info = f"chunk {policy.get('chunk_index', 'N/A')}" if policy.get('chunk_index') is not None else "full"
            print(f"  {idx}. {policy.get('title', 'Unknown')} (score: {policy.get('score', 0):.3f}, {chunk_info})")
    else:
        print(f"[Gap Analysis] ⚠️ No APPROVED policies found matching control {control_id}")
    
    # Step 2b: Fallback search - try with just control name if no results
    if len(similar_policies) == 0:
        print(f"[Gap Analysis] Attempting fallback search with control name only...")
        fallback_policies = query_similar_policies(
            query_text=control.name,  # Just the control name
            top_k=8,
            filter_metadata=filter_metadata,
            similarity_threshold=SIMILARITY_MIN  # PART 5: Use constant
        )
        if fallback_policies:
            print(f"[Gap Analysis] Fallback search found {len(fallback_policies)} policies")
            for idx, policy in enumerate(fallback_policies, 1):
                chunk_info = f"chunk {policy.get('chunk_index', 'N/A')}" if policy.get('chunk_index') is not None else "full"
                print(f"  {idx}. {policy.get('title', 'Unknown')} (score: {policy.get('score', 0):.3f}, {chunk_info})")
            similar_policies = fallback_policies
    
    # Store similarity scores for audit (before AI analysis)
    similarity_scores = [p.get('score', 0) for p in similar_policies]
    max_similarity = max(similarity_scores) if similarity_scores else 0.0
    policy_ids = [p.get('policy_id') for p in similar_policies if p.get('policy_id')]
    matched_policy_titles = [p.get('title', 'Unknown') for p in similar_policies]
    
    print(f"[Gap Analysis] Similarity scores: {similarity_scores}")
    print(f"[Gap Analysis] Max similarity: {max_similarity:.3f}")
    
    # TASK 1: Query Knowledge Base for authoritative reference
    print(f"[Gap Analysis] Querying Knowledge Base for framework {framework.id}...")
    knowledge_base_chunks = query_knowledge_base_chunks(
        query_text=control_text,
        framework_id=framework.id,
        top_k=5,
        similarity_threshold=0.70
    )
    
    if not knowledge_base_chunks or len(knowledge_base_chunks) == 0:
        print(f"[Gap Analysis] ⚠️ No Knowledge Base chunks found for framework {framework.id}")
        # This will be handled in centralized decision logic
    else:
        print(f"[Gap Analysis] Found {len(knowledge_base_chunks)} KB chunks")
        for idx, kb_chunk in enumerate(knowledge_base_chunks, 1):
            print(f"  {idx}. {kb_chunk.get('title', 'Unknown')} (score: {kb_chunk.get('score', 0):.3f})")
    
    # FIX 2: REMOVE EARLY RETURNS - Continue execution even if no policies found
    # Update hard rule flags based on similarity results
    if not similar_policies or len(similar_policies) == 0:
        print(f"[Gap Analysis] ⚠️ HARD RULE FLAG: No similar policies found (similarity search completed)")
        if not hard_rule_failed:  # Only set if not already set by policy check
            hard_rule_failed = True
            hard_rule_reason = "No similar policies found for this control"
    elif max_similarity < SIMILARITY_MIN:
        print(f"[Gap Analysis] ⚠️ HARD RULE FLAG: Max similarity {max_similarity:.3f} < {SIMILARITY_MIN}")
        if not hard_rule_failed:  # Only set if not already set
            hard_rule_failed = True
            hard_rule_reason = f"Policy similarity below threshold ({max_similarity:.3f} < {SIMILARITY_MIN})"
    
    # FIX 2: AI ANALYSIS ALWAYS RUNS (even if hard rules failed)
    # This ensures AI evaluation influences the output
    print(f"[Gap Analysis] Calling OpenAI for gap analysis evaluation...")
    gap_analysis = generate_gap_analysis(
        control_name=control.name,
        control_description=control.description or "",
        similar_policies=similar_policies,
        framework_name=framework.name,
        control_requirements=control_requirements,
        knowledge_base_chunks=knowledge_base_chunks
    )
    print(f"[Gap Analysis] AI Evaluation Result:")
    print(f"  - Coverage Level: {gap_analysis.get('coverage_level', 'NONE')}")
    print(f"  - Missing Requirements: {gap_analysis.get('missing_requirements', [])}")
    print(f"  - Covered Requirements: {gap_analysis.get('covered_requirements', [])}")
    print(f"  - KB Alignment: {gap_analysis.get('kb_alignment', 'MISMATCH')}")
    print(f"  - Explanation: {gap_analysis.get('explanation', 'N/A')[:200]}...")
    
    # Extract evaluation data from AI
    covered_requirements = gap_analysis.get("covered_requirements", [])
    missing_requirements = gap_analysis.get("missing_requirements", [])
    coverage_level = gap_analysis.get("coverage_level", "NONE").upper()
    kb_alignment = gap_analysis.get("kb_alignment", "MISMATCH").upper()
    ai_explanation = gap_analysis.get("explanation", "")
    
    print(f"[Gap Analysis] Evaluation Data:")
    print(f"  - Coverage Level: {coverage_level}")
    print(f"  - KB Alignment: {kb_alignment}")
    print(f"  - Max Similarity: {max_similarity:.3f}")
    print(f"  - Approved Policies for Control: {len(approved_policies_for_control)}")
    
    # Update hard rule flag if no KB chunks found
    if not knowledge_base_chunks or len(knowledge_base_chunks) == 0:
        print(f"[Gap Analysis] ⚠️ HARD RULE FLAG: No KB chunks found")
        if not hard_rule_failed:  # Only set if not already set
            hard_rule_failed = True
            hard_rule_reason = "No authoritative knowledge base reference found"
    
    # FIX 6: CENTRALIZED DECISION LOGIC (KEEP EXISTING THRESHOLDS)
    # Default state = GAP
    status = "GAP"
    
    # A control is COMPLIANT only if ALL conditions are met:
    # - At least one APPROVED policy exists (control-scoped)
    # - max_policy_similarity >= 0.85
    # - coverage_level == "FULL"
    # - knowledge_base_alignment == "MATCH"
    
    has_approved_policy = len(approved_policies_for_control) > 0  # FIX 1: Use control-scoped policies
    similarity_meets_threshold = max_similarity >= 0.85
    coverage_is_full = coverage_level == "FULL"
    kb_alignment_matches = kb_alignment == "MATCH"
    
    print(f"[Gap Analysis] Decision Criteria:")
    print(f"  - Has Approved Policy (control-scoped): {has_approved_policy}")
    print(f"  - Similarity >= 0.85: {similarity_meets_threshold} ({max_similarity:.3f})")
    print(f"  - Coverage FULL: {coverage_is_full} ({coverage_level})")
    print(f"  - KB Alignment MATCH: {kb_alignment_matches} ({kb_alignment})")
    print(f"  - Hard Rule Failed: {hard_rule_failed} ({hard_rule_reason})")
    
    if (
        has_approved_policy
        and similarity_meets_threshold
        and coverage_is_full
        and kb_alignment_matches
        and not hard_rule_failed  # Hard rules override compliance
    ):
        status = "COMPLIANT"
        print(f"[Gap Analysis] ✓✓✓ ALL CONDITIONS MET → COMPLIANT")
    else:
        status = "GAP"
        print(f"[Gap Analysis] ⚠️ CONDITIONS NOT MET → GAP")
        if not has_approved_policy:
            print(f"  - Missing: Approved policy for this control")
        if not similarity_meets_threshold:
            print(f"  - Missing: Similarity >= 0.85 (current: {max_similarity:.3f})")
        if not coverage_is_full:
            print(f"  - Missing: Coverage FULL (current: {coverage_level})")
        if not kb_alignment_matches:
            print(f"  - Missing: KB Alignment MATCH (current: {kb_alignment})")
        if hard_rule_failed:
            print(f"  - Hard Rule Failed: {hard_rule_reason}")
    
    # If status is GAP, create gap record
    if status == "GAP":
        # FIX 3: DYNAMIC RISK SCORE CALCULATION
        # Calculate risk score based on similarity (not hardcoded)
        risk_score = calculate_risk_score(max_similarity)
        
        # FIX 4: SEVERITY BASED ON RISK SCORE
        severity, severity_str = calculate_severity_from_risk(risk_score)
        
        # FIX 5: AI RESULT SHOULD OVERRIDE GENERIC HARD-RULE TEXT
        # Use AI explanation if available, otherwise use hard rule reason
        if ai_explanation and ai_explanation.strip():
            gap_description = ai_explanation
            if missing_requirements:
                gap_description += f". Missing requirements: {', '.join(missing_requirements[:3])}"
        elif hard_rule_reason:
            gap_description = hard_rule_reason
            if missing_requirements:
                gap_description += f". Missing requirements: {', '.join(missing_requirements[:3])}"
        else:
            gap_description = "Gap identified based on evaluation"
            if missing_requirements:
                gap_description += f". Missing requirements: {', '.join(missing_requirements[:3])}"
        
        gap = Gap(
            title=f"Gap in {control.code or control.name}",
            description=gap_description,
            severity=severity,
            status=GapStatus.IDENTIFIED,
            framework_id=framework.id,
            control_id=control.id,
            identified_by_id=user_id,
            risk_score=float(risk_score),
            root_cause=f"Centralized Decision: similarity={max_similarity:.3f}, coverage={coverage_level}, kb_alignment={kb_alignment}, hard_rule={hard_rule_reason or 'None'}",
            identified_date=datetime.utcnow(),
            is_active=True
        )
        db.add(gap)
        db.flush()
        gap_id = gap.id
        
        # Create remediation
        remediation_suggestions = gap_analysis.get("remediation_suggestions", [
            "Review and update policies to address all control requirements",
            "Ensure policy explicitly covers all mandatory requirements",
            "Align policy with knowledge base requirements",
            "Document implementation steps",
            "Establish monitoring to verify compliance"
        ])
        
        remediation = Remediation(
            title=f"Remediation for {control.code or control.name}",
            description="Remediation plan to address identified gap",
            action_plan="\n".join([f"{idx + 1}. {suggestion}" for idx, suggestion in enumerate(remediation_suggestions)]),
            status=RemediationStatus.PLANNED,
            gap_id=gap.id,
            assigned_to_id=user_id,
            is_active=True
        )
        db.add(remediation)
        db.commit()
        
        # FIX 8: PRESERVE EXISTING OUTPUT FORMAT
        return {
            "control_id": control_id,
            "control_code": control.code,
            "control_name": control.name,
            "gap_identified": True,
            "status": status,
            "severity": severity_str,
            "risk_score": risk_score,  # FIX 3: Dynamic risk score
            "gap_created": True,
            "gap_id": gap_id,
            "similar_policies_found": len(similar_policies),
            "max_similarity_score": max_similarity,
            "similarity_scores": similarity_scores,
            "reason": gap_description,  # FIX 5: AI result or hard rule reason
            "matched_policy_titles": matched_policy_titles,
            "missing_requirements": missing_requirements,
            "control_requirements": control_requirements,
            "coverage_level": coverage_level,
            "kb_alignment": kb_alignment,
            "decision_reason": hard_rule_reason or f"Centralized Decision: similarity={max_similarity:.3f}, coverage={coverage_level}, kb_alignment={kb_alignment}"
        }
    else:
        # Status is COMPLIANT - no gap created
        print(f"[Gap Analysis] ✓✓✓ COMPLIANT - No gap created")
        db.commit()
        # FIX 8: PRESERVE EXISTING OUTPUT FORMAT
        return {
            "control_id": control_id,
            "control_code": control.code,
            "control_name": control.name,
            "gap_identified": False,
            "status": status,
            "severity": None,
            "risk_score": 0,
            "gap_created": False,
            "gap_id": None,
            "similar_policies_found": len(similar_policies),
            "max_similarity_score": max_similarity,
            "similarity_scores": similarity_scores,
            "matched_policy_titles": matched_policy_titles,
            "coverage_level": coverage_level,
            "kb_alignment": kb_alignment,
            "reason": "All compliance conditions met",
            "missing_requirements": [],
            "covered_requirements": covered_requirements,
            "control_requirements": control_requirements,
            "decision_reason": f"All conditions met: similarity={max_similarity:.3f}, coverage={coverage_level}, kb_alignment={kb_alignment}"
        }
    
    # Legacy code below - should not be reached due to centralized decision above
    # PART 6: HARD RULE - PARTIAL or NONE coverage ALWAYS results in GAP
    if coverage_level in ["PARTIAL", "NONE"]:
        print(f"[Gap Analysis] ⚠️ HARD RULE: Coverage level is {coverage_level} → GAP IDENTIFIED (no partial compliance allowed)")
        gap_identified = True
        
        # Calculate risk score based on coverage level
        if coverage_level == "NONE":
            risk_score = 85
            severity_str = "HIGH"
            severity = GapSeverity.HIGH
        else:  # PARTIAL
            risk_score = 65  # Medium-high risk for partial coverage
            severity_str = "HIGH"
            severity = GapSeverity.HIGH
        
        # Create gap immediately
        gap = Gap(
            title=f"Gap in {control.code or control.name}",
            description=f"Control requirements not fully covered ({coverage_level} coverage). Missing requirements: {', '.join(missing_requirements[:3]) if missing_requirements else 'N/A'}",
            severity=severity,
            status=GapStatus.IDENTIFIED,
            framework_id=framework.id,
            control_id=control.id,
            identified_by_id=user_id,
            risk_score=float(risk_score),
            root_cause=f"HARD RULE: Coverage level is {coverage_level} (not FULL). Control requirements: {', '.join(control_requirements[:5])}. Missing requirements: {', '.join(missing_requirements[:5]) if missing_requirements else 'All requirements'}. Similarity: {max_similarity:.3f}.",
            identified_date=datetime.utcnow(),
            is_active=True
        )
        db.add(gap)
        db.flush()
        gap_id = gap.id
        
        # Create remediation
        remediation_suggestions = [
            f"Update policy to fully address all control requirements (currently {coverage_level} coverage)",
            "Ensure policy explicitly covers all mandatory requirements",
            "Review and enhance policy content to achieve FULL coverage",
            "Document implementation steps for missing requirements",
            "Establish monitoring to verify full compliance"
        ]
        
        remediation = Remediation(
            title=f"Remediation for {control.code or control.name}",
            description=f"Remediation plan to achieve FULL coverage (currently {coverage_level})",
            action_plan="\n".join([f"{idx + 1}. {suggestion}" for idx, suggestion in enumerate(remediation_suggestions)]),
            status=RemediationStatus.PLANNED,
            gap_id=gap.id,
            assigned_to_id=user_id,
            is_active=True
        )
        db.add(remediation)
        db.commit()
        
        return {
            "control_id": control_id,
            "control_code": control.code,
            "control_name": control.name,
            "gap_identified": True,
            "status": "GAP",
            "severity": severity_str,
            "risk_score": risk_score,
            "gap_created": True,
            "gap_id": gap_id,
            "similar_policies_found": len(similar_policies),
            "max_similarity_score": max_similarity,
            "similarity_scores": similarity_scores,
            "reason": f"Control requirements not fully covered ({coverage_level} coverage)",
            "matched_policy_titles": matched_policy_titles,
            "missing_requirements": missing_requirements if missing_requirements else control_requirements,
            "control_requirements": control_requirements,
            "decision_reason": f"HARD RULE: Coverage level is {coverage_level} (not FULL)",
            "gap_description": f"Control requirements not fully covered ({coverage_level} coverage)",
            "remediation_suggestions": remediation_suggestions,
            "coverage_level": coverage_level
        }
    
    # Check if all control requirements are covered (only if coverage_level == "FULL")
    all_requirements_covered = False
    if control_requirements:
        # Normalize for comparison
        covered_normalized = [r.lower().strip() for r in covered_requirements]
        required_normalized = [r.lower().strip() for r in control_requirements]
        
        # Check if all requirements have corresponding coverage
        all_covered = all(
            any(
                req in covered or covered in req or 
                any(keyword in covered for keyword in req.split()[:3] if len(keyword) > 4)
                for covered in covered_normalized
            )
            for req in required_normalized
        )
        all_requirements_covered = all_covered
        print(f"[Gap Analysis] Requirements coverage: {len(covered_requirements)}/{len(control_requirements)} covered")
    
    # PART 5: GAP DECISION (FINAL TRUTH TABLE)
    # Evaluate all conditions for explicit gap decision
    
    # Check all conditions
    no_approved_policy = len(approved_policies) == 0
    no_similar_policy = len(similar_policies) == 0
    similarity_below_threshold = max_similarity < SIMILARITY_MIN
    coverage_not_full = coverage_level != "FULL"
    requirements_not_covered = not all_requirements_covered if control_requirements else True
    
    # PART 5: GAP DECISION (FINAL TRUTH TABLE)
    # gap_identified = (
    #     no_approved_policy
    #     or no_similar_policy
    #     or max_similarity < 0.72
    #     or coverage_level != "FULL"
    #     or not all_requirements_covered
    # )
    gap_identified = (
        no_approved_policy
        or no_similar_policy
        or similarity_below_threshold
        or coverage_not_full
        or requirements_not_covered
    )
    
    # PART 6: Only compliant if max_similarity >= AUTO_COMPLIANT AND coverage_level == "FULL"
    # Since we already checked for PARTIAL/NONE above, at this point coverage_level must be "FULL"
    auto_compliant = (max_similarity >= AUTO_COMPLIANT and coverage_level == "FULL")
    
    # If auto-compliant, override gap_identified
    if auto_compliant:
        gap_identified = False
        decision_reason = f"Auto-compliant: similarity {max_similarity:.3f} >= {AUTO_COMPLIANT} and coverage_level == FULL"
        reason = "Control requirements fully covered"
        risk_score = round(max_similarity * 100)
        severity_str = "low"
        print(f"[Gap Analysis] ✓ Auto-compliant: similarity {max_similarity:.3f} >= {AUTO_COMPLIANT} AND coverage == FULL")
    else:
        # Even if coverage is FULL, if similarity < AUTO_COMPLIANT, it's still a gap
        if coverage_level == "FULL" and max_similarity < AUTO_COMPLIANT:
            print(f"[Gap Analysis] ⚠️ Coverage is FULL but similarity {max_similarity:.3f} < {AUTO_COMPLIANT} → GAP")
            gap_identified = True
        
        # Determine reason and risk score based on which condition(s) triggered
        reasons_list = []
        if no_approved_policy:
            reasons_list.append("No approved policies")
        if no_similar_policy:
            reasons_list.append("No similar policies found")
        if similarity_below_threshold:
            reasons_list.append(f"Similarity {max_similarity:.3f} < {SIMILARITY_MIN}")
        if coverage_not_full:
            reasons_list.append(f"Coverage level: {coverage_level} (not FULL)")
        if requirements_not_covered:
            reasons_list.append("Not all requirements covered")
        
        decision_reason = "Gap identified: " + ", ".join(reasons_list) if reasons_list else "Gap identified"
        
        # Set reason and risk score
        if missing_requirements:
            reason = f"Missing requirements: {', '.join(missing_requirements[:3])}"
        elif coverage_not_full:
            reason = gap_analysis.get("gap_description", f"Control requirements not fully covered ({coverage_level} coverage)")
        elif requirements_not_covered:
            reason = "Not all control requirements explicitly covered"
        else:
            reason = gap_analysis.get("gap_description", "Control requirements not fully covered")
        
        # Calculate risk score based on conditions
        if no_approved_policy or no_similar_policy:
            risk_score = 85.0
        elif similarity_below_threshold:
            risk_score = round((1 - max_similarity) * 100) if max_similarity > 0 else 85.0
        else:
            risk_score = float(gap_analysis.get("risk_score", 60))
    
    # PART 7: Severity mapping based on risk score
    if risk_score >= 80:
        severity_str = "critical"
    elif risk_score >= 60:
        severity_str = "high"
    elif risk_score >= 40:
        severity_str = "medium"
    else:
        severity_str = "low"
    
    # Log truth table evaluation
    print(f"[Gap Analysis] Truth Table Evaluation:")
    print(f"  - no_approved_policy: {no_approved_policy}")
    print(f"  - no_similar_policy: {no_similar_policy}")
    print(f"  - similarity_below_threshold (< {SIMILARITY_MIN}): {similarity_below_threshold} (max_similarity: {max_similarity:.3f})")
    print(f"  - coverage_not_full: {coverage_not_full} (coverage_level: {coverage_level})")
    print(f"  - requirements_not_covered: {requirements_not_covered} (all_covered: {all_requirements_covered})")
    print(f"  - Auto-compliant: {auto_compliant} (requires: similarity >= {AUTO_COMPLIANT} AND coverage == FULL)")
    print(f"[Gap Analysis] Final Decision:")
    print(f"  - Gap Identified: {gap_identified}")
    print(f"  - Decision Reason: {decision_reason}")
    print(f"  - Reason: {reason}")
    print(f"  - Risk Score: {risk_score}")
    print(f"  - Severity: {severity_str}")
    print(f"  - Coverage Level: {coverage_level}")
    
    gap_created = False
    gap_id = None
    
    # PART 7: GAP CREATION ENFORCEMENT
    # Whenever gap_identified == True, ALWAYS create a Gap record
    if gap_identified:
        # Map severity string to enum
        severity_map = {
            "low": GapSeverity.LOW,
            "medium": GapSeverity.MEDIUM,
            "high": GapSeverity.HIGH,
            "critical": GapSeverity.CRITICAL
        }
        severity = severity_map.get(severity_str.lower(), GapSeverity.MEDIUM)
        
        # Create Gap with comprehensive audit information
        gap_description = gap_analysis.get("gap_description", reason) if gap_analysis else reason
        # Use AI-provided missing requirements, fallback to our list if not provided
        missing_requirements_final = gap_analysis.get("missing_requirements", []) if gap_analysis else []
        if not missing_requirements_final and missing_requirements:
            missing_requirements_final = missing_requirements
        if not missing_requirements_final and control_requirements:
            # If no missing requirements identified, assume all are missing
            missing_requirements_final = control_requirements
        
        # Add missing requirements to description
        if missing_requirements_final:
            missing_text = "\n\nMissing Requirements:\n" + "\n".join([f"- {req}" for req in missing_requirements_final])
            gap_description = gap_description + missing_text
        
        # PART 8: AUDIT TRANSPARENCY - Store comprehensive audit trail
        similarity_info = f"Max similarity score: {max_similarity:.3f}" if similar_policies else "No policies found"
        policy_ids_str = ", ".join([str(pid) for pid in policy_ids]) if policy_ids else "None"
        matched_titles_str = ", ".join(matched_policy_titles[:5]) if matched_policy_titles else "None"
        
        root_cause = (
            f"Decision: {decision_reason}. "
            f"Reason: {reason}. "
            f"{similarity_info}. "
            f"Policies found: {len(similar_policies)}. "
            f"Similarity scores: {similarity_scores}. "
            f"Policy IDs: [{policy_ids_str}]. "
            f"Matched policies: {matched_titles_str}. "
            f"Coverage level: {coverage_level}. "
            f"Control requirements: {', '.join(control_requirements[:5])}. "
            f"Missing requirements: {', '.join(missing_requirements_final[:5]) if missing_requirements_final else 'All requirements'}. "
            f"Covered requirements: {', '.join(covered_requirements[:5]) if covered_requirements else 'None'}."
        )
        
        gap = Gap(
            title=f"Gap in {control.code or control.name}",
            description=gap_description,
            severity=severity,
            status=GapStatus.IDENTIFIED,
            framework_id=framework.id,
            control_id=control.id,
            identified_by_id=user_id,
            risk_score=risk_score,
            root_cause=root_cause,
            identified_date=datetime.utcnow(),
            is_active=True
        )
        db.add(gap)
        db.flush()
        gap_id = gap.id
        
        print(f"[Gap Analysis] ✓ Gap created: ID {gap_id}, Severity: {severity.value}, Risk: {gap.risk_score}")
        
        # Create Remediation
        remediation_suggestions = gap_analysis.get("remediation_suggestions", []) if gap_analysis else []
        if not remediation_suggestions:
            remediation_suggestions = [
                f"Create or update policy document addressing: {control.name}",
                "Define clear procedures and processes to meet the control requirement",
                "Document implementation steps and assign responsibilities",
                "Establish monitoring and review mechanisms"
            ]
        
        action_plan = "\n".join([
            f"{idx + 1}. {suggestion}"
            for idx, suggestion in enumerate(remediation_suggestions)
        ])
        
        remediation = Remediation(
            title=f"Remediation for {control.code or control.name}",
            description="Remediation plan to address identified gap",
            action_plan=action_plan,
            status=RemediationStatus.PLANNED,
            gap_id=gap.id,
            assigned_to_id=user_id,
            is_active=True
        )
        db.add(remediation)
        gap_created = True
        gap_id = gap.id
        
        db.commit()
        print(f"[Gap Analysis] ✓ Gap created: ID {gap_id}, Severity: {severity.value}, Risk: {risk_score}")
    
    # PART 6: Return detailed response with audit information
    return {
        "control_id": control_id,
        "control_code": control.code,
        "control_name": control.name,
        "gap_identified": gap_identified,
        "status": "GAP" if gap_identified else "COMPLIANT",
        "severity": severity_str,
        "risk_score": int(risk_score),
        "reason": reason,
        "decision_reason": decision_reason,
        "gap_created": gap_created,
        "gap_id": gap_id,
        "similar_policies_found": len(similar_policies),
        "max_similarity_score": max_similarity,
        "similarity_scores": similarity_scores,
        "matched_policy_titles": matched_policy_titles,
        "policy_ids": policy_ids,
        "missing_requirements": missing_requirements_final if gap_identified else [],
        "covered_requirements": covered_requirements if not gap_identified else [],
        "control_requirements": control_requirements,
        "coverage_level": coverage_level
    }


def index_all_policies(db: Session, company_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Index all policies in Pinecone.
    Useful for initial setup or re-indexing.
    
    Args:
        db: Database session
        company_id: Optional company ID to filter policies
    
    Returns:
        Dictionary with indexing results
    """
    query = db.query(Policy).filter(Policy.is_active == True)
    
    if company_id:
        # Filter by company through owner
        from app.models import User
        query = query.join(User, Policy.owner_id == User.id).filter(
            User.company_id == company_id
        )
    
    policies = query.all()
    
    indexed = 0
    errors = 0
    
    for policy in policies:
        try:
            # Get full policy content
            policy_content = policy.content or policy.description or ""
            
            # Index policy embedding
            metadata = {
                "company_id": company_id,
                "framework_id": policy.framework_id,
                "control_id": policy.control_id,
                "policy_number": policy.policy_number,
                "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status)
            }
            
            index_policy_embedding(
                policy_id=policy.id,
                policy_title=policy.title,
                policy_content=policy_content,
                metadata=metadata
            )
            indexed += 1
            
        except Exception as e:
            print(f"Error indexing policy {policy.id}: {str(e)}")
            errors += 1
            continue
    
    return {
        "total_policies": len(policies),
        "indexed": indexed,
        "errors": errors
    }
