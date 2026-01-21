"""
Test script to verify control validation is working correctly
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import SessionLocal
from app.models import Framework, ControlGroup, Control

def test_control_validation():
    """Test if controls can be validated correctly"""
    db = SessionLocal()
    try:
        # Find ISO 27001 framework
        framework = db.query(Framework).filter(
            Framework.name.ilike('%ISO 27001%')
        ).first()
        
        if not framework:
            print("❌ ISO 27001 framework not found!")
            return False
        
        print(f"✅ Found framework: {framework.name} (ID: {framework.id})")
        
        # Get control groups
        control_groups = db.query(ControlGroup).filter(
            ControlGroup.framework_id == framework.id,
            ControlGroup.code.in_(["A.5", "A.6", "A.7", "A.8"]),
            ControlGroup.is_active == True
        ).all()
        
        print(f"✅ Found {len(control_groups)} control groups:")
        for cg in control_groups:
            print(f"   - {cg.code}: {cg.name} (ID: {cg.id})")
        
        # Get valid control IDs
        valid_controls = db.query(Control.id).join(
            ControlGroup, Control.control_group_id == ControlGroup.id
        ).filter(
            ControlGroup.framework_id == framework.id,
            Control.is_active == True
        ).all()
        
        valid_control_ids = set(cid for (cid,) in valid_controls)
        
        print(f"\n✅ Found {len(valid_control_ids)} valid control IDs for framework {framework.id}")
        print(f"   Sample IDs: {list(valid_control_ids)[:10]}")
        
        # Check for controls with A.6.1 (Screening)
        screening_controls = db.query(Control).join(
            ControlGroup, Control.control_group_id == ControlGroup.id
        ).filter(
            Control.code == 'A.6.1',
            ControlGroup.framework_id == framework.id,
            Control.is_active == True
        ).all()
        
        if screening_controls:
            print(f"\n✅ Found A.6.1 Screening control:")
            for ctrl in screening_controls:
                print(f"   - ID: {ctrl.id}, Code: {ctrl.code}, Name: {ctrl.name}")
                print(f"     Group: {ctrl.control_group.code} (ID: {ctrl.control_group.id})")
                print(f"     Framework ID: {ctrl.control_group.framework_id}")
        else:
            print(f"\n⚠️  A.6.1 Screening control not found!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("CONTROL VALIDATION TEST")
    print("=" * 60)
    print()
    test_control_validation()

