from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class ControlGroup(Base):
    __tablename__ = "control_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String(50), nullable=True, index=True)  # e.g., "AC-1", "AC-2"
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_group_id = Column(Integer, ForeignKey("control_groups.id", ondelete="CASCADE"), nullable=True, index=True)
    order_index = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="control_groups")
    parent_group = relationship("ControlGroup", remote_side=[id], backref="child_groups")
    controls = relationship("Control", back_populates="control_group", cascade="all, delete-orphan")
