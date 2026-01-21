"""
Pinecone Service for vector database operations.
Handles policy embeddings and similarity search.
"""
from typing import List, Dict, Any, Optional
from pinecone import Pinecone
from app.core.config import settings
from app.services.ai_service import get_embedding

# Initialize Pinecone client and index (lazy initialization)
print("[Pinecone] Pinecone service module loaded")
print(f"[Pinecone] Configured Index Name: {settings.PINECONE_INDEX_NAME}")

# Global variables
_pc = None
_index = None
_index_verified = False

def reset_connection():
    """Reset the Pinecone connection (useful after config changes)."""
    global _pc, _index, _index_verified
    _pc = None
    _index = None
    _index_verified = False
    print("[Pinecone] Connection reset")


def get_index():
    """
    Get the Pinecone index instance.
    Lazy initialization - connects on first use.
    Verifies index dimensions match expected embedding size.
    """
    global _index, _pc, _index_verified
    
    # Check configuration
    if not settings.PINECONE_API_KEY:
        error_msg = "PINECONE_API_KEY not set in environment variables"
        print(f"[Pinecone] ✗ ERROR: {error_msg}")
        raise Exception(error_msg)
    
    if not settings.PINECONE_INDEX_NAME:
        error_msg = "PINECONE_INDEX_NAME not set in environment variables"
        print(f"[Pinecone] ✗ ERROR: {error_msg}")
        raise Exception(error_msg)
    
    # Initialize if not already done
    if _index is None:
        print("\n[Pinecone] ===== Initializing Pinecone Connection =====")
        print(f"[Pinecone] API Key: {'*' * 20}...{settings.PINECONE_API_KEY[-4:] if len(settings.PINECONE_API_KEY) > 4 else '****'}")
        print(f"[Pinecone] Index Name: {settings.PINECONE_INDEX_NAME}")
        print(f"[Pinecone] Environment: {settings.PINECONE_ENVIRONMENT}")
        
        try:
            _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            print("[Pinecone] ✓ Pinecone client created")
            
            # Get index
            _index = _pc.Index(settings.PINECONE_INDEX_NAME)
            print(f"🔥 Pinecone Connected: {settings.PINECONE_INDEX_NAME}")
            
            # Verify index exists and get stats
            try:
                stats = _index.describe_index_stats()
                print(f"[Pinecone] Index Stats:")
                print(f"[Pinecone]   - Dimension: {stats.dimension}")
                print(f"[Pinecone]   - Total Vector Count: {stats.total_vector_count}")
                print(f"[Pinecone]   - Namespaces: {list(stats.namespaces.keys()) if stats.namespaces else ['default']}")
                
                # Verify dimension matches expected (1536 for text-embedding-3-small)
                expected_dimension = 1536
                if stats.dimension != expected_dimension:
                    error_msg = f"Index dimension mismatch! Index has {stats.dimension} dimensions but embedding model produces {expected_dimension}. Please use an index with {expected_dimension} dimensions."
                    print(f"[Pinecone] ✗✗✗ ERROR: {error_msg}")
                    _index = None  # Reset so we don't use wrong index
                    raise Exception(error_msg)
                
                print(f"[Pinecone] ✓ Index dimension verified: {stats.dimension}")
                _index_verified = True
                
            except Exception as stats_error:
                if "dimension" in str(stats_error).lower():
                    raise
                print(f"[Pinecone] ⚠ Could not get index stats: {stats_error}")
                # Continue anyway - stats might fail but index could still work
            
            print("[Pinecone] ✓✓✓ Pinecone service ready! ✓✓✓")
            print("[Pinecone] ===== Connection Complete =====\n")
            
        except Exception as e:
            import traceback
            print(f"[Pinecone] ✗ ERROR connecting to Pinecone: {str(e)}")
            print(f"[Pinecone] Traceback:\n{traceback.format_exc()}")
            _index = None
            _pc = None
            raise Exception(f"Error connecting to Pinecone index: {str(e)}")
    
    return _index


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[str]:
    """
    Chunk text into overlapping segments.
    Ensures no content loss by properly chunking with overlap.
    
    Args:
        text: Text to chunk (full raw text, not truncated)
        chunk_size: Size of each chunk (default: 900 chars)
        overlap: Overlap between chunks (default: 150 chars)
    
    Returns:
        List of text chunks with proper overlap
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        # Move start position forward by chunk_size minus overlap
        start = end - overlap
        # Prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            start += 1
    
    return chunks


def index_policy_embedding(
    policy_id: int,
    policy_title: str,
    policy_content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Index a policy's embedding in Pinecone with chunking support.
    
    Args:
        policy_id: Unique identifier for the policy
        policy_title: Title of the policy
        policy_content: Full content of the policy
        metadata: Additional metadata to store (optional)
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n[Pinecone] ===== Indexing Policy {policy_id} =====")
    print(f"[Pinecone] Title: {policy_title}")
    print(f"[Pinecone] Content length: {len(policy_content)} characters")
    
    try:
        # Validate content
        if not policy_content or not policy_content.strip():
            print(f"[Pinecone] ✗ WARNING: Empty content, skipping indexing")
            return False
        
        # Get index (this will verify dimensions)
        print(f"[Pinecone] Getting Pinecone index...")
        index = get_index()
        print(f"[Pinecone] ✓ Index retrieved")
        
        # PART 4: FIX PINECONE CONTENT LOSS
        # Chunk policies properly to prevent content loss (500-1000 char truncation)
        # Use full raw text content, not truncated version
        raw_text = policy_content  # Ensure we use full content, not truncated
        print(f"[Pinecone] Using full content: {len(raw_text)} characters (no truncation)")
        
        # Chunk the policy content with proper overlap
        chunks = chunk_text(raw_text, chunk_size=900, overlap=150)
        print(f"[Pinecone] Content chunked into {len(chunks)} segments")
        
        if len(chunks) == 0:
            print(f"[Pinecone] ✗ WARNING: No chunks created from content")
            return False
        
        # Extract metadata values
        company_id = metadata.get("company_id") if metadata else None
        framework_id = metadata.get("framework_id") if metadata else None
        # Handle control_ids - could be single control_id or list
        control_id = metadata.get("control_id") if metadata else None
        control_ids = metadata.get("control_ids") if metadata else None
        # If control_ids not provided but control_id is, use control_id
        if not control_ids and control_id is not None:
            control_ids = [control_id] if isinstance(control_id, int) else control_id
        
        # Index each chunk
        vectors_to_upsert = []
        total_upserted = 0
        embedding_dim = None
        
        for i, chunk in enumerate(chunks):
            # Generate embedding for this chunk (use chunk only, not title+chunk for better similarity)
            print(f"[Pinecone] Generating embedding for chunk {i + 1}/{len(chunks)} (length: {len(chunk)} chars)...")
            
            # Use chunk text for embedding (title is already in metadata)
            embedding = get_embedding(chunk)
            if embedding:
                # Set embedding_dim on first iteration if not already set
                if embedding_dim is None:
                    embedding_dim = len(embedding)
            else:
                raise ValueError("Embedding generation failed")
            
            # Store FULL metadata with complete chunk text (no truncation)
            chunk_metadata = {
                "policy_id": policy_id,
                "framework_id": framework_id,
                "company_id": company_id,
                "text": chunk  # Store FULL chunk text (critical for content retrieval)
            }
            
            # Add control_ids if available
            if control_ids:
                chunk_metadata["control_ids"] = control_ids
            elif control_id:
                chunk_metadata["control_id"] = control_id
            
            # Add policy title and status
            chunk_metadata["policy_title"] = str(policy_title)
            if metadata and metadata.get("status"):
                chunk_metadata["status"] = metadata.get("status")
            
            # Add chunk indexing info
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            # Add any additional metadata fields (filtering out None values)
            if metadata:
                for key, value in metadata.items():
                    # Skip fields we've already handled explicitly
                    if key not in ["company_id", "framework_id", "control_id", "control_ids", "status"]:
                        if value is not None:
                            # Convert to appropriate type for Pinecone
                            if isinstance(value, (str, int, float, bool, list)):
                                chunk_metadata[key] = value
                            else:
                                chunk_metadata[key] = str(value)
            
            # Create vector ID with chunk index (matching user specification format)
            vector_id = f"policy-{policy_id}-{i}"
            
            vectors_to_upsert.append({
                "id": vector_id,
                "values": embedding,
                "metadata": chunk_metadata
            })
            
            print(f"[Pinecone] ✓ Chunk {i + 1} prepared (length: {len(chunk)} chars, stored in metadata['text'])")
        
        # Upsert all chunks to Pinecone
        print(f"[Pinecone] Upserting {len(vectors_to_upsert)} chunks to Pinecone...")
        print(f"[Pinecone] Embedding dimension: {embedding_dim}")
        print(f"[Pinecone] Index name: {settings.PINECONE_INDEX_NAME}")
        
        try:
            # Upsert in batches if needed (Pinecone supports up to 100 vectors per upsert)
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                pinecone_response = index.upsert(vectors=batch)
                
                # Log response
                if hasattr(pinecone_response, 'upserted_count'):
                    batch_upserted = pinecone_response.upserted_count
                    total_upserted += batch_upserted
                    print(f"[Pinecone] Batch {i//batch_size + 1}: {batch_upserted} chunks upserted")
                else:
                    total_upserted += len(batch)
                    print(f"[Pinecone] Batch {i//batch_size + 1}: {len(batch)} chunks upserted (assumed)")
            
            if total_upserted > 0:
                print(f"[Pinecone] ✓✓✓ Policy {policy_id} indexed successfully! ✓✓✓")
                print(f"[Pinecone] Total chunks indexed: {total_upserted}/{len(chunks)}")
                print(f"[Pinecone] ===== Indexing Complete =====\n")
                return True
            else:
                print(f"[Pinecone] ⚠ WARNING: No chunks were upserted!")
                print(f"[Pinecone] ===== Indexing May Have Failed =====\n")
                return False
            
        except Exception as upsert_error:
            import traceback
            print(f"[Pinecone] ✗✗✗ UPSERT ERROR: {str(upsert_error)} ✗✗✗")
            print(f"[Pinecone] Upsert Traceback:\n{traceback.format_exc()}")
            raise
        
    except Exception as e:
        import traceback
        print(f"[Pinecone] ✗✗✗ ERROR indexing policy {policy_id}: {str(e)} ✗✗✗")
        print(f"[Pinecone] Traceback:\n{traceback.format_exc()}")
        print(f"[Pinecone] ===== Indexing Failed =====\n")
        
        # Reset connection on dimension mismatch error
        if "dimension" in str(e).lower():
            print("[Pinecone] Resetting connection due to dimension error...")
            reset_connection()
        
        raise Exception(f"Error indexing policy embedding: {str(e)}")


def index_control_embedding(
    control_id: int,
    control_code: str,
    control_name: str,
    control_description: str,
    framework_id: Optional[int] = None,
    control_group_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Index a control's embedding in Pinecone.
    This makes controls searchable for AI chat and gap analysis.
    
    Args:
        control_id: Unique identifier for the control
        control_code: Code of the control (e.g., "A.5.1")
        control_name: Name of the control
        control_description: Full description of the control
        framework_id: Framework ID (optional)
        control_group_id: Control group ID (optional)
        metadata: Additional metadata to store (optional)
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n[Pinecone] ===== Indexing Control {control_id} =====")
    print(f"[Pinecone] Code: {control_code}")
    print(f"[Pinecone] Name: {control_name}")
    print(f"[Pinecone] Description length: {len(control_description)} characters")
    
    try:
        # Validate content
        if not control_description or not control_description.strip():
            print(f"[Pinecone] ✗ WARNING: Empty description, skipping indexing")
            return False
        
        # Get index
        print(f"[Pinecone] Getting Pinecone index...")
        index = get_index()
        print(f"[Pinecone] ✓ Index retrieved")
        
        # Prepare text to embed (combine code, name, and description)
        text_to_embed = f"Control {control_code}: {control_name}\n\n{control_description}"
        
        # Generate embedding
        print(f"[Pinecone] Generating embedding...")
        embedding = get_embedding(text_to_embed)
        embedding_dim = len(embedding)
        
        # Prepare metadata
        base_metadata = {
            "control_id": control_id,
            "control_code": str(control_code),
            "title": str(control_name),
            "content": control_description,
            "type": "control",  # Distinguish from policies
        }
        
        if framework_id:
            base_metadata["framework_id"] = framework_id
        
        if control_group_id:
            base_metadata["control_group_id"] = control_group_id
        
        # Add additional metadata
        if metadata:
            for key, value in metadata.items():
                if value is not None:
                    if isinstance(value, (str, int, float, bool)):
                        base_metadata[key] = value
                    else:
                        base_metadata[key] = str(value)
        
        # Create vector ID
        vector_id = f"control_{control_id}"
        
        # Upsert to Pinecone
        print(f"[Pinecone] Upserting control to Pinecone...")
        print(f"[Pinecone] Embedding dimension: {embedding_dim}")
        
        try:
            index.upsert(vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": base_metadata
            }])
            
            print(f"[Pinecone] ✓✓✓ Control {control_id} indexed successfully! ✓✓✓")
            print(f"[Pinecone] ===== Indexing Complete =====\n")
            return True
            
        except Exception as upsert_error:
            import traceback
            print(f"[Pinecone] ✗✗✗ UPSERT ERROR: {str(upsert_error)} ✗✗✗")
            print(f"[Pinecone] Upsert Traceback:\n{traceback.format_exc()}")
            raise
        
    except Exception as e:
        import traceback
        print(f"[Pinecone] ✗✗✗ ERROR indexing control {control_id}: {str(e)} ✗✗✗")
        print(f"[Pinecone] Traceback:\n{traceback.format_exc()}")
        raise Exception(f"Error indexing control embedding: {str(e)}")


def query_similar_policies(
    query_text: str,
    top_k: int = 8,
    filter_metadata: Optional[Dict[str, Any]] = None,
    similarity_threshold: float = 0.65  # PART 1: Changed to 0.65 threshold
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for similar policies based on text similarity.
    Applies similarity threshold to filter low-quality matches.
    
    Args:
        query_text: The text to search for similar policies
        top_k: Number of similar policies to return (default: 8)
        filter_metadata: Optional metadata filters (e.g., {"framework_id": 1, "status": "approved"})
        similarity_threshold: Minimum similarity score (0-1), default 0.75
    
    Returns:
        List of dictionaries containing:
        - policy_id: int
        - title: str
        - content: str
        - score: float (similarity score)
        - metadata: dict
        - chunk_index: int (if chunked)
    """
    try:
        index = get_index()
        
        # Generate embedding for query text
        print(f"[Pinecone Query] Generating embedding for query (length: {len(query_text)} chars)")
        query_embedding = get_embedding(query_text)
        
        # Build query parameters - request more results to filter by threshold
        query_kwargs = {
            "vector": query_embedding,
            "top_k": top_k * 2,  # Request more to filter by threshold
            "include_metadata": True
        }
        
        # Add metadata filter if provided
        if filter_metadata:
            try:
                # Check if it's already in Pinecone format (has operators like $eq)
                has_operator = False
                if isinstance(filter_metadata, dict):
                    has_operator = any(
                        isinstance(v, dict) and any(k.startswith('$') for k in v.keys()) 
                        for v in filter_metadata.values() if isinstance(v, dict)
                    )
                
                if not has_operator and isinstance(filter_metadata, dict):
                    # Convert simple dict to Pinecone serverless format
                    pinecone_filter = {}
                    for key, value in filter_metadata.items():
                        if value is not None:
                            if isinstance(value, bool):
                                pinecone_filter[key] = value
                            else:
                                pinecone_filter[key] = {"$eq": value}
                    query_kwargs["filter"] = pinecone_filter
                    print(f"[Pinecone Query] Filter applied: {pinecone_filter}")
                else:
                    query_kwargs["filter"] = filter_metadata
            except Exception as filter_error:
                # If filter format fails, try without filter
                print(f"[Pinecone Query] Warning: Filter format error, querying without filter: {str(filter_error)}")
                # Continue without filter - less secure but functional
        
        # Query Pinecone
        try:
            results = index.query(**query_kwargs)
        except Exception as query_error:
            # If query with filter fails, try without filter
            if filter_metadata:
                print(f"[Pinecone Query] Warning: Query with filter failed, retrying without filter: {str(query_error)}")
                query_kwargs.pop("filter", None)
                results = index.query(**query_kwargs)
            else:
                raise
        
        # Format results and apply similarity threshold
        similar_policies = []
        for match in results.matches:
            similarity_score = float(match.score)
            
            # Apply similarity threshold
            if similarity_score < similarity_threshold:
                print(f"[Pinecone Query] Skipping match with score {similarity_score:.3f} (below threshold {similarity_threshold})")
                continue
            
            metadata = match.metadata or {}
            
            # Handle both policies and controls
            if metadata.get("type") == "control":
                policy_data = {
                    "control_id": metadata.get("control_id"),
                    "control_code": metadata.get("control_code"),
                    "title": metadata.get("title", "Unknown"),
                    "content": metadata.get("content", ""),
                    "score": similarity_score,
                    "metadata": metadata,
                    "type": "control"
                }
                print(f"[Pinecone Query] ✓ Match (Control): {policy_data['title']} (score: {similarity_score:.3f}, code: {metadata.get('control_code', 'N/A')})")
            else:
                # Get chunk text - use "text" (new) or fallback to "content" (old) for backward compatibility
                chunk_text = metadata.get("text") or metadata.get("content", "")
                policy_data = {
                    "policy_id": metadata.get("policy_id"),
                    "title": metadata.get("policy_title") or metadata.get("title", "Unknown"),
                    "content": chunk_text,  # Full chunk text (stored as "text" in new format)
                    "score": similarity_score,
                    "metadata": metadata,
                    "chunk_index": metadata.get("chunk_index"),
                    "total_chunks": metadata.get("total_chunks"),
                    "type": "policy"
                }
                print(f"[Pinecone Query] ✓ Match (Policy): {policy_data['title']} (score: {similarity_score:.3f}, chunk: {metadata.get('chunk_index', 'N/A')})")
            
            similar_policies.append(policy_data)
        
        # Limit to top_k after filtering
        similar_policies = similar_policies[:top_k]
        
        print(f"[Pinecone Query] Returning {len(similar_policies)} policies (after threshold filter)")
        return similar_policies
        
    except Exception as e:
        import traceback
        print(f"[Pinecone Query] ✗ ERROR: {str(e)}")
        print(f"[Pinecone Query] Traceback:\n{traceback.format_exc()}")
        raise Exception(f"Error querying similar policies: {str(e)}")


