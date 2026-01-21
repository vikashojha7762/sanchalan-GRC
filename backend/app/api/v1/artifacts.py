"""
Artifacts API endpoints.
Handles uploading and fetching artifacts linked to gaps, policies, and controls.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from app.db import get_db
from app.models import Artifact, ArtifactType, Gap, User
from app.api.v1.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

# Storage directory for artifacts
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "uploads" / "artifacts"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Ensure uploads directory exists
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


class ArtifactResponse(BaseModel):
    """Artifact response model."""
    id: int
    name: str
    description: Optional[str] = None
    artifact_type: str
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    gap_id: Optional[int] = None
    policy_id: Optional[int] = None
    control_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/upload", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def upload_artifact(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    artifact_type: str = Form("document"),
    policy_id: Optional[int] = Form(None),
    gap_id: Optional[int] = Form(None),
    control_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an artifact (document, evidence, etc.).
    
    Args:
        file: The file to upload
        name: Artifact name
        description: Optional description
        artifact_type: Type of artifact (document, evidence, report, etc.)
        policy_id: Optional policy ID to link
        gap_id: Optional gap ID to link
        control_id: Optional control ID to link
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        Created artifact record
    """
    try:
        # Validate artifact type
        try:
            artifact_type_enum = ArtifactType(artifact_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid artifact type: {artifact_type}"
            )
        
        # Validate linked entities exist if provided
        if gap_id:
            gap = db.query(Gap).filter(Gap.id == gap_id, Gap.is_active == True).first()
            if not gap:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Gap {gap_id} not found"
                )
        
        # Save file
        # Sanitize filename to avoid path issues
        safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
        file_path = STORAGE_DIR / f"{current_user.id}_{safe_filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Store relative path from uploads directory for serving
        # Path format: uploads/artifacts/{user_id}_{filename}
        relative_path = f"uploads/artifacts/{current_user.id}_{safe_filename}"
        
        # Create artifact record
        artifact = Artifact(
            name=name,
            description=description,
            artifact_type=artifact_type_enum,
            file_path=relative_path,  # Store path relative to project root for static serving
            file_size=file_size,
            mime_type=file.content_type,
            policy_id=policy_id,
            gap_id=gap_id,
            control_id=control_id,
            uploaded_by_id=current_user.id,
            is_active=True
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        return artifact
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading artifact: {str(e)}"
        )


@router.get("", response_model=List[ArtifactResponse])
async def get_artifacts(
    gap_id: Optional[int] = None,
    policy_id: Optional[int] = None,
    control_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all artifacts, optionally filtered by gap_id, policy_id, or control_id.
    Returns artifacts uploaded by the current user's company.
    
    Args:
        gap_id: Optional filter by gap ID
        policy_id: Optional filter by policy ID
        control_id: Optional filter by control ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of artifacts
    """
    query = db.query(Artifact).filter(Artifact.is_active == True)
    
    # Filter by linked entity if provided
    if gap_id:
        query = query.filter(Artifact.gap_id == gap_id)
    if policy_id:
        query = query.filter(Artifact.policy_id == policy_id)
    if control_id:
        query = query.filter(Artifact.control_id == control_id)
    
    # Filter by user's company (through uploaded_by)
    query = query.join(User, Artifact.uploaded_by_id == User.id).filter(
        User.company_id == current_user.company_id
    )
    
    artifacts = query.order_by(Artifact.created_at.desc()).all()
    return artifacts


@router.get("/by-gap/{gap_id}", response_model=List[ArtifactResponse])
async def get_artifacts_by_gap(
    gap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all artifacts linked to a specific gap.
    
    Args:
        gap_id: ID of the gap
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of artifacts linked to the gap
    """
    # Verify gap exists
    gap = db.query(Gap).filter(
        Gap.id == gap_id,
        Gap.is_active == True
    ).first()
    
    if not gap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gap not found"
        )
    
    # Fetch artifacts for this gap
    artifacts = db.query(Artifact).filter(
        Artifact.gap_id == gap_id,
        Artifact.is_active == True
    ).order_by(Artifact.created_at.desc()).all()
    
    return artifacts


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download an artifact file.
    
    Args:
        artifact_id: ID of the artifact
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        File response for download
    """
    # Get artifact
    artifact = db.query(Artifact).filter(
        Artifact.id == artifact_id,
        Artifact.is_active == True
    ).first()
    
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact not found"
        )
    
    # Verify user has access (same company)
    if artifact.uploaded_by:
        uploader = db.query(User).filter(User.id == artifact.uploaded_by_id).first()
        if uploader and uploader.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this artifact"
            )
    
    # Get file path
    if not artifact.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found for this artifact"
        )
    
    # Construct full file path
    file_path = BASE_DIR / artifact.file_path
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File does not exist on server"
        )
    
    # Return file with proper headers
    return FileResponse(
        path=str(file_path),
        filename=artifact.name or file_path.name,
        media_type=artifact.mime_type or "application/octet-stream"
    )

