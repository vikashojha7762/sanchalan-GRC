"""
Script to check and fix PolicyStatus enum in PostgreSQL database.
Run this to ensure 'rejected' status exists in the database.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_and_fix_enum():
    """Check if 'rejected' exists in PolicyStatus enum, add it if missing."""
    print("🔍 Checking PolicyStatus enum in database...")
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Check current enum values
        result = db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'policystatus'
            )
            ORDER BY enumsortorder;
        """))
        
        enum_values = [row[0] for row in result]
        print(f"📋 Current PolicyStatus enum values: {enum_values}")
        
        if 'rejected' in enum_values:
            print("✅ 'rejected' status already exists in database enum")
            return True
        
        # Add 'rejected' to enum
        print("➕ Adding 'rejected' to PolicyStatus enum...")
        db.execute(text("ALTER TYPE policystatus ADD VALUE IF NOT EXISTS 'rejected'"))
        db.commit()
        print("✅ Successfully added 'rejected' to PolicyStatus enum")
        
        # Verify it was added
        result = db.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (
                SELECT oid 
                FROM pg_type 
                WHERE typname = 'policystatus'
            )
            ORDER BY enumsortorder;
        """))
        
        enum_values = [row[0] for row in result]
        print(f"📋 Updated PolicyStatus enum values: {enum_values}")
        
        if 'rejected' in enum_values:
            print("✅ Verification successful: 'rejected' is now in the enum")
            return True
        else:
            print("⚠️ Warning: 'rejected' was not found after adding it")
            return False
            
    except Exception as e:
        print(f"❌ Error checking/fixing enum: {str(e)}")
        import traceback
        print(traceback.format_exc())
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = check_and_fix_enum()
    sys.exit(0 if success else 1)

