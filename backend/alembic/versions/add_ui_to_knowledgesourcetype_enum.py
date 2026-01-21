"""add_ui_to_knowledgesourcetype_enum

Revision ID: add_ui_enum_001
Revises: add_kb_fields_001
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_ui_enum_001'
down_revision = 'add_kb_fields_001'  # Update this to match your latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'UI' value to knowledgesourcetype enum
    # PostgreSQL requires creating a new enum type, migrating data, and replacing the old type
    op.execute("""
        ALTER TYPE knowledgesourcetype ADD VALUE IF NOT EXISTS 'UI';
    """)


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values easily
    # This would require recreating the enum type
    # For now, we'll leave it as-is
    pass

