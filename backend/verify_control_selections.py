"""
Script to verify and optimize control_selections table
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text, inspect
from app.db import SessionLocal

def check_indexes():
    """Check if all recommended indexes exist"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT 
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = 'control_selections'
            ORDER BY indexname
        """))
        
        indexes = result.fetchall()
        print("📊 Existing indexes:")
        if indexes:
            for idx in indexes:
                print(f"   ✅ {idx[0]}")
        else:
            print("   ⚠️ No indexes found")
        
        # Check for recommended indexes
        index_names = [idx[0] for idx in indexes]
        
        recommended_indexes = {
            'ix_control_selections_company_framework': """
                CREATE INDEX IF NOT EXISTS ix_control_selections_company_framework 
                ON control_selections(company_id, framework_id)
            """,
            'ix_control_selections_control_ids': """
                CREATE INDEX IF NOT EXISTS ix_control_selections_control_ids 
                ON control_selections USING GIN (selected_control_ids)
            """
        }
        
        print("\n🔧 Checking recommended indexes...")
        for idx_name, idx_sql in recommended_indexes.items():
            if idx_name not in index_names:
                print(f"   📦 Creating missing index: {idx_name}")
                try:
                    db.execute(text(idx_sql))
                    db.commit()
                    print(f"   ✅ Created: {idx_name}")
                except Exception as e:
                    print(f"   ⚠️ Could not create {idx_name}: {str(e)}")
            else:
                print(f"   ✅ Index exists: {idx_name}")
        
    except Exception as e:
        print(f"❌ Error checking indexes: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def check_data():
    """Check if there's any data in the table"""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT company_id) as unique_companies,
                COUNT(DISTINCT framework_id) as unique_frameworks
            FROM control_selections
        """))
        
        stats = result.fetchone()
        print("\n📊 Table statistics:")
        print(f"   - Total records: {stats[0]}")
        print(f"   - Unique companies: {stats[1]}")
        print(f"   - Unique frameworks: {stats[2]}")
        
        if stats[0] > 0:
            # Show sample data
            result = db.execute(text("""
                SELECT 
                    cs.id,
                    c.name AS company_name,
                    f.name AS framework_name,
                    cs.selected_control_ids,
                    jsonb_array_length(cs.selected_control_ids::jsonb) AS control_count,
                    cs.created_at
                FROM control_selections cs
                LEFT JOIN companies c ON cs.company_id = c.id
                LEFT JOIN frameworks f ON cs.framework_id = f.id
                ORDER BY cs.created_at DESC
                LIMIT 5
            """))
            
            samples = result.fetchall()
            print("\n📋 Sample records (latest 5):")
            for sample in samples:
                print(f"   - ID {sample[0]}: {sample[1]} | {sample[2]} | {sample[4]} controls | {sample[5]}")
        
    except Exception as e:
        print(f"❌ Error checking data: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def main():
    """Main function"""
    print("=" * 60)
    print("CONTROL SELECTIONS TABLE VERIFICATION")
    print("=" * 60)
    print()
    
    check_indexes()
    check_data()
    
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()

