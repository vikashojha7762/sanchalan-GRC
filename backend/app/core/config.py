from typing import List
import os
from dotenv import load_dotenv
from pathlib import Path

# Ensure .env loads from backend/.env
# config.py is at: backend/app/core/config.py
# So we need to go up 3 levels: core -> app -> backend
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from backend/.env
print(f"🔍 Loading .env from: {ENV_PATH}")
load_dotenv(ENV_PATH, override=True)  # Override=True to ensure fresh values


class Settings:
    """
    Application settings loaded from environment variables.
    """
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change_this_secret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()

# Debug: Print Pinecone config on load
print(f"🔍 Pinecone Index Name from .env: {settings.PINECONE_INDEX_NAME}")
