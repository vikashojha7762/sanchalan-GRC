from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class GapSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GapStatus(str, enum.Enum):
    IDENTIFIED = "identified"
    IN_REMEDIATION = "in_remediation"
    REMEDIATED = "remediated"
    VERIFIED = "verified"
    CLOSED = "closed"


class Gap(Base):
    __tablename__ = "gaps"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    severity = Column(Enum(GapSeverity), default=GapSeverity.MEDIUM, nullable=False)
    status = Column(Enum(GapStatus), default=GapStatus.IDENTIFIED, nullable=False)
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="SET NULL"), nullable=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="SET NULL"), nullable=True, index=True)
    policy_id = Column(Integer, ForeignKey("policies.id", ondelete="SET NULL"), nullable=True, index=True)
    identified_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    risk_score = Column(Float, nullable=True)
    impact = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    identified_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    target_remediation_date = Column(DateTime(timezone=True), nullable=True)
    actual_remediation_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="gaps")
    control = relationship("Control", back_populates="gaps")
    policy = relationship("Policy", back_populates="gaps")
    identified_by = relationship("User", foreign_keys=[identified_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    remediations = relationship("Remediation", back_populates="gap", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="gap", cascade="all, delete-orphan")
