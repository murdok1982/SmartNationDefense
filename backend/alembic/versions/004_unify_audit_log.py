"""Alembic migration: unificación de auditoría en ``audit_log`` (TASK-016).

Añade a la tabla canónica ``audit_log`` las columnas del antiguo trail de
seguridad (``audit_logs``) para eliminar las tablas duplicadas
``audit_logs`` y ``audit_chain``.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '004_unify_audit_log'
down_revision = '003_intel_products'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('audit_log', sa.Column('user_id', sa.String(length=128), nullable=True))
    op.add_column('audit_log', sa.Column('username', sa.String(length=64), nullable=True, server_default=''))
    op.add_column('audit_log', sa.Column('details', sa.JSON(), nullable=True))
    op.add_column('audit_log', sa.Column('ip_address', sa.String(length=64), nullable=True, server_default=''))
    op.add_column('audit_log', sa.Column('user_agent', sa.Text(), nullable=True, server_default=''))
    op.add_column('audit_log', sa.Column('request_id', sa.String(length=64), nullable=True, server_default=''))
    op.add_column('audit_log', sa.Column('success', sa.Boolean(), nullable=True, server_default=sa.true()))
    op.add_column('audit_log', sa.Column('error_message', sa.Text(), nullable=True, server_default=''))
    op.create_index('ix_audit_log_user_id', 'audit_log', ['user_id'])

    # Migración de datos desde las tablas duplicadas (si existen).
    op.execute("""
        DO $$
        BEGIN
            IF to_regclass('audit_logs') IS NOT NULL THEN
                INSERT INTO audit_log (ts, actor, action, resource_type, resource_id, context,
                                       prev_hash, row_hash, user_id, username, details,
                                       ip_address, user_agent, request_id, success, error_message)
                SELECT timestamp, user_id, action, resource_type, resource_id, details,
                       repeat('0', 64), '', user_id, username, details,
                       ip_address, user_agent, request_id, success, error_message
                FROM audit_logs
                WHERE NOT EXISTS (
                    SELECT 1 FROM audit_log a
                    WHERE a.actor = audit_logs.user_id
                      AND a.action = audit_logs.action
                      AND a.ts = audit_logs.timestamp
                );
            END IF;
        END
        $$;
    """)


def downgrade():
    op.drop_index('ix_audit_log_user_id', table_name='audit_log')
    op.drop_column('audit_log', 'error_message')
    op.drop_column('audit_log', 'success')
    op.drop_column('audit_log', 'request_id')
    op.drop_column('audit_log', 'user_agent')
    op.drop_column('audit_log', 'ip_address')
    op.drop_column('audit_log', 'details')
    op.drop_column('audit_log', 'username')
    op.drop_column('audit_log', 'user_id')
