"""
PART 3 — CLEAN EXISTING INVALID DATA (ONE-TIME FIX)

This script removes invalid control IDs from control_selections table.
Control IDs that don't exist in the controls table will be removed.

Usage:
    python cleanup_invalid_control_selections.py
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models.control import Control
from app.models.control_selection import ControlSelection


def cleanup_invalid_control_selections():
    """
    Remove invalid control IDs from control_selections.
    Invalid = control IDs that don't exist in controls table.
    """
    db = SessionLocal()
    
    try:
        # Get all control selections
        selections = db.query(ControlSelection).all()
        
        print(f"Found {len(selections)} control selections to check...")
        
        # Get all valid control IDs from database
        valid_control_ids = {c.id for c in db.query(Control.id).all()}
        print(f"Found {len(valid_control_ids)} valid control IDs in database")
        
        cleaned_count = 0
        removed_count = 0
        
        for selection in selections:
            if not selection.selected_control_ids:
                continue
            
            # Parse control IDs (handle both list and JSON string)
            control_ids = selection.selected_control_ids
            if isinstance(control_ids, str):
                try:
                    control_ids = json.loads(control_ids)
                except (json.JSONDecodeError, TypeError):
                    print(f"Warning: Could not parse selected_control_ids for selection {selection.id}")
                    continue
            
            if not isinstance(control_ids, list):
                continue
            
            # Filter out invalid IDs
            valid_ids = [cid for cid in control_ids if cid in valid_control_ids]
            invalid_ids = [cid for cid in control_ids if cid not in valid_control_ids]
            
            if invalid_ids:
                print(f"Selection {selection.id} (Company {selection.company_id}, Framework {selection.framework_id}):")
                print(f"  Found {len(invalid_ids)} invalid control IDs: {invalid_ids[:10]}...")  # Show first 10
                print(f"  Keeping {len(valid_ids)} valid control IDs")
                
                # Update selection with only valid IDs
                selection.selected_control_ids = valid_ids
                cleaned_count += 1
                removed_count += len(invalid_ids)
        
        if cleaned_count > 0:
            db.commit()
            print(f"\n✅ Cleanup complete!")
            print(f"  - Cleaned {cleaned_count} selections")
            print(f"  - Removed {removed_count} invalid control IDs")
        else:
            print("\n✅ No invalid control IDs found. All selections are valid.")
    
    except Exception as e:
        db.rollback()
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("PART 3: CLEANUP INVALID CONTROL SELECTIONS")
    print("=" * 60)
    print()
    
    if cleanup_invalid_control_selections():
        print("\n✅ Cleanup script completed successfully")
        sys.exit(0)
    else:
        print("\n❌ Cleanup script failed")
        sys.exit(1)

