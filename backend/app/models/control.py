from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class ControlStatus(str, enum.Enum):
    NOT_IMPLEMENTED = "not_implemented"
    PARTIALLY_IMPLEMENTED = "partially_implemented"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"


class Control(Base):
    __tablename__ = "controls"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String(50), nullable=True, index=True)  # e.g., "AC-1.1", "AC-1.2"
    control_group_id = Column(Integer, ForeignKey("control_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(ControlStatus), default=ControlStatus.NOT_IMPLEMENTED, nullable=False)
    implementation_notes = Column(Text, nullable=True)
    evidence = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    control_group = relationship("ControlGroup", back_populates="controls")
    policies = relationship("Policy", back_populates="control", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="control", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="control", cascade="all, delete-orphan")