def delete_policy_embedding(policy_id: int) -> bool:
    """
    Delete a policy's embedding from Pinecone.
    
    Args:
        policy_id: ID of the policy to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        index = get_index()
        index.delete(ids=[f"policy_{policy_id}"])
        return True
    except Exception as e:
        raise Exception(f"Error deleting policy embedding: {str(e)}")


def query_knowledge_base_chunks(
    query_text: str,
    framework_id: int,
    top_k: int = 5,
    similarity_threshold: float = 0.70
) -> List[Dict[str, Any]]:
    """
    Query Pinecone for knowledge base chunks related to a control.
    Searches in the knowledge base namespace for the framework.
    
    Args:
        query_text: The control text or requirement to search for
        framework_id: ID of the framework (determines namespace)
        top_k: Number of chunks to return (default: 5)
        similarity_threshold: Minimum similarity score (0-1), default 0.70
    
    Returns:
        List of dictionaries containing:
        - kb_doc_id: int
        - title: str
        - text: str (chunk content)
        - score: float (similarity score)
        - metadata: dict
    """
    try:
        index = get_index()
        namespace = f"kb-{framework_id}"
        
        # Generate embedding for query text
        print(f"[KB Query] Generating embedding for KB query (length: {len(query_text)} chars)")
        query_embedding = get_embedding(query_text)
        
        # Query knowledge base namespace
        query_kwargs = {
            "vector": query_embedding,
            "top_k": top_k * 2,  # Request more to filter by threshold
            "include_metadata": True,
            "namespace": namespace
        }
        
        print(f"[KB Query] Querying namespace: {namespace}")
        results = index.query(**query_kwargs)
        
        # Format results and apply similarity threshold
        kb_chunks = []
        for match in results.matches:
            similarity_score = float(match.score)
            
            # Apply similarity threshold
            if similarity_score < similarity_threshold:
                print(f"[KB Query] Skipping match with score {similarity_score:.3f} (below threshold {similarity_threshold})")
                continue
            
            metadata = match.metadata or {}
            chunk_text = metadata.get("text", "")
            
            kb_data = {
                "kb_doc_id": metadata.get("kb_doc_id"),
                "title": metadata.get("title", "Unknown"),
                "text": chunk_text,
                "score": similarity_score,
                "metadata": metadata
            }
            
            kb_chunks.append(kb_data)
            print(f"[KB Query] ✓ Match: {kb_data['title']} (score: {similarity_score:.3f})")
        
        # Limit to top_k after filtering
        kb_chunks = kb_chunks[:top_k]
        
        print(f"[KB Query] Returning {len(kb_chunks)} KB chunks (after threshold filter)")
        return kb_chunks
        
    except Exception as e:
        import traceback
        print(f"[KB Query] ✗ ERROR: {str(e)}")
        print(f"[KB Query] Traceback:\n{traceback.format_exc()}")
        # Return empty list on error (will be treated as GAP)
        return []


def verify_pinecone_config() -> Dict[str, Any]:
    """
    Verify Pinecone configuration and return diagnostic info.
    Useful for troubleshooting.
    """
    result = {
        "api_key_set": bool(settings.PINECONE_API_KEY),
        "api_key_length": len(settings.PINECONE_API_KEY) if settings.PINECONE_API_KEY else 0,
        "index_name": settings.PINECONE_INDEX_NAME,
        "environment": settings.PINECONE_ENVIRONMENT,
        "connection_status": "unknown",
        "index_dimension": None,
        "vector_count": None,
        "error": None
    }
    
    try:
        index = get_index()
        stats = index.describe_index_stats()
        result["connection_status"] = "connected"
        result["index_dimension"] = stats.dimension
        result["vector_count"] = stats.total_vector_count
    except Exception as e:
        result["connection_status"] = "failed"
        result["error"] = str(e)
    
    return result
