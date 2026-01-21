from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum, TypeDecorator
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class PolicyStatus(str, enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"  # Added for proper rejection tracking
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PolicyStatusType(TypeDecorator):
    """Custom type to handle case-insensitive enum conversion.
    
    Database enum has mixed case: 'DRAFT', 'UNDER_REVIEW', etc. (uppercase)
    but 'rejected' (lowercase). This type handles the conversion.
    """
    impl = String
    cache_ok = True
    
    # Mapping from Python enum value (lowercase) to database enum value
    DB_VALUE_MAP = {
        'draft': 'DRAFT',
        'under_review': 'UNDER_REVIEW',
        'approved': 'APPROVED',
        'rejected': 'rejected',  # Database has lowercase for this one
        'published': 'PUBLISHED',
        'archived': 'ARCHIVED'
    }
    
    # Reverse mapping from database value to Python enum value
    PYTHON_VALUE_MAP = {v: k for k, v in DB_VALUE_MAP.items()}
    
    def __init__(self):
        super().__init__(length=50)
    
    def process_bind_param(self, value, dialect):
        """Convert Python enum to database value."""
        if value is None:
            return None
        if isinstance(value, PolicyStatus):
            # Convert Python enum value to database enum value
            return self.DB_VALUE_MAP.get(value.value, value.value.upper())
        if isinstance(value, str):
            value_lower = value.lower()
            return self.DB_VALUE_MAP.get(value_lower, value.upper())
        return str(value).upper()
    
    def process_result_value(self, value, dialect):
        """Convert database value to Python enum."""
        if value is None:
            return None
        # Convert database value to Python enum value
        if isinstance(value, str):
            python_value = self.PYTHON_VALUE_MAP.get(value, value.lower())
            try:
                return PolicyStatus(python_value)
            except ValueError:
                # Fallback: try direct match
                for status in PolicyStatus:
                    if status.value.lower() == value.lower():
                        return status
                raise ValueError(f"Invalid PolicyStatus value: {value}")
        return PolicyStatus(str(value).lower())


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    policy_number = Column(String(100), nullable=True, unique=True, index=True)
    version = Column(String(50), nullable=True)
    status = Column(PolicyStatusType(), default=PolicyStatus.DRAFT, nullable=False)
    framework_id = Column(Integer, ForeignKey("frameworks.id", ondelete="SET NULL"), nullable=True, index=True)
    control_id = Column(Integer, ForeignKey("controls.id", ondelete="SET NULL"), nullable=True, index=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    framework = relationship("Framework", back_populates="policies")
    control = relationship("Control", back_populates="policies")
    owner = relationship("User")
    gaps = relationship("Gap", back_populates="policy", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="policy", cascade="all, delete-orphan")
