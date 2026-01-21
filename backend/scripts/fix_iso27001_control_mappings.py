"""
PART 1 — FIX DATABASE MAPPING (ROOT CAUSE)

One-time repair script to fix ISO 27001 control mappings.
Repairs control_group_id assignments for ISO 27001 controls.
"""
import sys
from pathlib import Path

# Add parent directories to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.db import SessionLocal
from app.models import Framework, ControlGroup, Control

def fix_iso27001_control_mappings():
    """
    Fix ISO 27001 control mappings.
    Reassigns controls to correct control groups if they're mis-mapped.
    """
    db = SessionLocal()
    try:
        print("=" * 60)
        print("ISO 27001 CONTROL MAPPING REPAIR SCRIPT")
        print("=" * 60)
        print()
        
        # Step 1: Fetch ISO 27001 framework
        framework = db.query(Framework).filter(
            Framework.name.ilike('%27001%')
        ).first()
        
        if not framework:
            print("❌ ISO 27001 framework not found!")
            print("   Please ensure the framework is seeded first.")
            return False
        
        print(f"✅ Found framework: {framework.name} (ID: {framework.id})")
        print()
        
        # Step 2: Fetch its 4 control groups (A.5, A.6, A.7, A.8)
        control_groups = db.query(ControlGroup).filter(
            ControlGroup.framework_id == framework.id,
            ControlGroup.code.in_(["A.5", "A.6", "A.7", "A.8"]),
            ControlGroup.is_active == True
        ).all()
        
        if len(control_groups) != 4:
            print(f"⚠️  Expected 4 control groups, found {len(control_groups)}")
            print("   Groups found:")
            for cg in control_groups:
                print(f"     - {cg.code}: {cg.name} (ID: {cg.id})")
        
        # Create mapping: code prefix -> control_group_id
        group_mapping = {}
        for cg in control_groups:
            group_mapping[cg.code] = cg.id
            print(f"✅ Control group: {cg.code} - {cg.name} (ID: {cg.id})")
        
        print()
        
        # Step 3: Find all controls that should belong to ISO 27001
        # Get all controls with codes starting with A.5, A.6, A.7, A.8
        all_controls = db.query(Control).filter(
            Control.is_active == True,
            Control.code.like('A.%')
        ).all()
        
        print(f"🔍 Checking {len(all_controls)} controls with A.* codes...")
        print()
        
        fixed_count = 0
        already_correct = 0
        skipped_count = 0
        
        for control in all_controls:
            if not control.code:
                skipped_count += 1
                continue
            
            # Determine which group this control should belong to
            code_prefix = None
            if control.code.startswith("A.5"):
                code_prefix = "A.5"
            elif control.code.startswith("A.6"):
                code_prefix = "A.6"
            elif control.code.startswith("A.7"):
                code_prefix = "A.7"
            elif control.code.startswith("A.8"):
                code_prefix = "A.8"
            else:
                # Not A.5-A.8, skip
                skipped_count += 1
                continue
            
            # Get the correct control_group_id
            correct_group_id = group_mapping.get(code_prefix)
            if not correct_group_id:
                print(f"⚠️  Control {control.code} ({control.id}): No group found for prefix {code_prefix}")
                skipped_count += 1
                continue
            
            # Check current control_group_id
            needs_fix = False
            fix_reason = ""
            
            if not control.control_group_id:
                # NULL control_group_id
                needs_fix = True
                fix_reason = "NULL control_group_id"
            else:
                # Check if current group belongs to correct framework
                current_group = db.query(ControlGroup).filter(
                    ControlGroup.id == control.control_group_id
                ).first()
                
                if not current_group:
                    # control_group_id points to non-existent group
                    needs_fix = True
                    fix_reason = f"Invalid control_group_id ({control.control_group_id})"
                elif current_group.framework_id != framework.id:
                    # Group belongs to different framework
                    needs_fix = True
                    fix_reason = f"Wrong framework (group framework_id={current_group.framework_id}, expected {framework.id})"
                elif control.control_group_id != correct_group_id:
                    # Wrong group (but same framework)
                    needs_fix = True
                    fix_reason = f"Wrong group (current: {current_group.code}, expected: {code_prefix})"
            
            if needs_fix:
                print(f"🔧 Fixing {control.code} ({control.id}): {fix_reason} → {code_prefix} (ID: {correct_group_id})")
                control.control_group_id = correct_group_id
                fixed_count += 1
            else:
                already_correct += 1
        
        # Step 4: Commit changes safely
        if fixed_count > 0:
            print()
            print(f"💾 Committing {fixed_count} fixes to database...")
            db.commit()
            print(f"✅ Successfully committed changes")
        else:
            print()
            print("✅ No fixes needed - all controls are correctly mapped")
        
        # Step 5: Print summary
        print()
        print("=" * 60)
        print("REPAIR SUMMARY")
        print("=" * 60)
        print(f"✅ Framework: {framework.name} (ID: {framework.id})")
        print(f"✅ Control groups: {len(control_groups)}")
        print(f"🔧 Controls fixed: {fixed_count}")
        print(f"✅ Controls already correct: {already_correct}")
        print(f"⏭️  Controls skipped: {skipped_count}")
        print(f"📊 Total controls checked: {len(all_controls)}")
        print()
        
        if fixed_count > 0:
            print("✅ Repair completed successfully!")
        else:
            print("✅ No repairs needed - mappings are correct")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during repair: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = fix_iso27001_control_mappings()
    sys.exit(0 if success else 1)

