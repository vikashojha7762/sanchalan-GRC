from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.db import engine
from app.core.config import settings

app = FastAPI(
    title="SANCHALAN AI GRC Platform",
    description="AI-powered Governance, Risk, and Compliance platform",
    version="1.0.0"
)

# Mount static file directories for serving uploaded files
BASE_DIR = Path(__file__).resolve().parent.parent
uploads_dir = BASE_DIR / "uploads"
if uploads_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "message": "SANCHALAN AI GRC Platform is running"}


# API routers
from app.api.v1 import auth, onboarding, frameworks, policies, gaps, dashboard, chat, gap_analysis, reports, knowledge_base, artifacts

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(frameworks.router, prefix="/api/v1/frameworks", tags=["frameworks"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])
app.include_router(gaps.router, prefix="/api/v1/gaps", tags=["gaps"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(gap_analysis.router, prefix="/api/v1/gap-analysis", tags=["gap-analysis"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(knowledge_base.router, prefix="/api/v1/knowledge-base", tags=["Knowledge Base"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["artifacts"])
