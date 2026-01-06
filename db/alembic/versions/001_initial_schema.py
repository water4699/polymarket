"""
初始数据库结构
创建 PredictLab 三层数据架构的所有基础表

Revision ID: 001
Revises:
Create Date: 2024-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库结构 - 创建所有基础表"""

    # ===========================================
    # Raw Layer: 原始数据层
    # ===========================================

    # 原始市场数据表
    op.create_table('raw_market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        sa.Column('fetch_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('raw_data', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('data_hash', sa.String(length=64), nullable=True),
        sa.Column('is_processed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('data_hash')
    )

    # 原始链上交易数据表
    op.create_table('raw_onchain_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', sa.String(length=50), nullable=False),
        sa.Column('contract_address', sa.String(length=100), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('transaction_hash', sa.String(length=100), nullable=False),
        sa.Column('log_index', sa.Integer(), nullable=False),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        sa.Column('fetch_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('raw_event_data', sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column('data_hash', sa.String(length=64), nullable=True),
        sa.Column('is_processed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('network', 'transaction_hash', 'log_index'),
        sa.UniqueConstraint('data_hash')
    )

    # ===========================================
    # Clean Layer: 清洗数据层
    # ===========================================

    # 清洗后的市场价格数据
    op.create_table('clean_market_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('open_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('high_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('low_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('close_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('vwap', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('trade_count', sa.Integer(), nullable=True),
        sa.Column('additional_data', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_outlier', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('raw_data_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_data_id'], ['raw_market_data.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'symbol', 'data_timestamp')
    )

    # 清洗后的K线数据
    op.create_table('clean_kline_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('interval_type', sa.String(length=10), nullable=False),
        sa.Column('interval_start', sa.DateTime(), nullable=False),
        sa.Column('interval_end', sa.DateTime(), nullable=False),
        sa.Column('open_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('high_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('low_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('close_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('trade_count', sa.Integer(), nullable=True),
        sa.Column('vwap', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('data_points', sa.Integer(), nullable=True),
        sa.Column('data_quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('is_complete', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type', 'symbol', 'interval_type', 'interval_start')
    )

    # 清洗后的链上交易数据
    op.create_table('clean_onchain_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', sa.String(length=50), nullable=False),
        sa.Column('contract_address', sa.String(length=100), nullable=False),
        sa.Column('transaction_hash', sa.String(length=100), nullable=False),
        sa.Column('block_number', sa.BigInteger(), nullable=False),
        sa.Column('transaction_index', sa.Integer(), nullable=True),
        sa.Column('log_index', sa.Integer(), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=True),
        sa.Column('from_address', sa.String(length=100), nullable=True),
        sa.Column('to_address', sa.String(length=100), nullable=True),
        sa.Column('token_address', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Numeric(precision=78, scale=0), nullable=True),
        sa.Column('amount_decimal', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('gas_price', sa.Numeric(precision=36, scale=0), nullable=True),
        sa.Column('gas_used', sa.BigInteger(), nullable=True),
        sa.Column('fee', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        sa.Column('raw_data_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['raw_data_id'], ['raw_onchain_data.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('network', 'transaction_hash', 'log_index')
    )

    # ===========================================
    # Feature Layer: 特征数据层
    # ===========================================

    # 技术指标数据
    op.create_table('feature_technical_indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('interval_type', sa.String(length=10), nullable=False),
        sa.Column('data_timestamp', sa.DateTime(), nullable=False),
        # 移动平均线
        sa.Column('sma_5', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('sma_10', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('sma_20', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('sma_50', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('sma_200', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('ema_5', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('ema_10', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('ema_20', sa.Numeric(precision=36, scale=18), nullable=True),
        # 动量指标
        sa.Column('rsi_6', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('rsi_14', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('rsi_21', sa.Numeric(precision=5, scale=2), nullable=True),
        # MACD
        sa.Column('macd_line', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('macd_signal', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('macd_histogram', sa.Numeric(precision=36, scale=18), nullable=True),
        # 布林带
        sa.Column('bb_upper', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('bb_middle', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('bb_lower', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('bb_width', sa.Numeric(precision=36, scale=18), nullable=True),
        # 其他指标
        sa.Column('williams_r', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('cci', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('stoch_k', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('stoch_d', sa.Numeric(precision=5, scale=2), nullable=True),
        # 成交量指标
        sa.Column('volume_sma_5', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume_sma_20', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('obv', sa.Numeric(precision=36, scale=18), nullable=True),
        # 价格变化
        sa.Column('price_change_1d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_7d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('price_change_30d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('volatility_7d', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('volatility_30d', sa.Numeric(precision=10, scale=4), nullable=True),
        # 元数据
        sa.Column('indicators_version', sa.String(length=20), server_default=sa.text("'v1.0'"), nullable=False),
        sa.Column('calculation_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'interval_type', 'data_timestamp')
    )

    # 市场统计特征
    op.create_table('feature_market_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('stat_date', sa.Date(), nullable=False),
        sa.Column('stat_period', sa.String(length=10), nullable=False),
        # 价格统计
        sa.Column('price_open', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_high', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_low', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_close', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_avg', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_median', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('price_std', sa.Numeric(precision=36, scale=18), nullable=True),
        # 成交量统计
        sa.Column('volume_total', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume_avg', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume_std', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('volume_max', sa.Numeric(precision=36, scale=18), nullable=True),
        # 市场活跃度
        sa.Column('trade_count_total', sa.Integer(), nullable=True),
        sa.Column('trade_count_avg', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('unique_traders', sa.Integer(), nullable=True),
        sa.Column('concentration_ratio', sa.Numeric(precision=5, scale=4), nullable=True),
        # 波动率指标
        sa.Column('realized_volatility', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('parkinson_volatility', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('garman_klass_volatility', sa.Numeric(precision=10, scale=4), nullable=True),
        # 流动性指标
        sa.Column('bid_ask_spread_avg', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('market_depth', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('turnover_ratio', sa.Numeric(precision=10, scale=4), nullable=True),
        # 元数据
        sa.Column('stats_version', sa.String(length=20), server_default=sa.text("'v1.0'"), nullable=False),
        sa.Column('calculation_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol', 'stat_date', 'stat_period')
    )

    # 链上特征数据
    op.create_table('feature_onchain_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', sa.String(length=50), nullable=False),
        sa.Column('contract_address', sa.String(length=100), nullable=True),
        sa.Column('token_symbol', sa.String(length=20), nullable=True),
        sa.Column('metric_date', sa.Date(), nullable=False),
        sa.Column('metric_period', sa.String(length=10), nullable=False),
        # 交易统计
        sa.Column('transaction_count', sa.Integer(), nullable=True),
        sa.Column('unique_senders', sa.Integer(), nullable=True),
        sa.Column('unique_receivers', sa.Integer(), nullable=True),
        sa.Column('total_volume', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('avg_transaction_size', sa.Numeric(precision=36, scale=18), nullable=True),
        # Gas 统计
        sa.Column('avg_gas_price', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('total_gas_used', sa.BigInteger(), nullable=True),
        sa.Column('total_fees', sa.Numeric(precision=36, scale=18), nullable=True),
        # 地址活跃度
        sa.Column('active_addresses', sa.Integer(), nullable=True),
        sa.Column('new_addresses', sa.Integer(), nullable=True),
        sa.Column('dormant_addresses', sa.Integer(), nullable=True),
        # 大额交易
        sa.Column('whale_transactions', sa.Integer(), nullable=True),
        sa.Column('large_transactions', sa.Integer(), nullable=True),
        # 网络健康度
        sa.Column('network_utilization', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('congestion_level', sa.Numeric(precision=3, scale=2), nullable=True),
        # 元数据
        sa.Column('metrics_version', sa.String(length=20), server_default=sa.text("'v1.0'"), nullable=False),
        sa.Column('calculation_timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('network', sa.text("COALESCE(contract_address, '')"), 'metric_date', 'metric_period')
    )

    # ===========================================
    # 元数据和配置表
    # ===========================================

    # 数据源配置表
    op.create_table('metadata_data_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('last_successful_fetch', sa.DateTime(), nullable=True),
        sa.Column('last_failed_fetch', sa.DateTime(), nullable=True),
        sa.Column('failure_count', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('fetch_interval_seconds', sa.Integer(), server_default=sa.text('300'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_type')
    )

    # 符号/资产配置表
    op.create_table('metadata_symbols',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(length=100), nullable=False),
        sa.Column('symbol_name', sa.String(length=200), nullable=True),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('contract_address', sa.String(length=100), nullable=True),
        sa.Column('network', sa.String(length=50), nullable=True),
        sa.Column('decimals', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('launch_date', sa.Date(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.dialects.postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )

    # 数据质量监控表
    op.create_table('metadata_data_quality',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False),
        sa.Column('check_date', sa.Date(), nullable=False),
        sa.Column('record_count', sa.Integer(), nullable=True),
        sa.Column('null_count', sa.Integer(), nullable=True),
        sa.Column('duplicate_count', sa.Integer(), nullable=True),
        sa.Column('outlier_count', sa.Integer(), nullable=True),
        sa.Column('quality_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('issues', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_name', 'check_date')
    )

    # ===========================================
    # 创建索引
    # ===========================================

    # Raw 数据索引
    op.create_index('idx_raw_market_data_source_timestamp', 'raw_market_data', ['source_type', 'data_timestamp'], unique=False)
    op.create_index('idx_raw_market_data_symbol_timestamp', 'raw_market_data', ['symbol', 'data_timestamp'], unique=False)
    op.create_index('idx_raw_market_data_hash', 'raw_market_data', ['data_hash'], unique=False)
    op.create_index('idx_raw_market_data_processed', 'raw_market_data', ['is_processed'], unique=False, postgresql_where=sa.text("is_processed = false"))

    op.create_index('idx_raw_onchain_network_block', 'raw_onchain_data', ['network', 'block_number'], unique=False)
    op.create_index('idx_raw_onchain_contract_timestamp', 'raw_onchain_data', ['contract_address', 'data_timestamp'], unique=False)

    # Clean 数据索引
    op.create_index('idx_clean_market_symbol_timestamp', 'clean_market_data', ['symbol', 'data_timestamp'], unique=False)
    op.create_index('idx_clean_market_source_timestamp', 'clean_market_data', ['source_type', 'data_timestamp'], unique=False)
    op.create_index('idx_clean_market_timestamp_only', 'clean_market_data', ['data_timestamp'], unique=False)
    op.create_index('idx_clean_market_quality', 'clean_market_data', ['data_quality_score'], unique=False, postgresql_where=sa.text("data_quality_score < 0.8"))

    op.create_index('idx_clean_kline_symbol_interval_time', 'clean_kline_data', ['symbol', 'interval_type', 'interval_start'], unique=False)
    op.create_index('idx_clean_kline_time_range', 'clean_kline_data', ['interval_start', 'interval_end'], unique=False)
    op.create_index('idx_clean_kline_incomplete', 'clean_kline_data', ['is_complete'], unique=False, postgresql_where=sa.text("is_complete = false"))

    op.create_index('idx_clean_onchain_token_timestamp', 'clean_onchain_transactions', ['token_address', 'data_timestamp'], unique=False)
    op.create_index('idx_clean_onchain_from_to', 'clean_onchain_transactions', ['from_address', 'to_address'], unique=False)
    op.create_index('idx_clean_onchain_block', 'clean_onchain_transactions', ['network', 'block_number'], unique=False)

    # Feature 数据索引
    op.create_index('idx_feature_ti_symbol_interval_time', 'feature_technical_indicators', ['symbol', 'interval_type', 'data_timestamp'], unique=False)
    op.create_index('idx_feature_ti_rsi', 'feature_technical_indicators', ['rsi_14'], unique=False, postgresql_where=sa.text("rsi_14 < 30 OR rsi_14 > 70"))
    op.create_index('idx_feature_ti_macd', 'feature_technical_indicators', ['macd_histogram'], unique=False)

    op.create_index('idx_feature_stats_symbol_date', 'feature_market_stats', ['symbol', 'stat_date'], unique=False)
    op.create_index('idx_feature_stats_period_date', 'feature_market_stats', ['stat_period', 'stat_date'], unique=False)

    op.create_index('idx_feature_onchain_network_date', 'feature_onchain_metrics', ['network', 'metric_date'], unique=False)
    op.create_index('idx_feature_onchain_token_date', 'feature_onchain_metrics', ['token_symbol', 'metric_date'], unique=False, postgresql_where=sa.text("token_symbol IS NOT NULL"))

    # 元数据索引
    op.create_index('idx_metadata_symbols_category', 'metadata_symbols', ['category', 'is_active'], unique=False)
    op.create_index('idx_metadata_quality_date', 'metadata_data_quality', ['check_date'], unique=False)


def downgrade() -> None:
    """回滚数据库结构 - 删除所有表"""

    # 删除索引
    op.drop_index('idx_metadata_quality_date', table_name='metadata_data_quality')
    op.drop_index('idx_metadata_symbols_category', table_name='metadata_symbols')
    op.drop_index('idx_feature_onchain_token_date', table_name='feature_onchain_metrics')
    op.drop_index('idx_feature_onchain_network_date', table_name='feature_onchain_metrics')
    op.drop_index('idx_feature_stats_period_date', table_name='feature_market_stats')
    op.drop_index('idx_feature_stats_symbol_date', table_name='feature_market_stats')
    op.drop_index('idx_feature_ti_macd', table_name='feature_technical_indicators')
    op.drop_index('idx_feature_ti_rsi', table_name='feature_technical_indicators')
    op.drop_index('idx_feature_ti_symbol_interval_time', table_name='feature_technical_indicators')
    op.drop_index('idx_clean_onchain_block', table_name='clean_onchain_transactions')
    op.drop_index('idx_clean_onchain_from_to', table_name='clean_onchain_transactions')
    op.drop_index('idx_clean_onchain_token_timestamp', table_name='clean_onchain_transactions')
    op.drop_index('idx_clean_kline_incomplete', table_name='clean_kline_data')
    op.drop_index('idx_clean_kline_time_range', table_name='clean_kline_data')
    op.drop_index('idx_clean_kline_symbol_interval_time', table_name='clean_kline_data')
    op.drop_index('idx_clean_market_quality', table_name='clean_market_data')
    op.drop_index('idx_clean_market_timestamp_only', table_name='clean_market_data')
    op.drop_index('idx_clean_market_source_timestamp', table_name='clean_market_data')
    op.drop_index('idx_clean_market_symbol_timestamp', table_name='clean_market_data')
    op.drop_index('idx_raw_onchain_contract_timestamp', table_name='raw_onchain_data')
    op.drop_index('idx_raw_onchain_network_block', table_name='raw_onchain_data')
    op.drop_index('idx_raw_market_data_processed', table_name='raw_market_data')
    op.drop_index('idx_raw_market_data_hash', table_name='raw_market_data')
    op.drop_index('idx_raw_market_data_symbol_timestamp', table_name='raw_market_data')
    op.drop_index('idx_raw_market_data_source_timestamp', table_name='raw_market_data')

    # 删除表
    op.drop_table('metadata_data_quality')
    op.drop_table('metadata_symbols')
    op.drop_table('metadata_data_sources')
    op.drop_table('feature_onchain_metrics')
    op.drop_table('feature_market_stats')
    op.drop_table('feature_technical_indicators')
    op.drop_table('clean_onchain_transactions')
    op.drop_table('clean_kline_data')
    op.drop_table('clean_market_data')
    op.drop_table('raw_onchain_data')
    op.drop_table('raw_market_data')
