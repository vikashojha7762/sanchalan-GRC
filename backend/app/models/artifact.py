from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class ArtifactType(str, enum.Enum):
    DOCUMENT = "document"
    EVIDENCE = "evidence"
    REPORT = "report"
    SCREENSHOT = "screenshot"
    CERTIFICATE = "certificate"
    OTHER = "other"


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    artifact_type = Column(Enum(ArtifactType), default=ArtifactType.DOCUMENT, nullable=False)
    file_path = Column(String(500), nullable=True)
    file_url = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), nullable=True, index=True)
    gap_id = Column(Integer, ForeignKey("gaps.id", ondelete="SET NULL"), nullable=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    policy = relationship("Policy", back_populates="artifacts")
    gap = relationship("Gap", back_populates="artifacts")
    control = relationship("Control", back_populates="artifacts")
    uploaded_by = relationship("User")
