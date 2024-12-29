"""Add doc_metadata column to document table

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-12-29 09:31:46.970535

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add doc_metadata column to document table
    op.add_column('document', sa.Column('doc_metadata', JSON))

def downgrade():
    # Remove doc_metadata column from document table
    op.drop_column('document', 'doc_metadata')
