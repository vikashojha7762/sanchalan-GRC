import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path

# Ensure .env loads from backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

print("🔍 Loading .env from:", ENV_PATH)
load_dotenv(ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")
print("🔍 DATABASE_URL Loaded:", DATABASE_URL)

# Ensure DATABASE_URL exists
if not DATABASE_URL or DATABASE_URL.strip() == "":
    raise ValueError("❌ DATABASE_URL is missing or empty in .env. Please set it correctly.")

# Create Engine
engine = create_engine(DATABASE_URL, echo=True)

# Session Local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base for models
Base = declarative_base()

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Safety Warning
if not DATABASE_URL.startswith("postgresql"):
    print("⚠️ WARNING: DATABASE_URL format seems invalid.")

# OPTIONAL temporary debug: Create tables if they don't exist
# Remove this after confirming tables exist via migration
Base.metadata.create_all(bind=engine)