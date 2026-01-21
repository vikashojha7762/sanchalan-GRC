"""
Knowledge Base Document Model
Stores authoritative compliance documents (ISO 27001, NIST, etc.)
"""
import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class KnowledgeSourceType(str, enum.Enum):
    """Source type for knowledge base documents."""
    ISO = "ISO"
    NIST = "NIST"
    CUSTOM = "CUSTOM"
    UI = "UI"  # Uploaded via UI


class KnowledgeBaseDocument(Base):
    """Knowledge Base Document model for storing authoritative compliance documents."""
    __tablename__ = "knowledge_base_documents"

    id = Column(Integer, primary_key=True, index=True)
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    version = Column(String(50), nullable=True)  # Optional version field
    source_type = Column(Enum(KnowledgeSourceType), default=KnowledgeSourceType.UI, nullable=False)
    raw_text = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)  # Path to stored file
    is_active = Column(Boolean, default=True, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # User who uploaded
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="knowledge_base_documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

