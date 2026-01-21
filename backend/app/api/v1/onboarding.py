from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from app.db import get_db
from app.models import (
    User, Company, Department, Role, Framework,
    ControlGroup, Control, Policy, PolicyStatus, ControlSelection, Gap
)
from app.api.v1.auth import get_current_user
from app.schemas.onboarding import (
    CompanyUpdate,
    DepartmentCreate, DepartmentResponse,
    RoleCreate, RoleResponse,
    FrameworkCreate, FrameworkResponse,
    ISO27001ControlsConfig,
    PolicyUpload, PolicyUploadResponse,
    GapAnalysisRequest, GapAnalysisResponse, GapInfo,
    ControlSelectionRequest, ControlSelectionResponse,
    OnboardingStatus
)
from app.services.gap_analysis_service import run_gap_analysis_for_control
from app.services.pinecone_service import index_policy_embedding

router = APIRouter()


@router.post("/company", status_code=status.HTTP_200_OK)
async def update_company(
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update company details during onboarding.
    """
    print(f"[Onboarding API] Received company update request from user {current_user.id}")
    print(f"[Onboarding API] Company data: {company_data}")
    
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    if not company:
        print(f"[Onboarding API] ERROR: Company not found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    print(f"[Onboarding API] Found company: {company.id} - {company.name}")
    
    # Update company fields
    if company_data.name is not None:
        company.name = company_data.name
        print(f"[Onboarding API] Updated company name to: {company_data.name}")
    if company_data.domain is not None:
        company.domain = company_data.domain
    if company_data.industry is not None:
        company.industry = company_data.industry
        print(f"[Onboarding API] Updated company industry to: {company_data.industry}")
    if company_data.size is not None:
        company.size = company_data.size
    
    try:
        db.commit()
        db.refresh(company)
        print(f"[Onboarding API] Company updated successfully: {company.id}")
    except Exception as e:
        print(f"[Onboarding API] ERROR committing company update: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update company: {str(e)}"
        )
    
    return {
        "message": "Company updated successfully",
        "company": {
            "id": company.id,
            "name": company.name,
            "domain": company.domain,
            "industry": company.industry,
            "size": company.size
        }
    }


@router.post("/departments", response_model=List[DepartmentResponse], status_code=status.HTTP_201_CREATED)
async def create_departments(
    departments: List[DepartmentCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple departments for the company during onboarding.
    """
    company_id = current_user.company_id
    
    created_departments = []
    for dept_data in departments:
        # Check if department already exists
        existing = db.query(Department).filter(
            Department.name == dept_data.name,
            Department.company_id == company_id
        ).first()
        
        if existing:
            continue  # Skip if already exists
        
        department = Department(
            name=dept_data.name,
            description=dept_data.description,
            company_id=company_id,
            is_active=True
        )
        db.add(department)
        created_departments.append(department)
    
    db.commit()
    
    for dept in created_departments:
        db.refresh(dept)
    
    return created_departments


@router.post("/roles", response_model=List[RoleResponse], status_code=status.HTTP_201_CREATED)
async def create_roles(
    roles: List[RoleCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple roles during onboarding.
    """
    created_roles = []
    for role_data in roles:
        # Check if role already exists
        existing = db.query(Role).filter(Role.name == role_data.name).first()
        
        if existing:
            continue  # Skip if already exists
        
        role = Role(
            name=role_data.name,
            description=role_data.description,
            permissions=role_data.permissions,
            is_active=True
        )
        db.add(role)
        created_roles.append(role)
    
    db.commit()
    
    for role in created_roles:
        db.refresh(role)
    
    return created_roles


@router.post("/frameworks", response_model=List[FrameworkResponse], status_code=status.HTTP_201_CREATED)
async def create_frameworks(
    frameworks: List[FrameworkCreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add frameworks during onboarding.
    """
    created_frameworks = []
    for framework_data in frameworks:
        # Check if framework already exists
        existing = db.query(Framework).filter(Framework.name == framework_data.name).first()
        
        if existing:
            continue  # Skip if already exists
        
        framework = Framework(
            name=framework_data.name,
            description=framework_data.description,
            version=framework_data.version,
            category=framework_data.category,
            is_active=True
        )
        db.add(framework)
        created_frameworks.append(framework)
    
    db.commit()
    
    for framework in created_frameworks:
        db.refresh(framework)
    
    return created_frameworks


@router.post("/iso27001/controls/config", status_code=status.HTTP_201_CREATED)
async def configure_iso27001_controls(
    config: ISO27001ControlsConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Configure ISO 27001 controls during onboarding.
    Creates control groups and controls for ISO 27001 framework.
    """
    # Find or create ISO 27001 framework
    iso27001_framework = db.query(Framework).filter(
        Framework.name.ilike("%ISO 27001%")
    ).first()
    
    if not iso27001_framework:
        iso27001_framework = Framework(
            name="ISO 27001:2022",
            description="Information Security Management System",
            version="2022",
            category="Security",
            is_active=True
        )
        db.add(iso27001_framework)
        db.flush()
    
    created_groups = []
    created_controls = []
    
    for group_data in config.control_groups:
        # Create control group
        control_group = ControlGroup(
            name=group_data.name,
            description=group_data.description,
            code=group_data.code,
            framework_id=iso27001_framework.id,
            order_index=group_data.order_index,
            is_active=True
        )
        db.add(control_group)
        db.flush()
        created_groups.append(control_group)
        
        # Create controls for this group
        if group_data.controls:
            for control_data in group_data.controls:
                control = Control(
                    name=control_data.name,
                    description=control_data.description,
                    code=control_data.code,
                    control_group_id=control_group.id,
                    order_index=control_data.order_index,
                    is_active=True
                )
                db.add(control)
                created_controls.append(control)
    
    db.commit()
    
    return {
        "message": "ISO 27001 controls configured successfully",
        "framework_id": iso27001_framework.id,
        "control_groups_created": len(created_groups),
        "controls_created": len(created_controls)
    }


@router.post("/policies/upload", response_model=List[PolicyUploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_policies(
    policies: List[PolicyUpload],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload policies during onboarding and index them in Pinecone.
    """
    created_policies = []
    
    for policy_data in policies:
        # Check if policy number already exists
        if policy_data.policy_number:
            existing = db.query(Policy).filter(
                Policy.policy_number == policy_data.policy_number
            ).first()
            if existing:
                continue  # Skip if already exists
        
        policy = Policy(
            title=policy_data.title,
            description=policy_data.description,
            content=policy_data.content,
            policy_number=policy_data.policy_number,
            version=policy_data.version,
            framework_id=policy_data.framework_id,
            control_id=policy_data.control_id,
            owner_id=current_user.id,
            status=PolicyStatus.UNDER_REVIEW,  # Set to UNDER_REVIEW for approval workflow
            is_active=True
        )
        db.add(policy)
        created_policies.append(policy)
    
    db.commit()
    
    # Index policies in Pinecone after they're created
    print(f"\n[Onboarding] ===== Indexing {len(created_policies)} Policies in Pinecone =====")
    
    for policy in created_policies:
        db.refresh(policy)
        
        # Index policy in Pinecone
        print(f"[Onboarding] Processing policy {policy.id}: {policy.title}")
        try:
            metadata = {
                "company_id": current_user.company_id,
                "framework_id": policy.framework_id,
                "control_id": policy.control_id,
                "policy_number": policy.policy_number,
                "status": policy.status.value
            }
            
            policy_content = policy.content or policy.description or ""
            
            if not policy_content.strip():
                print(f"[Onboarding] ✗ WARNING: Policy {policy.id} has no content. Skipping.")
            else:
                success = index_policy_embedding(
                    policy_id=policy.id,
                    policy_title=policy.title,
                    policy_content=policy_content,
                    metadata=metadata
                )
                
                if success:
                    print(f"[Onboarding] ✓ Policy {policy.id} indexed successfully")
                else:
                    print(f"[Onboarding] ✗ Policy {policy.id} indexing failed")
        except Exception as e:
            import traceback
            print(f"[Onboarding] ✗ ERROR indexing policy {policy.id}: {str(e)}")
            print(f"[Onboarding] Traceback:\n{traceback.format_exc()}")
    
    print(f"[Onboarding] ===== Policy Indexing Complete =====\n")
    
    return created_policies


@router.post("/controls/selection", response_model=ControlSelectionResponse, status_code=status.HTTP_201_CREATED)
async def save_control_selection(
    selection: ControlSelectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save selected controls for a framework during onboarding.
    Stores the selection in user's company context.
    """
    print(f"[Onboarding] ===== SAVE CONTROL SELECTION REQUEST =====")
    print(f"[Onboarding] Request data: framework_id={selection.framework_id}, framework={selection.framework}, controls={selection.controls}")
    
    # Get framework - prefer framework_id if provided, otherwise search by name
    if selection.framework_id:
        framework = db.query(Framework).filter(
            Framework.id == selection.framework_id,
            Framework.is_active == True
        ).first()
        if not framework:
            print(f"[Onboarding] ❌ Framework with ID {selection.framework_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework with ID {selection.framework_id} not found"
            )
        print(f"[Onboarding] ✅ Found framework by ID: {framework.name} (ID: {framework.id})")
    else:
        # Verify framework exists - handle variations like "ISO27001", "ISO 27001", "ISO 27001:2022"
        framework_name = selection.framework.upper().replace(" ", "").replace(":", "").replace("-", "")
        
        # Try exact match first
        framework = db.query(Framework).filter(
            Framework.name.ilike(f"%{selection.framework}%")
        ).first()
        
        # If not found, try matching without spaces/special chars
        if not framework:
            all_frameworks = db.query(Framework).filter(Framework.is_active == True).all()
            for fw in all_frameworks:
                fw_name_normalized = fw.name.upper().replace(" ", "").replace(":", "").replace("-", "")
                if framework_name in fw_name_normalized or fw_name_normalized in framework_name:
                    framework = fw
                    break
        
        if not framework:
            print(f"[Onboarding] ❌ Framework {selection.framework} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework {selection.framework} not found. Please ensure the framework is seeded first."
            )
        print(f"[Onboarding] ✅ Found framework by name: {framework.name} (ID: {framework.id})")
    
    # PART 2: FIX CONTROL SELECTION STORAGE - Validate all control IDs before saving
    # Normalize control IDs to integers (handle string IDs from frontend)
    try:
        control_ids = [int(cid) for cid in selection.controls if cid is not None and str(cid).strip() != '']
    except (ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid control IDs format: {selection.controls}. Error: {str(e)}"
        )
    
    if not control_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid control IDs provided"
        )
    
    # PART 1 — FIX OVER-STRICT CONTROL VALIDATION
    # Simplified validation: Only check if controls exist (no strict framework validation)
    
    print(f"[Onboarding] ===== VALIDATION START =====")
    print(f"[Onboarding] Target framework: ID={framework.id}, Name={framework.name}")
    print(f"[Onboarding] Validating {len(control_ids)} control IDs: {control_ids[:20]}...")
    
    # 1️⃣ First, check if controls exist (without is_active filter to see what's happening)
    all_controls = db.query(Control).filter(
        Control.id.in_(control_ids)
    ).all()
    
    print(f"[Onboarding] Found {len(all_controls)} controls in database (without is_active filter)")
    
    # Check which ones are active
    active_controls = [c for c in all_controls if c.is_active]
    inactive_controls = [c for c in all_controls if not c.is_active]
    
    if inactive_controls:
        print(f"[Onboarding] ⚠️  Found {len(inactive_controls)} inactive controls: {[c.id for c in inactive_controls]}")
    
    # 2️⃣ Use active controls for validation
    valid_controls = active_controls
    validated_control_ids = [c.id for c in valid_controls] if valid_controls else []
    
    # 3️⃣ If no active controls found, check if controls exist at all (for debugging)
    if not validated_control_ids and all_controls:
        print(f"[Onboarding] ⚠️  Controls exist but are inactive. IDs: {[c.id for c in all_controls]}")
        print(f"[Onboarding] ⚠️  Consider: Controls might need to be activated or framework needs to be re-seeded")
    
    # 4️⃣ Check if any requested IDs don't exist at all
    found_ids = {c.id for c in all_controls}
    not_found_ids = set(control_ids) - found_ids
    if not_found_ids:
        print(f"[Onboarding] ❌ Control IDs not found in database at all: {list(not_found_ids)}")
    
    # Check if any requested IDs were not found or inactive
    found_control_ids = {c.id for c in valid_controls}
    missing_control_ids = set(control_ids) - found_control_ids
    
    print(f"[Onboarding] ===== VALIDATION SUMMARY =====")
    print(f"[Onboarding] Requested control IDs: {len(control_ids)}")
    print(f"[Onboarding] Valid controls found: {len(validated_control_ids)}")
    print(f"[Onboarding] Invalid/missing controls: {len(missing_control_ids)}")
    
    if missing_control_ids:
        print(f"[Onboarding] ⚠️  Invalid control IDs (will be filtered out): {list(missing_control_ids)}")
    
    if validated_control_ids:
        print(f"[Onboarding] ✅ Valid control IDs to save: {validated_control_ids[:10]}...")
    else:
        print(f"[Onboarding] ❌ No valid controls found for any of the requested IDs: {control_ids}")
    
    # PART 2 — TRUST VALID CONTROL IDS
    # If no valid controls, provide detailed error message
    if not validated_control_ids:
        print(f"[Onboarding] ❌ No valid controls found for IDs: {control_ids}")
        
        # Provide helpful error message
        if not_found_ids:
            error_detail = f"Control IDs {list(not_found_ids)} not found in database. Please refresh the page and reselect controls."
        elif inactive_controls:
            error_detail = f"Selected controls exist but are inactive. Please contact administrator or refresh the page."
        else:
            error_detail = "No valid controls selected. Please select at least one valid control and try again."
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )
    
    # PART 2 — SAVE CONTROL SELECTION SAFELY
    # ALWAYS save validated_control_ids (NOT raw frontend input)
    
    print(f"[Onboarding] ✅ Validation passed. Saving {len(validated_control_ids)} validated control IDs: {validated_control_ids[:10]}... (showing first 10)")
    
    # PART 4 — LOG FOR DEBUGGING (TEMP)
    print(
        f"[CONTROL SELECTION] Framework={framework.id}, Controls={validated_control_ids}"
    )
    
    # Get user's company
    company = current_user.company
    company_id = company.id
    
    # Check if selection already exists for this company and framework
    existing_selection = db.query(ControlSelection).filter(
        ControlSelection.company_id == company_id,
        ControlSelection.framework_id == framework.id
    ).first()
    
    if existing_selection:
        # Update existing selection - ALWAYS use validated_control_ids
        print(f"[Onboarding] Updating existing control selection (ID: {existing_selection.id})")
        existing_selection.selected_control_ids = validated_control_ids
    else:
        # Create new selection - ALWAYS use validated_control_ids
        print(f"[Onboarding] Creating new control selection for company {company_id}, framework {framework.id}")
        new_selection = ControlSelection(
            company_id=company_id,
            framework_id=framework.id,
            selected_control_ids=validated_control_ids
        )
        db.add(new_selection)
    
    try:
        db.commit()
        print(f"[Onboarding] ✅ Successfully saved {len(validated_control_ids)} validated controls to database")
    except Exception as e:
        db.rollback()
        print(f"[Onboarding] ❌ Error committing to database: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save control selection: {str(e)}"
        )
    
    # Build response message - include warning if some controls were filtered
    if missing_control_ids:
        message = f"Successfully saved {len(validated_control_ids)} control(s). {len(missing_control_ids)} invalid control(s) were filtered out."
    else:
        message = f"Successfully saved {len(validated_control_ids)} control(s)."
    
    # Build response with specified format
    response = ControlSelectionResponse(
        message=message,
        framework_id=framework.id,
        controls_count=len(validated_control_ids)
    )
    print(f"[Onboarding] Returning response: {response}")
    return response


@router.post("/gap-analysis/run", response_model=GapAnalysisResponse)
async def run_gap_analysis(
    request: GapAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run gap analysis during onboarding.
    Uses only selected controls from the control selection step.
    """
    # Get user's company
    company = current_user.company
    
    # Fetch selected controls for the company
    selected_control_ids = []
    if request.framework_id:
        # Get selection for specific framework
        selection = db.query(ControlSelection).filter(
            ControlSelection.company_id == company.id,
            ControlSelection.framework_id == request.framework_id
        ).first()
        if selection:
            selected_control_ids = selection.selected_control_ids
    else:
        # Get all selections for the company
        selections = db.query(ControlSelection).filter(
            ControlSelection.company_id == company.id
        ).all()
        for selection in selections:
            selected_control_ids.extend(selection.selected_control_ids)
    
    # If no controls selected, use all controls (backward compatibility)
    if not selected_control_ids:
        # Fallback: use all controls for the framework if no selection exists
        if request.framework_id:
            controls = db.query(Control).join(
                ControlGroup, Control.control_group_id == ControlGroup.id
            ).filter(
                ControlGroup.framework_id == request.framework_id,
                Control.is_active == True
            ).all()
            selected_control_ids = [c.id for c in controls]
    
    # Run AI-powered gap analysis for selected controls
    if request.run_ai_analysis:
        if not selected_control_ids:
            return GapAnalysisResponse(
                status="error",
                message="No controls selected. Please select controls in the previous step.",
                gaps_identified=0,
                analysis_id=None,
                gaps=[]
            )
        
        # Run gap analysis for each selected control
        gaps_created = []
        gaps_identified_count = 0
        
        for control_id in selected_control_ids:
            try:
                result = run_gap_analysis_for_control(
                    control_id=control_id,
                    company_id=company.id,
                    user_id=current_user.id,
                    db=db
                )
                
                if result.get("gap_created", False):
                    gaps_identified_count += 1
                    # Fetch the created gap to include in response
                    gap = db.query(Gap).filter(Gap.id == result.get("gap_id")).first()
                    if gap:
                        gaps_created.append(gap)
            except Exception as e:
                # Log error but continue with other controls
                print(f"Error analyzing control {control_id}: {str(e)}")
                continue
        
        # Convert gaps to GapInfo schema
        gaps_info = []
        for gap in gaps_created:
            gaps_info.append(GapInfo(
                id=gap.id,
                title=gap.title,
                description=gap.description,
                severity=gap.severity.value,
                status=gap.status.value,
                control_id=gap.control_id,
                risk_score=gap.risk_score,
                root_cause=gap.root_cause,
                identified_date=gap.identified_date
            ))
        
        analysis_id = f"analysis_{company.id}_{current_user.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        return GapAnalysisResponse(
            status="completed",
            message=f"Gap analysis completed. Identified {gaps_identified_count} gap(s) across {len(selected_control_ids)} control(s).",
            gaps_identified=gaps_identified_count,
            analysis_id=analysis_id,
            gaps=gaps_info
        )
    else:
        return GapAnalysisResponse(
            status="skipped",
            message="Gap analysis skipped",
            gaps_identified=0,
            analysis_id=None,
            gaps=[]
        )


@router.get("/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current onboarding status for the company.
    """
    company_id = current_user.company_id
    
    # Check each onboarding step
    company = db.query(Company).filter(Company.id == company_id).first()
    company_configured = company and (
        company.domain is not None or
        company.industry is not None or
        company.size is not None
    )
    
    departments_count = db.query(func.count(Department.id)).filter(
        Department.company_id == company_id
    ).scalar()
    departments_configured = departments_count > 0
    
    roles_count = db.query(func.count(Role.id)).scalar()
    roles_configured = roles_count > 1  # More than just Admin role
    
    frameworks_count = db.query(func.count(Framework.id)).scalar()
    frameworks_configured = frameworks_count > 0
    
    controls_count = db.query(func.count(Control.id)).scalar()
    controls_configured = controls_count > 0
    
    policies_count = db.query(func.count(Policy.id)).filter(
        Policy.owner_id == current_user.id
    ).scalar()
    policies_uploaded = policies_count > 0
    
    # Gap analysis status (placeholder)
    gap_analysis_completed = False  # Would check actual gap analysis status
    
    # Calculate completion percentage
    steps = [
        company_configured,
        departments_configured,
        roles_configured,
        frameworks_configured,
        controls_configured,
        policies_uploaded,
        gap_analysis_completed
    ]
    completed_steps = sum(steps)
    completion_percentage = int((completed_steps / len(steps)) * 100)
    
    # Determine current step
    if not company_configured:
        current_step = "company"
    elif not departments_configured:
        current_step = "departments"
    elif not roles_configured:
        current_step = "roles"
    elif not frameworks_configured:
        current_step = "frameworks"
    elif not controls_configured:
        current_step = "controls"
    elif not policies_uploaded:
        current_step = "policies"
    elif not gap_analysis_completed:
        current_step = "gap_analysis"
    else:
        current_step = "completed"
    
    return OnboardingStatus(
        company_configured=company_configured,
        departments_configured=departments_configured,
        roles_configured=roles_configured,
        frameworks_configured=frameworks_configured,
        controls_configured=controls_configured,
        policies_uploaded=policies_uploaded,
        gap_analysis_completed=gap_analysis_completed,
        completion_percentage=completion_percentage,
        current_step=current_step
    )
