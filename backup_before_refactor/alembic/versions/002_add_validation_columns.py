"""
添加数据校验相关字段
为现有表添加校验状态和质量评分字段

Revision ID: 002
Revises: 001
Create Date: 2024-01-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级 - 添加校验相关字段"""

    # 为现有表添加校验字段
    # 注意：这里使用兼容的方式添加字段，避免破坏现有数据

    # 1. 为 raw_market_data 添加校验字段
    op.add_column('raw_market_data',
        sa.Column('validation_score', sa.Numeric(precision=3, scale=2), nullable=True,
                 server_default=sa.text('1.0'), comment='数据校验评分')
    )
    op.add_column('raw_market_data',
        sa.Column('validation_passed', sa.Boolean(), nullable=True,
                 server_default=sa.text('true'), comment='校验是否通过')
    )

    # 2. 为 clean_market_data 添加更多校验字段
    op.add_column('clean_market_data',
        sa.Column('validation_passed', sa.Boolean(), nullable=True,
                 server_default=sa.text('true'), comment='数据校验是否通过')
    )

    # 3. 为 feature_technical_indicators 添加校验版本字段
    op.add_column('feature_technical_indicators',
        sa.Column('validation_score', sa.Numeric(precision=3, scale=2), nullable=True,
                 server_default=sa.text('1.0'), comment='指标校验评分')
    )

    # 4. 为 metadata_data_sources 添加新字段
    op.add_column('metadata_data_sources',
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True,
                 server_default=sa.text('60'), comment='每分钟请求限制')
    )
    op.add_column('metadata_data_sources',
        sa.Column('timeout_seconds', sa.Integer(), nullable=True,
                 server_default=sa.text('30'), comment='请求超时时间')
    )

    # 5. 为 metadata_symbols 添加新字段
    op.add_column('metadata_symbols',
        sa.Column('price_precision', sa.Integer(), nullable=True,
                 server_default=sa.text('8'), comment='价格精度')
    )
    op.add_column('metadata_symbols',
        sa.Column('volume_precision', sa.Integer(), nullable=True,
                 server_default=sa.text('2'), comment='成交量精度')
    )

    # 6. 创建新表：数据校验历史表
    op.create_table('metadata_validation_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=False),
        sa.Column('validation_type', sa.String(length=50), nullable=False),
        sa.Column('validation_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('issues_found', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('validated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('validator_version', sa.String(length=20), server_default=sa.text("'v1.0'"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 为新表创建索引
    op.create_index('idx_validation_history_table_record',
                   'metadata_validation_history',
                   ['table_name', 'record_id'], unique=False)
    op.create_index('idx_validation_history_validated_at',
                   'metadata_validation_history',
                   ['validated_at'], unique=False)

    # 更新默认值（可选）
    # 注意：在生产环境中，这些操作应该更谨慎

    print("✅ 校验字段添加完成")


def downgrade() -> None:
    """回滚 - 移除校验相关字段"""

    # 删除索引
    op.drop_index('idx_validation_history_validated_at', table_name='metadata_validation_history')
    op.drop_index('idx_validation_history_table_record', table_name='metadata_validation_history')

    # 删除新表
    op.drop_table('metadata_validation_history')

    # 删除添加的字段
    op.drop_column('metadata_symbols', 'volume_precision')
    op.drop_column('metadata_symbols', 'price_precision')
    op.drop_column('metadata_data_sources', 'timeout_seconds')
    op.drop_column('metadata_data_sources', 'rate_limit_per_minute')
    op.drop_column('feature_technical_indicators', 'validation_score')
    op.drop_column('clean_market_data', 'validation_passed')
    op.drop_column('raw_market_data', 'validation_passed')
    op.drop_column('raw_market_data', 'validation_score')

    print("✅ 校验字段移除完成")
