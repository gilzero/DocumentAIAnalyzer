"""Add processing columns to document table

Revision ID: 2a2b3c4d5e6f
Revises: 1a2b3c4d5e6f
Create Date: 2024-12-29 09:38:46.970535

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '2a2b3c4d5e6f'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None

def upgrade():
    # Add processing_attempts and processing_method columns
    op.add_column('document', sa.Column('processing_attempts', sa.Integer, default=1))
    op.add_column('document', sa.Column('processing_method', sa.String(50)))

def downgrade():
    # Remove the columns
    op.drop_column('document', 'processing_method')
    op.drop_column('document', 'processing_attempts')
