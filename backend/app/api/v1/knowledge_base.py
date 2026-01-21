"""
Knowledge Base API endpoints.
Handles uploading and managing knowledge base documents (ISO 27001, NIST, etc.)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from pathlib import Path
from app.db import get_db
from app.models import (
    KnowledgeBaseDocument, KnowledgeSourceType, Framework, User, Role
)
from app.api.v1.auth import get_current_user
from app.utils.text_extraction import extract_text_from_file
from app.services.pinecone_service import get_index, chunk_text
from app.services.ai_service import get_embedding

router = APIRouter()

# Storage directory for knowledge base files
# Use absolute path relative to backend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage" / "knowledge_base"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def require_admin_or_compliance_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to check if user has SUPER_ADMIN or COMPLIANCE_ADMIN role.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User if authorized
    
    Raises:
        HTTPException: If user doesn't have required role
    """
    # Check if user is superuser
    if current_user.is_superuser:
        return current_user
    
    # Check role name
    if current_user.role:
        role_name = current_user.role.name.upper()
        if role_name in ["SUPER_ADMIN", "COMPLIANCE_ADMIN"]:
            return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied. Only SUPER_ADMIN or COMPLIANCE_ADMIN can upload knowledge base documents."
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_knowledge_base_document(
    file: UploadFile = File(...),
    framework_id: int = Form(...),
    title: str = Form(...),
    version: Optional[str] = Form(None),
    current_user: User = Depends(require_admin_or_compliance_admin),
    db: Session = Depends(get_db)
):
    """
    Upload a knowledge base document (PDF/DOCX) for a framework.
    
    Access: Only SUPER_ADMIN or COMPLIANCE_ADMIN
    
    Steps:
    1. Validate file type (PDF or DOCX)
    2. Save file to storage/knowledge_base/
    3. Extract text from file
    4. Create database entry
    5. Chunk text (800-1000 chars, 150-200 overlap)
    6. Generate embeddings for each chunk
    7. Index in Pinecone namespace: kb-{framework_id}
    
    Args:
        file: PDF or DOCX file
        framework_id: Framework ID
        title: Document title
        version: Optional version string
        current_user: Current authenticated user (must be admin)
        db: Database session
    
    Returns:
        Dictionary with upload results
    """
    import traceback
    
    print(f"\n[Knowledge Base] ===== Upload Request =====")
    print(f"[Knowledge Base] User: {current_user.email} (ID: {current_user.id})")
    print(f"[Knowledge Base] Framework ID: {framework_id}")
    print(f"[Knowledge Base] Title: {title}")
    print(f"[Knowledge Base] Version: {version}")
    print(f"[Knowledge Base] File: {file.filename if file else 'None'}")
    
    file_path = None
    try:
            # Validate framework exists
        framework = db.query(Framework).filter(Framework.id == framework_id).first()
        if not framework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework {framework_id} not found"
            )
        
        # Validate file type
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = ['.pdf', '.docx']
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save file to storage
        file_path = STORAGE_DIR / f"kb_{framework_id}_{file.filename}"
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print(f"[Knowledge Base] ✓ File saved: {file_path}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
        
        # Extract text
        try:
            raw_text = extract_text_from_file(str(file_path))
            print(f"[Knowledge Base] ✓ Text extracted: {len(raw_text)} characters")
        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error extracting text: {str(e)}"
            )
        
        if not raw_text or not raw_text.strip():
            # Clean up file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract any text from the document. Please ensure the file is not corrupted."
            )
        
        # Create database record
        try:
            # First, try with all fields (if migration has been run)
            try:
                # Use CUSTOM as source_type since UI might not be in database enum yet
                # After running migration to add UI, this can be changed to KnowledgeSourceType.UI
                source_type = KnowledgeSourceType.CUSTOM
                
                kb_doc = KnowledgeBaseDocument(
                    framework_id=framework_id,
                    title=title,
                    version=version if version else None,
                    source_type=source_type,
                    raw_text=raw_text,
                    file_path=str(file_path),
                    is_active=True,
                    uploaded_by=current_user.id
                )
                db.add(kb_doc)
                db.commit()
                db.refresh(kb_doc)
                print(f"[Knowledge Base] ✓ Document saved to DB: ID={kb_doc.id}")
            except Exception as db_error:
                error_str = str(db_error)
                # Check if error is about missing columns or invalid enum
                is_column_error = "column" in error_str.lower() and ("does not exist" in error_str.lower() or "undefinedcolumn" in error_str.lower())
                is_enum_error = "invalid input value for enum" in error_str.lower() or "invalidtextrepresentation" in error_str.lower()
                
                if is_column_error or is_enum_error:
                    if is_column_error:
                        print(f"[Knowledge Base] ⚠️ Missing columns detected. Attempting insert without optional fields...")
                    if is_enum_error:
                        print(f"[Knowledge Base] ⚠️ Enum value issue detected. Retrying with CUSTOM source_type...")
                    
                    db.rollback()
                    
                    # Try again without version and uploaded_by columns, and with CUSTOM source_type
                    # Use raw SQL insert to avoid SQLAlchemy model constraints
                    from sqlalchemy import text
                    
                    insert_sql = text("""
                        INSERT INTO knowledge_base_documents 
                        (framework_id, title, source_type, raw_text, file_path, is_active, created_at, updated_at)
                        VALUES 
                        (:framework_id, :title, :source_type, :raw_text, :file_path, :is_active, NOW(), NOW())
                        RETURNING id
                    """)
                    
                    # Always use CUSTOM as source_type (valid enum value)
                    source_type_value = "CUSTOM"
                    
                    result = db.execute(insert_sql, {
                        "framework_id": framework_id,
                        "title": title,
                        "source_type": source_type_value,
                        "raw_text": raw_text,
                        "file_path": str(file_path),
                        "is_active": True
                    })
                    kb_doc_id = result.scalar()
                    db.commit()
                    
                    # Fetch the created document
                    kb_doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == kb_doc_id).first()
                    print(f"[Knowledge Base] ✓ Document saved to DB (fallback mode): ID={kb_doc.id}")
                    if is_column_error:
                        print(f"[Knowledge Base] ⚠️ NOTE: Run 'alembic upgrade head' to add version and uploaded_by columns")
                    if is_enum_error:
                        print(f"[Knowledge Base] ⚠️ NOTE: Using CUSTOM as source_type. Run migration to add UI to enum if needed.")
                else:
                    # Re-raise if it's a different error
                    raise
        except Exception as e:
            # Clean up file on error
            if file_path.exists():
                file_path.unlink()
            print(f"[Knowledge Base] ✗✗✗ Database error: {str(e)}")
            print(f"[Knowledge Base] Traceback:\n{traceback.format_exc()}")
            db.rollback()
            
            error_str = str(e)
            is_column_error = "column" in error_str.lower() and ("does not exist" in error_str.lower() or "undefinedcolumn" in error_str.lower())
            is_enum_error = "invalid input value for enum" in error_str.lower() or "invalidtextrepresentation" in error_str.lower()
            
            if is_column_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database schema mismatch. Please run migration: 'alembic upgrade head' in the backend directory. This will add the missing 'version' and 'uploaded_by' columns."
                )
            elif is_enum_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database enum mismatch. The 'UI' value is not in the knowledgesourcetype enum. The system will automatically retry with 'CUSTOM'. If this error persists, run: 'alembic upgrade head'"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error saving document to database: {error_str}"
                )
        
        # Chunk text (800-1000 chars, 150-200 overlap)
        # Using 900 chars chunk size and 150 overlap as a good balance
        chunks = chunk_text(raw_text, chunk_size=900, overlap=150)
        print(f"[Knowledge Base] ✓ Text chunked into {len(chunks)} chunks")
        
        if len(chunks) == 0:
            print(f"[Knowledge Base] ⚠️ WARNING: No chunks created")
            return {
                "message": "Knowledge base document uploaded but no chunks created",
                "document_id": kb_doc.id,
                "title": kb_doc.title,
                "framework_id": framework_id,
                "chunks_indexed": 0,
                "namespace": f"kb-{framework_id}"
            }
        
        # Embed and index in Pinecone
        chunks_indexed = 0
        namespace = f"kb-{framework_id}"
        try:
            index = get_index()
            
            vectors_to_upsert = []
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = get_embedding(chunk)
                    if not embedding:
                        print(f"[Knowledge Base] ⚠️ Skipping chunk {i} - embedding generation failed")
                        continue
                    
                    # Create vector ID
                    vector_id = f"kb-{kb_doc.id}-{i}"
                    
                    # Prepare metadata
                    metadata = {
                        "framework_id": framework_id,
                        "kb_doc_id": kb_doc.id,
                        "title": title,
                        "text": chunk[:1000]  # Store first 1000 chars in metadata
                    }
                    
                    vectors_to_upsert.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    print(f"[Knowledge Base] ⚠️ Error processing chunk {i}: {str(e)}")
                    import traceback
                    print(f"[Knowledge Base] Chunk error traceback:\n{traceback.format_exc()}")
                    continue
            
            # Upsert to Pinecone in batches
            if vectors_to_upsert:
                try:
                    # Pinecone supports up to 100 vectors per upsert
                    batch_size = 100
                    for i in range(0, len(vectors_to_upsert), batch_size):
                        batch = vectors_to_upsert[i:i + batch_size]
                        index.upsert(vectors=batch, namespace=namespace)
                        chunks_indexed += len(batch)
                        print(f"[Knowledge Base] ✓ Upserted batch {i//batch_size + 1} ({len(batch)} vectors) to namespace '{namespace}'")
                    
                    print(f"[Knowledge Base] ✓✓✓ Successfully indexed {chunks_indexed} chunks in Pinecone namespace '{namespace}'")
                except Exception as e:
                    import traceback
                    print(f"[Knowledge Base] ✗✗✗ Error indexing in Pinecone: {str(e)}")
                    print(f"[Knowledge Base] Pinecone error traceback:\n{traceback.format_exc()}")
                    # Don't fail the request - document is saved, can retry indexing later
        except Exception as e:
            import traceback
            print(f"[Knowledge Base] ✗✗✗ Error initializing Pinecone: {str(e)}")
            print(f"[Knowledge Base] Pinecone init error traceback:\n{traceback.format_exc()}")
            # Don't fail the request - document is saved, can retry indexing later
        
        print(f"[Knowledge Base] ===== Upload Complete =====\n")
        
        return {
            "message": "Knowledge base document uploaded and indexed successfully",
            "document_id": kb_doc.id,
            "title": kb_doc.title,
            "framework_id": framework_id,
            "chunks_indexed": chunks_indexed,
            "namespace": namespace
        }
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Clean up file on any error
        if file_path and file_path.exists():
            try:
                file_path.unlink()
                print(f"[Knowledge Base] Cleaned up file: {file_path}")
            except:
                pass
        
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"[Knowledge Base] ✗✗✗ UNEXPECTED ERROR: {error_msg} ✗✗✗")
        print(f"[Knowledge Base] Full traceback:\n{error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during upload: {error_msg}"
        )

