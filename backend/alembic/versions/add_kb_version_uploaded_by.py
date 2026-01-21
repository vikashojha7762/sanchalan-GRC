"""add_kb_version_uploaded_by

Revision ID: add_kb_fields_001
Revises: 1514387c3691
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_kb_fields_001'
down_revision = '1514387c3691'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add version column (nullable)
    op.add_column('knowledge_base_documents', 
        sa.Column('version', sa.String(length=50), nullable=True)
    )
    
    # Add uploaded_by column (nullable, foreign key to users)
    op.add_column('knowledge_base_documents',
        sa.Column('uploaded_by', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_kb_documents_uploaded_by',
        'knowledge_base_documents',
        'users',
        ['uploaded_by'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_kb_documents_uploaded_by', 'knowledge_base_documents', type_='foreignkey')
    
    # Remove columns
    op.drop_column('knowledge_base_documents', 'uploaded_by')
    op.drop_column('knowledge_base_documents', 'version')

