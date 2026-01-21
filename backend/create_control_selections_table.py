"""
Script to create control_selections table if it doesn't exist
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.db import engine, Base, SessionLocal
from app.models.control_selection import ControlSelection
from app.models.company import Company
from app.models.framework import Framework

def check_table_exists():
    """Check if control_selections table exists"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    return 'control_selections' in existing_tables

def check_dependencies():
    """Check if required tables (companies, frameworks) exist"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    companies_exists = 'companies' in existing_tables
    frameworks_exists = 'frameworks' in existing_tables
    
    print(f"📋 Dependencies check:")
    print(f"   - companies table: {'✅' if companies_exists else '❌'}")
    print(f"   - frameworks table: {'✅' if frameworks_exists else '❌'}")
    
    return companies_exists and frameworks_exists

def create_table_sql():
    """Create table using SQL (more reliable)"""
    db = SessionLocal()
    try:
        # Check if table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'control_selections'
            )
        """))
        table_exists = result.scalar()
        
        if table_exists:
            print("✅ Table 'control_selections' already exists")
            return True
        
        # Check dependencies
        if not check_dependencies():
            print("❌ Required tables (companies, frameworks) do not exist!")
            print("   Please create them first before creating control_selections table.")
            return False
        
        print("📦 Creating 'control_selections' table...")
        
        # Create table with proper structure
        db.execute(text("""
            CREATE TABLE control_selections (
                id SERIAL PRIMARY KEY,
                company_id INTEGER NOT NULL,
                framework_id INTEGER NOT NULL,
                selected_control_ids JSONB NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                
                CONSTRAINT fk_control_selections_company 
                    FOREIGN KEY (company_id) 
                    REFERENCES companies(id) 
                    ON DELETE CASCADE,
                
                CONSTRAINT fk_control_selections_framework 
                    FOREIGN KEY (framework_id) 
                    REFERENCES frameworks(id) 
                    ON DELETE CASCADE
            )
        """))
        
        # Create indexes
        print("📦 Creating indexes...")
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_control_selections_id 
                ON control_selections(id)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_control_selections_company_framework 
                ON control_selections(company_id, framework_id)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_control_selections_control_ids 
                ON control_selections USING GIN (selected_control_ids)
        """))
        
        db.commit()
        print("✅ Table 'control_selections' created successfully!")
        print("✅ Indexes created successfully!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating table: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def verify_table():
    """Verify the table structure"""
    db = SessionLocal()
    try:
        # Check columns
        result = db.execute(text("""
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = 'control_selections'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        if columns:
            print("\n📊 Table structure:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]} ({'nullable' if col[2] == 'YES' else 'not null'})")
        else:
            print("❌ Table structure not found")
            return False
        
        # Check foreign keys
        result = db.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'control_selections'
                AND tc.constraint_type = 'FOREIGN KEY'
        """))
        
        fks = result.fetchall()
        if fks:
            print("\n🔗 Foreign key constraints:")
            for fk in fks:
                print(f"   - {fk[1]} -> {fk[2]}.id")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying table: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """Main function"""
    print("=" * 60)
    print("CONTROL SELECTIONS TABLE CREATION SCRIPT")
    print("=" * 60)
    print()
    
    # Check if table already exists
    if check_table_exists():
        print("✅ Table 'control_selections' already exists")
        print("\n📊 Verifying table structure...")
        verify_table()
        return
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot create table - dependencies missing!")
        return
    
    # Create table
    print()
    success = create_table_sql()
    
    if success:
        print("\n📊 Verifying table structure...")
        verify_table()
        print("\n✅ Setup complete!")
    else:
        print("\n❌ Setup failed!")

if __name__ == "__main__":
    main()
