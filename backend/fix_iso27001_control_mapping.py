"""
PART 1 & PART 2: Fix ISO 27001 Control Groups and Control Mappings

This script:
1. Ensures ISO 27001 control groups (A.5, A.6, A.7, A.8) exist and are correctly linked
2. Fixes control mappings - ensures all ISO 27001 controls have correct control_group_id
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.db import SessionLocal
from app.models import Framework, ControlGroup, Control

def fix_control_groups():
    """PART 1: Ensure ISO 27001 control groups exist and are correctly linked"""
    db = SessionLocal()
    try:
        # Find ISO 27001 framework
        framework = db.query(Framework).filter(
            Framework.name.ilike('%ISO 27001%')
        ).first()
        
        if not framework:
            print("❌ ISO 27001 framework not found in database!")
            print("   Please seed the framework first using: POST /api/v1/frameworks/seed/iso27001")
            return False
        
        print(f"✅ Found framework: {framework.name} (ID: {framework.id})")
        
        # Required control groups
        required_groups = [
            {"code": "A.5", "name": "Organizational Controls", "description": "Organizational controls for information security"},
            {"code": "A.6", "name": "People Controls", "description": "People controls for information security"},
            {"code": "A.7", "name": "Physical Controls", "description": "Physical and environmental controls"},
            {"code": "A.8", "name": "Technological Controls", "description": "Technological controls for information security"}
        ]
        
        created_count = 0
        updated_count = 0
        
        for group_data in required_groups:
            # Check if group exists
            existing_group = db.query(ControlGroup).filter(
                ControlGroup.code == group_data["code"],
                ControlGroup.framework_id == framework.id
            ).first()
            
            if existing_group:
                # Check if framework_id is correct
                if existing_group.framework_id != framework.id:
                    print(f"⚠️  Fixing {group_data['code']} - Wrong framework_id: {existing_group.framework_id} -> {framework.id}")
                    existing_group.framework_id = framework.id
                    updated_count += 1
                else:
                    print(f"✅ {group_data['code']} - {group_data['name']} exists and is correctly linked")
            else:
                # Create missing group
                print(f"📦 Creating {group_data['code']} - {group_data['name']}")
                new_group = ControlGroup(
                    code=group_data["code"],
                    name=group_data["name"],
                    description=group_data["description"],
                    framework_id=framework.id,
                    is_active=True
                )
                db.add(new_group)
                created_count += 1
        
        db.commit()
        print(f"\n✅ Control groups: {created_count} created, {updated_count} updated")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing control groups: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def fix_control_mappings():
    """PART 2: Fix control mappings - ensure all ISO 27001 controls have correct control_group_id"""
    db = SessionLocal()
    try:
        # Find ISO 27001 framework
        framework = db.query(Framework).filter(
            Framework.name.ilike('%ISO 27001%')
        ).first()
        
        if not framework:
            print("❌ ISO 27001 framework not found!")
            return False
        
        # Get control groups for this framework
        control_groups = db.query(ControlGroup).filter(
            ControlGroup.framework_id == framework.id,
            ControlGroup.code.in_(["A.5", "A.6", "A.7", "A.8"]),
            ControlGroup.is_active == True
        ).all()
        
        if not control_groups:
            print("❌ Control groups not found! Run fix_control_groups() first.")
            return False
        
        # Create mapping: code prefix -> control_group_id
        group_mapping = {}
        for cg in control_groups:
            group_mapping[cg.code] = cg.id
            print(f"📋 Group mapping: {cg.code} -> ID {cg.id}")
        
        # Find all controls that should belong to ISO 27001
        # Controls with codes starting with A.5, A.6, A.7, A.8
        all_controls = db.query(Control).filter(
            Control.is_active == True
        ).all()
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        print(f"\n🔍 Checking {len(all_controls)} controls...")
        
        for control in all_controls:
            # Check if control code matches ISO 27001 pattern
            if not control.code:
                continue
            
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
                # Not an ISO 27001 control, skip
                continue
            
            # Check if control_group_id is correct
            correct_group_id = group_mapping.get(code_prefix)
            
            if not correct_group_id:
                print(f"⚠️  Control {control.code} ({control.id}): No group found for prefix {code_prefix}")
                error_count += 1
                continue
            
            # Check current control_group
            current_group = db.query(ControlGroup).filter(
                ControlGroup.id == control.control_group_id
            ).first()
            
            if not current_group:
                # control_group_id is invalid or NULL
                print(f"🔧 Fixing {control.code} ({control.id}): NULL/invalid control_group_id -> {code_prefix} (ID: {correct_group_id})")
                control.control_group_id = correct_group_id
                fixed_count += 1
            elif current_group.framework_id != framework.id:
                # Control belongs to wrong framework
                print(f"🔧 Fixing {control.code} ({control.id}): Wrong framework (group framework_id={current_group.framework_id}) -> {code_prefix} (ID: {correct_group_id})")
                control.control_group_id = correct_group_id
                fixed_count += 1
            elif control.control_group_id != correct_group_id:
                # Control in wrong group (but same framework)
                print(f"🔧 Fixing {control.code} ({control.id}): Wrong group (current: {current_group.code}) -> {code_prefix} (ID: {correct_group_id})")
                control.control_group_id = correct_group_id
                fixed_count += 1
            else:
                # Control is correctly mapped
                skipped_count += 1
        
        db.commit()
        print(f"\n✅ Control mappings: {fixed_count} fixed, {skipped_count} already correct, {error_count} errors")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error fixing control mappings: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def verify_fix():
    """Verify that the fix worked"""
    db = SessionLocal()
    try:
        framework = db.query(Framework).filter(
            Framework.name.ilike('%ISO 27001%')
        ).first()
        
        if not framework:
            print("❌ Framework not found")
            return False
        
        # Check control groups
        groups = db.query(ControlGroup).filter(
            ControlGroup.framework_id == framework.id,
            ControlGroup.code.in_(["A.5", "A.6", "A.7", "A.8"])
        ).all()
        
        print(f"\n📊 Verification:")
        print(f"   Framework: {framework.name} (ID: {framework.id})")
        print(f"   Control groups: {len(groups)}")
        
        for group in groups:
            # Count controls in each group
            control_count = db.query(Control).filter(
                Control.control_group_id == group.id,
                Control.is_active == True
            ).count()
            print(f"   - {group.code} ({group.name}): {control_count} controls")
        
        # Check for controls with NULL or wrong control_group_id
        all_controls = db.query(Control).filter(
            Control.is_active == True,
            Control.code.like('A.%')
        ).all()
        
        issues = 0
        for control in all_controls:
            if not control.control_group_id:
                print(f"   ⚠️  Control {control.code} ({control.id}): NULL control_group_id")
                issues += 1
            else:
                cg = db.query(ControlGroup).filter(ControlGroup.id == control.control_group_id).first()
                if cg and cg.framework_id != framework.id:
                    print(f"   ⚠️  Control {control.code} ({control.id}): Wrong framework (group framework_id={cg.framework_id})")
                    issues += 1
        
        if issues == 0:
            print(f"   ✅ No mapping issues found!")
        else:
            print(f"   ⚠️  {issues} mapping issues found")
        
        return issues == 0
        
    except Exception as e:
        print(f"❌ Error verifying: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Main function"""
    print("=" * 60)
    print("ISO 27001 CONTROL MAPPING FIX")
    print("=" * 60)
    print()
    
    print("PART 1: Fixing control groups...")
    if not fix_control_groups():
        print("\n❌ Failed to fix control groups. Exiting.")
        return
    
    print("\nPART 2: Fixing control mappings...")
    if not fix_control_mappings():
        print("\n❌ Failed to fix control mappings. Exiting.")
        return
    
    print("\nPART 3: Verifying fix...")
    verify_fix()
    
    print("\n✅ Fix complete!")

if __name__ == "__main__":
    main()

