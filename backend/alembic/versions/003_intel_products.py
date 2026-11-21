"""Alembic migration: intelligence_products (legacy 002_intel_products.sql).

Convierte el SQL legacy `002_intel_products.sql.legacy` (archivado en
`backend/migrations/archived/`) a una migración atómica con `op.create_table`
+ `op.create_index`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers
revision = '003_intel_products'
down_revision = '002_audit_chain'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'intelligence_products',
        sa.Column('id', sa.Text(), nullable=False),
        sa.Column('product_type', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('classification_level', sa.Text(), nullable=False,
                  server_default='CONFIDENTIAL'),
        sa.Column('source_data', JSONB(),
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('created_by', sa.Text(), nullable=False,
                  server_default='SYSTEM'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_intel_products_type', 'intelligence_products',
                    ['product_type'])
    op.create_index('idx_intel_products_created', 'intelligence_products',
                    ['created_at'],
                    postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_intel_products_classification', 'intelligence_products',
                    ['classification_level'])


def downgrade():
    op.drop_index('idx_intel_products_classification',
                  table_name='intelligence_products')
    op.drop_index('idx_intel_products_created',
                  table_name='intelligence_products')
    op.drop_index('idx_intel_products_type',
                  table_name='intelligence_products')
    op.drop_table('intelligence_products')
