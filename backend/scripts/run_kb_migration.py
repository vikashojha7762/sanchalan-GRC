"""
Quick script to run the knowledge base migration.
Run this if you get "column does not exist" errors.
"""
import subprocess
import sys
import os
from pathlib import Path

# Change to backend directory
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

print("Running Alembic migration to add version and uploaded_by columns...")
print("=" * 60)

try:
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        check=True
    )
    print(result.stdout)
    print("\n✅ Migration completed successfully!")
    print("You can now upload knowledge base documents.")
except subprocess.CalledProcessError as e:
    print("❌ Migration failed:")
    print(e.stderr)
    print("\nTry running manually:")
    print("  cd backend")
    print("  alembic upgrade head")
    sys.exit(1)
except FileNotFoundError:
    print("❌ Alembic not found. Please run manually:")
    print("  cd backend")
    print("  alembic upgrade head")
    sys.exit(1)

