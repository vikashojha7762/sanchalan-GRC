from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Framework(Base):
    __tablename__ = "frameworks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)  # e.g., "Security", "Compliance", "Risk"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    control_groups = relationship("ControlGroup", back_populates="framework", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="framework", cascade="all, delete-orphan")
    gaps = relationship("Gap", back_populates="framework", cascade="all, delete-orphan")
    knowledge_base_documents = relationship("KnowledgeBaseDocument", back_populates="framework", cascade="all, delete-orphan")
