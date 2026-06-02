"""add metadata_ml_configs table

Revision ID: 002_add_ml_configs
Revises: 001_add_admin_dashboard
Create Date: 2025-11-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_add_ml_configs'
down_revision = 'add_admin_dashboard_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metadata_ml_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('group_by', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('methods', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('method_params', postgresql.JSONB(), nullable=False),
        sa.Column('retrain_schedule', sa.String(), nullable=True),
        sa.Column('auto_alert', sa.Boolean(), nullable=True),
        sa.Column('alert_severity', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['metric_name'], ['metadata_metrics.metric_name'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_ml_configs_metric', 'metadata_ml_configs', ['metric_name'])
    op.create_index('ix_ml_configs_active', 'metadata_ml_configs', ['is_active'])


def downgrade():
    op.drop_table('metadata_ml_configs')