-- PredictLab 数据库建表SQL
-- 支持 Raw/Clean/Feature 三层数据架构
-- 兼容 PostgreSQL 和 ClickHouse

-- ===========================================
-- PostgreSQL 建表语句
-- ===========================================

-- Raw Layer: 原始数据层，保留完整原始数据
-- 支持多种数据源：predict, polymarket, onchain, dune

-- 1. 原始市场数据表 (Raw Market Data)
CREATE TABLE IF NOT EXISTS raw_market_data (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL, -- predict, polymarket, onchain, dune
    symbol VARCHAR(100) NOT NULL, -- 交易对/市场标识
    data_timestamp TIMESTAMP NOT NULL, -- 数据时间戳
    fetch_timestamp TIMESTAMP NOT NULL DEFAULT NOW(), -- 采集时间戳
    raw_data JSONB NOT NULL, -- 原始JSON数据
    data_hash VARCHAR(64) UNIQUE, -- 数据哈希，用于去重
    is_processed BOOLEAN DEFAULT FALSE, -- 是否已处理
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_raw_market_data_source_timestamp
    ON raw_market_data(source_type, data_timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_market_data_symbol_timestamp
    ON raw_market_data(symbol, data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_raw_market_data_hash
    ON raw_market_data(data_hash);
CREATE INDEX IF NOT EXISTS idx_raw_market_data_processed
    ON raw_market_data(is_processed) WHERE is_processed = FALSE;

-- 2. 原始链上交易数据表 (Raw OnChain Data)
CREATE TABLE IF NOT EXISTS raw_onchain_data (
    id SERIAL PRIMARY KEY,
    network VARCHAR(50) NOT NULL, -- ethereum, bsc, polygon等
    contract_address VARCHAR(100) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_hash VARCHAR(100) NOT NULL,
    log_index INTEGER NOT NULL,
    data_timestamp TIMESTAMP NOT NULL,
    fetch_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    raw_event_data JSONB NOT NULL,
    data_hash VARCHAR(64) UNIQUE,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(network, transaction_hash, log_index)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_raw_onchain_network_block
    ON raw_onchain_data(network, block_number DESC);
CREATE INDEX IF NOT EXISTS idx_raw_onchain_contract_timestamp
    ON raw_onchain_data(contract_address, data_timestamp);
CREATE INDEX IF NOT EXISTS idx_raw_onchain_hash
    ON raw_onchain_data(data_hash);

-- ===========================================
-- Clean Layer: 清洗数据层，标准化字段
-- ===========================================

-- 1. 清洗后的市场价格数据 (Clean Market Data)
CREATE TABLE IF NOT EXISTS clean_market_data (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    data_timestamp TIMESTAMP NOT NULL,
    price DECIMAL(36,18), -- 支持高精度价格
    volume DECIMAL(36,18),
    open_price DECIMAL(36,18),
    high_price DECIMAL(36,18),
    low_price DECIMAL(36,18),
    close_price DECIMAL(36,18),
    vwap DECIMAL(36,18), -- 成交量加权平均价格
    trade_count INTEGER,
    additional_data JSONB, -- 扩展字段
    data_quality_score DECIMAL(3,2), -- 数据质量评分 0-1
    is_outlier BOOLEAN DEFAULT FALSE,
    raw_data_id INTEGER REFERENCES raw_market_data(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_type, symbol, data_timestamp)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_clean_market_symbol_timestamp
    ON clean_market_data(symbol, data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_clean_market_source_timestamp
    ON clean_market_data(source_type, data_timestamp);
CREATE INDEX IF NOT EXISTS idx_clean_market_timestamp_only
    ON clean_market_data(data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_clean_market_quality
    ON clean_market_data(data_quality_score) WHERE data_quality_score < 0.8;

-- 2. 清洗后的K线数据 (Clean Kline Data)
CREATE TABLE IF NOT EXISTS clean_kline_data (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) NOT NULL,
    symbol VARCHAR(100) NOT NULL,
    interval_type VARCHAR(10) NOT NULL, -- 1m, 5m, 1h, 1d, 1w, 1M
    interval_start TIMESTAMP NOT NULL, -- K线开始时间
    interval_end TIMESTAMP NOT NULL, -- K线结束时间
    open_price DECIMAL(36,18),
    high_price DECIMAL(36,18),
    low_price DECIMAL(36,18),
    close_price DECIMAL(36,18),
    volume DECIMAL(36,18),
    trade_count INTEGER,
    vwap DECIMAL(36,18),
    data_points INTEGER, -- 构成这条K线的原始数据点数
    data_quality_score DECIMAL(3,2),
    is_complete BOOLEAN DEFAULT TRUE, -- K线是否完整
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_type, symbol, interval_type, interval_start)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_clean_kline_symbol_interval_time
    ON clean_kline_data(symbol, interval_type, interval_start DESC);
CREATE INDEX IF NOT EXISTS idx_clean_kline_time_range
    ON clean_kline_data(interval_start, interval_end);
CREATE INDEX IF NOT EXISTS idx_clean_kline_incomplete
    ON clean_kline_data(is_complete) WHERE is_complete = FALSE;

-- 3. 清洗后的链上交易数据 (Clean OnChain Data)
CREATE TABLE IF NOT EXISTS clean_onchain_transactions (
    id SERIAL PRIMARY KEY,
    network VARCHAR(50) NOT NULL,
    contract_address VARCHAR(100) NOT NULL,
    transaction_hash VARCHAR(100) NOT NULL,
    block_number BIGINT NOT NULL,
    transaction_index INTEGER,
    log_index INTEGER,
    event_name VARCHAR(100),
    from_address VARCHAR(100),
    to_address VARCHAR(100),
    token_address VARCHAR(100), -- ERC20代币地址
    amount DECIMAL(78,0), -- 支持大整数
    amount_decimal DECIMAL(36,18), -- 转换为小数形式
    gas_price DECIMAL(36,0),
    gas_used BIGINT,
    fee DECIMAL(36,18),
    data_timestamp TIMESTAMP NOT NULL,
    raw_data_id INTEGER REFERENCES raw_onchain_data(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(network, transaction_hash, log_index)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_clean_onchain_token_timestamp
    ON clean_onchain_transactions(token_address, data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_clean_onchain_from_to
    ON clean_onchain_transactions(from_address, to_address);
CREATE INDEX IF NOT EXISTS idx_clean_onchain_block
    ON clean_onchain_transactions(network, block_number DESC);

-- ===========================================
-- Feature Layer: 特征数据层，技术指标和衍生数据
-- ===========================================

-- 1. 技术指标数据 (Technical Indicators)
CREATE TABLE IF NOT EXISTS feature_technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    interval_type VARCHAR(10) NOT NULL,
    data_timestamp TIMESTAMP NOT NULL,
    -- 移动平均线
    sma_5 DECIMAL(36,18),
    sma_10 DECIMAL(36,18),
    sma_20 DECIMAL(36,18),
    sma_50 DECIMAL(36,18),
    sma_200 DECIMAL(36,18),
    ema_5 DECIMAL(36,18),
    ema_10 DECIMAL(36,18),
    ema_20 DECIMAL(36,18),
    -- 动量指标
    rsi_6 DECIMAL(5,2),
    rsi_14 DECIMAL(5,2),
    rsi_21 DECIMAL(5,2),
    -- MACD
    macd_line DECIMAL(36,18),
    macd_signal DECIMAL(36,18),
    macd_histogram DECIMAL(36,18),
    -- 布林带
    bb_upper DECIMAL(36,18),
    bb_middle DECIMAL(36,18),
    bb_lower DECIMAL(36,18),
    bb_width DECIMAL(36,18),
    -- 其他指标
    williams_r DECIMAL(5,2),
    cci DECIMAL(10,2), -- 商品通道指数
    stoch_k DECIMAL(5,2),
    stoch_d DECIMAL(5,2),
    -- 成交量指标
    volume_sma_5 DECIMAL(36,18),
    volume_sma_20 DECIMAL(36,18),
    obv DECIMAL(36,18), -- 能量潮
    -- 价格变化
    price_change_1d DECIMAL(10,4), -- 1日涨跌幅
    price_change_7d DECIMAL(10,4), -- 7日涨跌幅
    price_change_30d DECIMAL(10,4), -- 30日涨跌幅
    volatility_7d DECIMAL(10,4), -- 7日波动率
    volatility_30d DECIMAL(10,4), -- 30日波动率
    -- 元数据
    indicators_version VARCHAR(20) DEFAULT 'v1.0',
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, interval_type, data_timestamp)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_feature_ti_symbol_interval_time
    ON feature_technical_indicators(symbol, interval_type, data_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_feature_ti_rsi
    ON feature_technical_indicators(rsi_14) WHERE rsi_14 < 30 OR rsi_14 > 70;
CREATE INDEX IF NOT EXISTS idx_feature_ti_macd
    ON feature_technical_indicators(macd_histogram);

-- 2. 市场统计特征 (Market Statistics)
CREATE TABLE IF NOT EXISTS feature_market_stats (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(100) NOT NULL,
    stat_date DATE NOT NULL,
    stat_period VARCHAR(10) NOT NULL, -- 1d, 7d, 30d, 90d, 1y
    -- 价格统计
    price_open DECIMAL(36,18),
    price_high DECIMAL(36,18),
    price_low DECIMAL(36,18),
    price_close DECIMAL(36,18),
    price_avg DECIMAL(36,18),
    price_median DECIMAL(36,18),
    price_std DECIMAL(36,18),
    -- 成交量统计
    volume_total DECIMAL(36,18),
    volume_avg DECIMAL(36,18),
    volume_std DECIMAL(36,18),
    volume_max DECIMAL(36,18),
    -- 市场活跃度
    trade_count_total INTEGER,
    trade_count_avg DECIMAL(10,2),
    unique_traders INTEGER,
    concentration_ratio DECIMAL(5,4), -- 前十大交易者占比
    -- 波动率指标
    realized_volatility DECIMAL(10,4),
    parkinson_volatility DECIMAL(10,4),
    garman_klass_volatility DECIMAL(10,4),
    -- 流动性指标
    bid_ask_spread_avg DECIMAL(36,18),
    market_depth DECIMAL(36,18),
    turnover_ratio DECIMAL(10,4),
    -- 元数据
    stats_version VARCHAR(20) DEFAULT 'v1.0',
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(symbol, stat_date, stat_period)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_feature_stats_symbol_date
    ON feature_market_stats(symbol, stat_date DESC);
CREATE INDEX IF NOT EXISTS idx_feature_stats_period_date
    ON feature_market_stats(stat_period, stat_date DESC);

-- 3. 链上特征数据 (OnChain Features)
CREATE TABLE IF NOT EXISTS feature_onchain_metrics (
    id SERIAL PRIMARY KEY,
    network VARCHAR(50) NOT NULL,
    contract_address VARCHAR(100),
    token_symbol VARCHAR(20),
    metric_date DATE NOT NULL,
    metric_period VARCHAR(10) NOT NULL, -- 1d, 7d, 30d
    -- 交易统计
    transaction_count INTEGER,
    unique_senders INTEGER,
    unique_receivers INTEGER,
    total_volume DECIMAL(36,18),
    avg_transaction_size DECIMAL(36,18),
    -- Gas 统计
    avg_gas_price DECIMAL(36,18),
    total_gas_used BIGINT,
    total_fees DECIMAL(36,18),
    -- 地址活跃度
    active_addresses INTEGER,
    new_addresses INTEGER,
    dormant_addresses INTEGER,
    -- 大额交易
    whale_transactions INTEGER, -- >$10k
    large_transactions INTEGER, -- >$1k
    -- 网络健康度
    network_utilization DECIMAL(5,4),
    congestion_level DECIMAL(3,2), -- 0-1
    -- 元数据
    metrics_version VARCHAR(20) DEFAULT 'v1.0',
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(network, COALESCE(contract_address, ''), metric_date, metric_period)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_feature_onchain_network_date
    ON feature_onchain_metrics(network, metric_date DESC);
CREATE INDEX IF NOT EXISTS idx_feature_onchain_token_date
    ON feature_onchain_metrics(token_symbol, metric_date DESC) WHERE token_symbol IS NOT NULL;

-- ===========================================
-- 元数据和配置表
-- ===========================================

-- 数据源配置表
CREATE TABLE IF NOT EXISTS metadata_data_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50) UNIQUE NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    api_endpoint VARCHAR(500),
    api_key_encrypted TEXT, -- 加密存储的API密钥
    is_active BOOLEAN DEFAULT TRUE,
    last_successful_fetch TIMESTAMP,
    last_failed_fetch TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    fetch_interval_seconds INTEGER DEFAULT 300,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 符号/资产配置表
CREATE TABLE IF NOT EXISTS metadata_symbols (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(100) UNIQUE NOT NULL,
    symbol_name VARCHAR(200),
    source_type VARCHAR(50) NOT NULL,
    contract_address VARCHAR(100),
    network VARCHAR(50),
    decimals INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    launch_date DATE,
    category VARCHAR(50), -- crypto, stock, commodity, etc.
    tags TEXT[], -- 标签数组
    metadata JSONB, -- 扩展元数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 数据质量监控表
CREATE TABLE IF NOT EXISTS metadata_data_quality (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    check_date DATE NOT NULL,
    record_count INTEGER,
    null_count INTEGER,
    duplicate_count INTEGER,
    outlier_count INTEGER,
    quality_score DECIMAL(3,2),
    issues JSONB, -- 质量问题详情
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(table_name, check_date)
);

-- ===========================================
-- ClickHouse 建表语句 (时间序列优化)
-- ===========================================

-- ClickHouse Raw Market Data (使用ReplacingMergeTree处理重复数据)
CREATE TABLE IF NOT EXISTS raw_market_data_ch (
    source_type String,
    symbol String,
    data_timestamp DateTime,
    fetch_timestamp DateTime DEFAULT now(),
    raw_data String, -- JSON字符串
    data_hash String,
    is_processed UInt8 DEFAULT 0,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (source_type, symbol, data_timestamp)
PARTITION BY toYYYYMM(data_timestamp)
TTL toDate(data_timestamp) + INTERVAL 90 DAY; -- 90天后自动删除

-- ClickHouse Clean Kline Data (使用时间序列优化)
CREATE TABLE IF NOT EXISTS clean_kline_data_ch (
    source_type String,
    symbol String,
    interval_type String, -- 1m, 5m, 1h, 1d
    interval_start DateTime,
    interval_end DateTime,
    open_price Decimal128(18),
    high_price Decimal128(18),
    low_price Decimal128(18),
    close_price Decimal128(18),
    volume Decimal128(18),
    trade_count UInt32,
    vwap Decimal128(18),
    data_points UInt32,
    data_quality_score Decimal32(2),
    is_complete UInt8 DEFAULT 1,
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, interval_type, interval_start)
PARTITION BY toYYYYMM(interval_start)
TTL toDate(interval_start) + INTERVAL 365 DAY;

-- ClickHouse Technical Indicators (列式存储优化)
CREATE TABLE IF NOT EXISTS feature_technical_indicators_ch (
    symbol String,
    interval_type String,
    data_timestamp DateTime,
    -- MA系列
    sma_5 Decimal128(18),
    sma_10 Decimal128(18),
    sma_20 Decimal128(18),
    sma_50 Decimal128(18),
    sma_200 Decimal128(18),
    ema_5 Decimal128(18),
    ema_10 Decimal128(18),
    ema_20 Decimal128(18),
    -- RSI系列
    rsi_6 Decimal32(2),
    rsi_14 Decimal32(2),
    rsi_21 Decimal32(2),
    -- MACD
    macd_line Decimal128(18),
    macd_signal Decimal128(18),
    macd_histogram Decimal128(18),
    -- 布林带
    bb_upper Decimal128(18),
    bb_middle Decimal128(18),
    bb_lower Decimal128(18),
    -- 其他指标
    williams_r Decimal32(2),
    cci Decimal64(2),
    stoch_k Decimal32(2),
    stoch_d Decimal32(2),
    -- 成交量
    volume_sma_5 Decimal128(18),
    volume_sma_20 Decimal128(18),
    obv Decimal128(18),
    -- 价格变化
    price_change_1d Decimal64(4),
    price_change_7d Decimal64(4),
    price_change_30d Decimal64(4),
    volatility_7d Decimal64(4),
    volatility_30d Decimal64(4),
    -- 元数据
    indicators_version String DEFAULT 'v1.0',
    calculation_timestamp DateTime DEFAULT now(),
    created_at DateTime DEFAULT now(),
    updated_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (symbol, interval_type, data_timestamp)
PARTITION BY toYYYYMM(data_timestamp)
TTL toDate(data_timestamp) + INTERVAL 180 DAY;
