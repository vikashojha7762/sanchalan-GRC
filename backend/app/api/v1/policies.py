from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from app.db import get_db
from app.models import Policy, PolicyStatus, User
from app.api.v1.auth import get_current_user
from app.schemas.policy import PolicyCreate, PolicyResponse
from app.services.pinecone_service import index_policy_embedding, get_index
from app.services.ai_service import get_embedding
from app.utils.text_extraction import extract_text_from_file

router = APIRouter()


@router.post("/upload", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def upload_policy(
    policy_data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new policy and index it in Pinecone.
    """
    # Check if policy number already exists
    if policy_data.policy_number:
        existing = db.query(Policy).filter(
            Policy.policy_number == policy_data.policy_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Policy number already exists"
            )
    
    # Create policy
    policy = Policy(
        title=policy_data.title,
        description=policy_data.description,
        content=policy_data.content,
        policy_number=policy_data.policy_number,
        version=policy_data.version,
        framework_id=policy_data.framework_id,
        control_id=policy_data.control_id,
        effective_date=policy_data.effective_date,
        review_date=policy_data.review_date,
        owner_id=current_user.id,
        status=PolicyStatus.UNDER_REVIEW,  # Set to UNDER_REVIEW for approval workflow
        is_active=True
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    # Index policy in Pinecone
    print(f"\n[API] ===== Indexing Policy {policy.id} in Pinecone =====")
    print(f"[API] Policy Title: {policy.title}")
    print(f"[API] Policy ID: {policy.id}")
    print(f"[API] Company ID: {current_user.company_id}")
    
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
            print(f"[API] ✗ WARNING: Policy {policy.id} has no content. Skipping Pinecone indexing.")
        else:
            print(f"[API] Policy content available: {len(policy_content)} characters")
            print(f"[API] Calling index_policy_embedding...")
            
            success = index_policy_embedding(
                policy_id=policy.id,
                policy_title=policy.title,
                policy_content=policy_content,
                metadata=metadata
            )
            
            if success:
                print(f"[API] ✓✓✓ Policy {policy.id} successfully indexed in Pinecone! ✓✓✓")
            else:
                print(f"[API] ✗ Policy {policy.id} indexing returned False")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] ✗✗✗ ERROR indexing policy {policy.id} in Pinecone: {str(e)} ✗✗✗")
        print(f"[API] Full traceback:\n{error_trace}")
    
    print(f"[API] ===== Policy Upload Complete =====\n")
    return policy


@router.get("", response_model=List[PolicyResponse])
async def get_policies(
    framework_id: Optional[int] = None,
    control_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all policies with optional filtering.
    """
    query = db.query(Policy).filter(Policy.is_active == True)
    
    # Filter by company (through owner)
    query = query.join(User, Policy.owner_id == User.id).filter(
        User.company_id == current_user.company_id
    )
    
    # Apply filters
    if framework_id:
        query = query.filter(Policy.framework_id == framework_id)
    
    if control_id:
        query = query.filter(Policy.control_id == control_id)
    
    if status:
        try:
            status_enum = PolicyStatus(status.lower())
            query = query.filter(Policy.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    policies = query.order_by(Policy.created_at.desc()).all()
    return policies


@router.post("/upload-file", status_code=status.HTTP_201_CREATED)
async def upload_policy_file(
    file: UploadFile = File(...),
    framework_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a policy file (PDF, DOCX, TXT) and index it in Pinecone.
    This endpoint handles file uploads, extracts text, saves to DB, and indexes in Pinecone.
    """
    print(f"\n[API] ===== File Upload Started =====")
    print(f"[API] Filename: {file.filename}")
    print(f"[API] Content Type: {file.content_type}")
    print(f"[API] Company ID: {current_user.company_id}")
    print(f"[API] Framework ID: {framework_id}")
    
    try:
        # 1. Save file
        print(f"[API] Step 1: Saving file...")
        folder = "uploads"
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"[API] ✓ File saved to: {file_path}")
        
        # 2. Extract text
        print(f"[API] Step 2: Extracting text from file...")
        raw_text = extract_text_from_file(file_path)
        print(f"[API] ✓ Text extracted: {len(raw_text)} characters")
        
        if not raw_text or not raw_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from file. File may be empty or corrupted."
            )
        
        # 3. Save policy in DB
        print(f"[API] Step 3: Saving policy to database...")
        policy = Policy(
            title=file.filename,
            description=f"Policy uploaded from file: {file.filename}",
            content=raw_text,
            policy_number=None,
            version="1.0",
            framework_id=framework_id,
            control_id=None,
            owner_id=current_user.id,
            status=PolicyStatus.UNDER_REVIEW,  # Set to UNDER_REVIEW for approval workflow
            is_active=True
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
        print(f"[API] ✓ Policy saved to database (ID: {policy.id})")
        
        # 4. Generate embedding
        print(f"[API] Step 4: Generating embedding...")
        text_to_embed = f"{policy.title}\n\n{raw_text}"
        embedding = get_embedding(text_to_embed)
        print(f"[API] ✓ Embedding generated (dimension: {len(embedding)})")
        
        # 5. Upsert into Pinecone
        print(f"[API] Step 5: Upserting to Pinecone...")
        index = get_index()
        vector_id = f"policy_{policy.id}"
        
        metadata = {
            "policy_id": policy.id,
            "company_id": current_user.company_id,
            "framework_id": framework_id,
            "title": file.filename,
            "content": raw_text[:1000],  # First 1000 chars in metadata
            "status": policy.status.value
        }
        
        print(f"[API] Vector ID: {vector_id}")
        print(f"[API] Metadata: {list(metadata.keys())}")
        
        pinecone_response = index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                }
            ]
        )
        
        print("🔵 Pinecone Upsert Response:", pinecone_response)
        print(f"[API] ✓✓✓ Policy {policy.id} indexed in Pinecone! ✓✓✓")
        print(f"[API] ===== File Upload Complete =====\n")
        
        return {
            "message": "Policy uploaded and embedded successfully",
            "policy_id": policy.id,
            "policy_title": policy.title,
            "file_path": file_path,
            "text_length": len(raw_text),
            "embedding_dimension": len(embedding),
            "pinecone_response": str(pinecone_response),
            "vector_id": vector_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[API] ✗✗✗ ERROR uploading file: {str(e)} ✗✗✗")
        print(f"[API] Full traceback:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading policy file: {str(e)}"
        )


@router.patch("/{policy_id}", response_model=PolicyResponse, status_code=status.HTTP_200_OK)
async def update_policy_status(
    policy_id: int,
    status_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update policy status (for approval/rejection workflow).
    """
    # Get policy
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.is_active == True
    ).first()
    
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )
    
    # Verify user has access (same company)
    if policy.owner and policy.owner.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this policy"
        )
    
    # Update status if provided
    policy_approved = False
    if "status" in status_update:
        try:
            status_value = status_update["status"].lower()
            print(f"[API] Attempting to update policy {policy_id} status to: {status_value}")
            
            # Validate status value
            try:
                new_status = PolicyStatus(status_value)
            except ValueError as e:
                print(f"[API] Invalid status value: {status_value}")
                print(f"[API] Valid statuses: {[s.value for s in PolicyStatus]}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status_value}. Valid statuses are: {[s.value for s in PolicyStatus]}"
                )
            
            old_status = policy.status
            policy.status = new_status
            print(f"[API] Policy {policy_id} status updated from {old_status.value} to: {new_status.value}")
            
            # If policy is being approved, re-index in Pinecone with updated status
            if new_status == PolicyStatus.APPROVED:
                policy_approved = True
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            print(f"[API] Error updating policy status: {str(e)}")
            print(f"[API] Traceback:\n{traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating policy status: {str(e)}"
            )
    
    # Update other fields if provided
    if "title" in status_update:
        policy.title = status_update["title"]
    if "description" in status_update:
        policy.description = status_update["description"]
    if "content" in status_update:
        policy.content = status_update["content"]
    
    # Commit changes with error handling
    try:
        db.commit()
        db.refresh(policy)
        print(f"[API] ✓ Policy {policy_id} successfully updated in database")
    except Exception as e:
        import traceback
        db.rollback()
        print(f"[API] ✗ Database error updating policy {policy_id}: {str(e)}")
        print(f"[API] Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}. Please ensure the 'rejected' status exists in the database enum."
        )
    
    # Return updated policy immediately
    # Re-index policy in Pinecone if approved (to update status metadata)
    # Do this in background to avoid blocking the response
    if policy_approved:
        print(f"[API] Policy {policy_id} approved - re-indexing in Pinecone with APPROVED status...")
        try:
            # Run Pinecone re-indexing in background thread to avoid blocking
            from concurrent.futures import ThreadPoolExecutor
            
            def reindex_in_background():
                try:
                    from app.services.pinecone_service import index_policy_embedding
                    
                    metadata = {
                        "company_id": current_user.company_id,
                        "framework_id": policy.framework_id,
                        "control_id": policy.control_id,
                        "policy_number": policy.policy_number,
                        "status": "approved"
                    }
                    
                    policy_content = policy.content or policy.description or ""
                    
                    if policy_content.strip():
                        success = index_policy_embedding(
                            policy_id=policy.id,
                            policy_title=policy.title,
                            policy_content=policy_content,
                            metadata=metadata
                        )
                        if success:
                            print(f"[API] ✓ Policy {policy_id} re-indexed with APPROVED status")
                        else:
                            print(f"[API] ⚠ Policy {policy_id} re-indexing returned False")
                    else:
                        print(f"[API] ⚠ Policy {policy_id} has no content, skipping re-indexing")
                except Exception as e:
                    import traceback
                    print(f"[API] ⚠ Error re-indexing approved policy {policy_id}: {str(e)}")
                    print(f"[API] Traceback:\n{traceback.format_exc()}")
            
            # Run in background thread (non-blocking)
            executor = ThreadPoolExecutor(max_workers=1)
            executor.submit(reindex_in_background)
            executor.shutdown(wait=False)
        except Exception as e:
            print(f"[API] ⚠ Failed to start background re-indexing: {str(e)}")
            # Don't fail the approval if background task setup fails
    
    # Return policy immediately (don't wait for Pinecone)
    return policy


@router.get("/test-pinecone", status_code=status.HTTP_200_OK)
async def test_pinecone_connection(
    current_user: User = Depends(get_current_user)
):
    """
    Test Pinecone connection and configuration.
    Useful for debugging Pinecone connectivity issues.
    Returns index stats including dimension to verify compatibility.
    """
    from app.core.config import settings
    from app.services.pinecone_service import get_index, reset_connection, verify_pinecone_config
    from datetime import datetime
    
    print("\n[TEST] ===== Testing Pinecone Connection =====")
    
    # First reset connection to get fresh state
    reset_connection()
    print("[TEST] Connection reset for fresh test")
    
    results = {
        "config": {
            "api_key_set": bool(settings.PINECONE_API_KEY),
            "api_key_length": len(settings.PINECONE_API_KEY) if settings.PINECONE_API_KEY else 0,
            "index_name": settings.PINECONE_INDEX_NAME,
            "environment": settings.PINECONE_ENVIRONMENT,
            "expected_dimension": 1536  # text-embedding-3-small
        },
        "connection": None,
        "index_info": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    try:
        print(f"[TEST] Configuration Check:")
        print(f"[TEST]   - API Key Set: {results['config']['api_key_set']}")
        print(f"[TEST]   - API Key Length: {results['config']['api_key_length']}")
        print(f"[TEST]   - Index Name: {results['config']['index_name']}")
        print(f"[TEST]   - Environment: {results['config']['environment']}")
        
        if not settings.PINECONE_API_KEY:
            results["connection"] = "failed"
            results["error"] = "PINECONE_API_KEY not set"
            print(f"[TEST] ✗ ERROR: {results['error']}")
            return results
        
        if not settings.PINECONE_INDEX_NAME:
            results["connection"] = "failed"
            results["error"] = "PINECONE_INDEX_NAME not set"
            print(f"[TEST] ✗ ERROR: {results['error']}")
            return results
        
        print(f"[TEST] Getting Pinecone index...")
        index = get_index()
        print(f"[TEST] ✓ Index retrieved")
        
        # Get index stats
        print(f"[TEST] Getting index stats...")
        try:
            stats = index.describe_index_stats()
            results["index_info"] = {
                "dimension": stats.dimension,
                "total_vectors": stats.total_vector_count,
                "namespaces": list(stats.namespaces.keys()) if stats.namespaces else ["default"],
                "dimension_matches_expected": stats.dimension == 1536
            }
            print(f"[TEST] ✓ Index Stats:")
            print(f"[TEST]   - Dimension: {stats.dimension}")
            print(f"[TEST]   - Total Vectors: {stats.total_vector_count}")
            print(f"[TEST]   - Dimension Match: {stats.dimension == 1536}")
            
            if stats.dimension != 1536:
                results["connection"] = "dimension_mismatch"
                results["error"] = f"Index has {stats.dimension} dimensions but embedding model produces 1536. Please use a 1536-dimension index."
                print(f"[TEST] ✗ DIMENSION MISMATCH: {results['error']}")
                return results
                
        except Exception as stats_error:
            print(f"[TEST] ⚠ Could not get stats: {stats_error}")
            results["index_info"] = {"stats_error": str(stats_error)}
        
        # Try a simple query to verify connection
        print(f"[TEST] Testing index query (dummy vector)...")
        try:
            dummy_vector = [0.0] * 1536  # text-embedding-3-small dimension
            test_result = index.query(
                vector=dummy_vector,
                top_k=1,
                include_metadata=False
            )
            print(f"[TEST] ✓ Query test successful")
            results["connection"] = "success"
            if results["index_info"]:
                results["index_info"]["query_successful"] = True
                results["index_info"]["matches_returned"] = len(test_result.matches)
        except Exception as query_error:
            print(f"[TEST] ⚠ Query test failed: {str(query_error)}")
            if "dimension" in str(query_error).lower():
                results["connection"] = "dimension_mismatch"
                results["error"] = str(query_error)
            else:
                results["connection"] = "partial"  # Connected but query failed
                results["error"] = f"Query test failed: {str(query_error)}"
        
        print(f"[TEST] ===== Test Complete =====\n")
        return results
        
    except Exception as e:
        import traceback
        results["connection"] = "failed"
        results["error"] = str(e)
        print(f"[TEST] ✗ ERROR: {str(e)}")
        print(f"[TEST] Traceback:\n{traceback.format_exc()}")
        print(f"[TEST] ===== Test Failed =====\n")
        return results


@router.post("/reset-pinecone", status_code=status.HTTP_200_OK)
async def reset_pinecone_connection(
    current_user: User = Depends(get_current_user)
):
    """
    Reset the Pinecone connection.
    Useful after changing .env configuration.
    """
    from app.services.pinecone_service import reset_connection
    
    reset_connection()
    return {"message": "Pinecone connection reset. Next operation will reconnect with fresh settings."}
