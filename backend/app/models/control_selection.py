from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from app.db import Base


class ControlSelection(Base):
    __tablename__ = "control_selections"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="CASCADE"))
    selected_control_ids = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

