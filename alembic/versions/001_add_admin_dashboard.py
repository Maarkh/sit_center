"""Add admin dashboard tables

Revision ID: add_admin_dashboard_001
Revises: 
Create Date: 2025-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_admin_dashboard_001'
down_revision = None  # Или ID предыдущей миграции
branch_labels = None
depends_on = None


def upgrade():
    """
    Создание таблиц для админ-панели конструктора дашбордов
    """
    
    # 1. Таблица конфигураций дашбордов
    op.create_table(
        'dashboard_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.Column('updated_at', sa.String(), nullable=True),
        sa.Column('layout_config', sa.JSON(), nullable=True),
        sa.Column('theme', sa.String(length=50), default='light'),
        sa.Column('auto_refresh_interval', sa.Integer(), default=30),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # 2. Таблица виджетов
    op.create_table(
        'widget_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dashboard_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('chart_type', sa.String(length=50), nullable=False),
        sa.Column('metric_column', sa.String(length=100), nullable=False),
        sa.Column('position_x', sa.Integer(), default=0),
        sa.Column('position_y', sa.Integer(), default=0),
        sa.Column('width', sa.Integer(), default=6),
        sa.Column('height', sa.Integer(), default=4),
        sa.Column('time_filter', sa.String(length=10), default='1h'),
        sa.Column('aggregation', sa.String(length=50), default='sum'),
        sa.Column('group_by', sa.String(length=100), nullable=True),
        sa.Column('chart_config', sa.JSON(), nullable=True),
        sa.Column('filters', sa.JSON(), nullable=True),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('is_visible', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['dashboard_id'], ['dashboard_configs.id'], ondelete='CASCADE')
    )
    
    # Индексы для widget_configs
    op.create_index('ix_widget_dashboard_id', 'widget_configs', ['dashboard_id'])
    op.create_index('ix_widget_order', 'widget_configs', ['order'])
    
    # 3. Таблица слоёв карты
    op.create_table(
        'map_layer_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('metric_column', sa.String(length=100), nullable=False),
        sa.Column('color_scale', sa.String(length=50), default='Reds'),
        sa.Column('opacity', sa.Float(), default=0.7),
        sa.Column('show_in_rotation', sa.Boolean(), default=True),
        sa.Column('rotation_order', sa.Integer(), default=0),
        sa.Column('legend_title', sa.String(length=100), nullable=True),
        sa.Column('value_format', sa.String(length=50), default='{:.0f}'),
        sa.Column('thresholds', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Индексы для map_layer_configs
    op.create_index('ix_map_layer_rotation_order', 'map_layer_configs', ['rotation_order'])
    op.create_index('ix_map_layer_active', 'map_layer_configs', ['is_active'])
    
    # 4. Таблица тем
    op.create_table(
        'theme_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('primary_color', sa.String(length=7), default='#007BFF'),
        sa.Column('secondary_color', sa.String(length=7), default='#6C757D'),
        sa.Column('background_color', sa.String(length=7), default='#FFFFFF'),
        sa.Column('text_color', sa.String(length=7), default='#212529'),
        sa.Column('chart_colors', sa.JSON(), nullable=True),
        sa.Column('font_family', sa.String(length=100), default='Arial, sans-serif'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    print("✅ Таблицы админ-панели созданы")


def downgrade():
    """
    Удаление таблиц админ-панели
    """
    op.drop_table('theme_configs')
    op.drop_index('ix_map_layer_active', 'map_layer_configs')
    op.drop_index('ix_map_layer_rotation_order', 'map_layer_configs')
    op.drop_table('map_layer_configs')
    op.drop_index('ix_widget_order', 'widget_configs')
    op.drop_index('ix_widget_dashboard_id', 'widget_configs')
    op.drop_table('widget_configs')
    op.drop_table('dashboard_configs')
    
    print("✅ Таблицы админ-панели удалены")