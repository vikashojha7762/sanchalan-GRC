"""
Script to check if knowledge_base_documents table has required columns.
"""
from app.db import SessionLocal
from sqlalchemy import inspect

db = SessionLocal()

try:
    # Check if table exists and get columns
    inspector = inspect(db.bind)
    if 'knowledge_base_documents' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('knowledge_base_documents')]
        print("Knowledge Base Documents Table Columns:")
        print("=" * 50)
        for col in columns:
            print(f"  - {col}")
        
        # Check for required columns
        required = ['version', 'uploaded_by']
        missing = [col for col in required if col not in columns]
        
        if missing:
            print(f"\n⚠️  Missing columns: {missing}")
            print("Run migration: alembic upgrade head")
        else:
            print("\n✅ All required columns exist")
    else:
        print("❌ Table 'knowledge_base_documents' does not exist")
        print("Run migration: alembic upgrade head")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

