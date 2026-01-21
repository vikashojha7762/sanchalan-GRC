"""
Script to re-index all existing policies in Pinecone.
Useful if policies were uploaded before Pinecone was properly configured.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal
from app.models import Policy
from app.services.pinecone_service import index_policy_embedding

def reindex_all_policies():
    """Re-index all policies from the database to Pinecone."""
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("RE-INDEXING ALL POLICIES TO PINECONE")
        print("="*80 + "\n")
        
        # Get all active policies
        policies = db.query(Policy).filter(Policy.is_active == True).all()
        
        print(f"Found {len(policies)} active policies in database\n")
        
        if len(policies) == 0:
            print("No policies to index. Exiting.\n")
            return
        
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for policy in policies:
            print(f"\n{'='*80}")
            print(f"Processing Policy ID: {policy.id}")
            print(f"Title: {policy.title}")
            print(f"{'='*80}")
            
            try:
                # Prepare content
                policy_content = policy.content or policy.description or ""
                
                if not policy_content.strip():
                    print(f"⚠ SKIPPED: Policy {policy.id} has no content")
                    skipped_count += 1
                    continue
                
                print(f"Content length: {len(policy_content)} characters")
                
                # Prepare metadata
                metadata = {
                    "company_id": policy.owner.company_id if policy.owner else None,
                    "framework_id": policy.framework_id,
                    "control_id": policy.control_id,
                    "policy_number": policy.policy_number,
                    "status": policy.status.value if policy.status else None
                }
                
                # Index in Pinecone
                success = index_policy_embedding(
                    policy_id=policy.id,
                    policy_title=policy.title,
                    policy_content=policy_content,
                    metadata=metadata
                )
                
                if success:
                    print(f"✓ Policy {policy.id} indexed successfully")
                    success_count += 1
                else:
                    print(f"✗ Policy {policy.id} indexing returned False")
                    failed_count += 1
                    
            except Exception as e:
                import traceback
                print(f"✗ ERROR indexing policy {policy.id}: {str(e)}")
                print(f"Traceback:\n{traceback.format_exc()}")
                failed_count += 1
        
        print("\n" + "="*80)
        print("RE-INDEXING SUMMARY")
        print("="*80)
        print(f"Total policies: {len(policies)}")
        print(f"✓ Successfully indexed: {success_count}")
        print(f"✗ Failed: {failed_count}")
        print(f"⚠ Skipped (no content): {skipped_count}")
        print("="*80 + "\n")
        
    except Exception as e:
        import traceback
        print(f"\n✗✗✗ FATAL ERROR: {str(e)} ✗✗✗")
        print(f"Traceback:\n{traceback.format_exc()}\n")
    finally:
        db.close()

if __name__ == "__main__":
    reindex_all_policies()

