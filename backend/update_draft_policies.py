"""
Script to update existing DRAFT policies to UNDER_REVIEW status.
Use this if you have policies that were uploaded before the fix.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal
from app.models import Policy, PolicyStatus

def update_draft_policies():
    """Update all DRAFT policies to UNDER_REVIEW."""
    db = SessionLocal()
    
    try:
        print("\n" + "="*80)
        print("UPDATING DRAFT POLICIES TO UNDER_REVIEW")
        print("="*80 + "\n")
        
        # Get all DRAFT policies
        draft_policies = db.query(Policy).filter(
            Policy.status == PolicyStatus.DRAFT,
            Policy.is_active == True
        ).all()
        
        print(f"Found {len(draft_policies)} DRAFT policies\n")
        
        if len(draft_policies) == 0:
            print("No DRAFT policies to update. Exiting.\n")
            return
        
        updated_count = 0
        
        for policy in draft_policies:
            print(f"Updating Policy ID {policy.id}: {policy.title}")
            policy.status = PolicyStatus.UNDER_REVIEW
            updated_count += 1
        
        db.commit()
        
        print("\n" + "="*80)
        print(f"SUCCESS: Updated {updated_count} policies to UNDER_REVIEW")
        print("="*80 + "\n")
        
        print("These policies will now appear in the 'Pending' tab of Approvals.\n")
        
    except Exception as e:
        import traceback
        db.rollback()
        print(f"\n✗✗✗ ERROR: {str(e)} ✗✗✗")
        print(f"Traceback:\n{traceback.format_exc()}\n")
    finally:
        db.close()

if __name__ == "__main__":
    update_draft_policies()

