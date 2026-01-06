-- PredictLab 数据库操作示例
-- 包含数据插入、查询、更新等操作

-- ===========================================
-- 数据插入示例
-- ===========================================

-- 1. 插入原始市场数据 (Raw Layer)
INSERT INTO raw_market_data (
    source_type, symbol, data_timestamp, raw_data, data_hash
) VALUES (
    'predict',
    'BTC_PRICE',
    '2024-01-01 12:00:00+00',
    '{
        "market_id": "BTC_PRICE",
        "price": 45000.50,
        "volume": 1234567.89,
        "timestamp": "2024-01-01T12:00:00Z",
        "metadata": {
            "confidence": 0.95,
            "sources": ["exchange_a", "exchange_b"]
        }
    }'::jsonb,
    'hash_value_here'
) ON CONFLICT (data_hash) DO NOTHING;

-- 2. 批量插入清洗后的市场数据 (Clean Layer)
INSERT INTO clean_market_data (
    source_type, symbol, data_timestamp, price, volume,
    open_price, high_price, low_price, close_price,
    trade_count, data_quality_score, raw_data_id
) VALUES
    ('predict', 'BTC_PRICE', '2024-01-01 12:00:00+00', 45000.50, 1234567.89,
     44900.00, 45100.00, 44800.00, 45000.50, 1250, 0.95, 1),
    ('predict', 'ETH_PRICE', '2024-01-01 12:00:00+00', 2450.75, 987654.32,
     2430.00, 2460.00, 2420.00, 2450.75, 890, 0.92, 2)
ON CONFLICT (source_type, symbol, data_timestamp) DO UPDATE SET
    price = EXCLUDED.price,
    volume = EXCLUDED.volume,
    updated_at = NOW();

-- 3. 插入K线数据
INSERT INTO clean_kline_data (
    source_type, symbol, interval_type, interval_start, interval_end,
    open_price, high_price, low_price, close_price, volume,
    trade_count, data_points, data_quality_score
) VALUES (
    'predict', 'BTC_PRICE', '1h', '2024-01-01 12:00:00+00', '2024-01-01 12:59:59+00',
    44900.00, 45100.00, 44800.00, 45000.50, 1234567.89,
    1250, 60, 0.95
) ON CONFLICT (source_type, symbol, interval_type, interval_start) DO UPDATE SET
    close_price = EXCLUDED.close_price,
    high_price = GREATEST(high_price, EXCLUDED.high_price),
    low_price = LEAST(low_price, EXCLUDED.low_price),
    volume = volume + EXCLUDED.volume,
    trade_count = trade_count + EXCLUDED.trade_count,
    updated_at = NOW();

-- 4. 插入技术指标数据 (Feature Layer)
INSERT INTO feature_technical_indicators (
    symbol, interval_type, data_timestamp,
    sma_5, sma_10, sma_20, rsi_14,
    macd_line, macd_signal, macd_histogram,
    bb_upper, bb_middle, bb_lower,
    price_change_1d, volatility_7d
) VALUES (
    'BTC_PRICE', '1h', '2024-01-01 12:00:00+00',
    44800.00, 44700.00, 44600.00, 65.50,
    150.50, 120.30, 30.20,
    45200.00, 44800.00, 44400.00,
    2.50, 15.75
) ON CONFLICT (symbol, interval_type, data_timestamp) DO UPDATE SET
    rsi_14 = EXCLUDED.rsi_14,
    macd_line = EXCLUDED.macd_line,
    price_change_1d = EXCLUDED.price_change_1d,
    updated_at = NOW();

-- 5. 插入链上交易数据
INSERT INTO clean_onchain_transactions (
    network, contract_address, transaction_hash, block_number,
    from_address, to_address, token_address, amount, amount_decimal,
    gas_price, gas_used, fee, data_timestamp
) VALUES (
    'ethereum', '0x1234567890123456789012345678901234567890',
    '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    18500000, 100,
    '0x1111111111111111111111111111111111111111',
    '0x2222222222222222222222222222222222222222',
    '0xa0b86a33e6441e88c5f2712c3e9b74f5c4d6e3b6', -- USDC
    1000000, 1.0, -- 1 USDC (6 decimals)
    20000000000, 21000, 0.00042,
    '2024-01-01 12:00:00+00'
) ON CONFLICT (network, transaction_hash, log_index) DO NOTHING;

-- ===========================================
-- 数据查询示例
-- ===========================================

-- 1. 查询最新市场数据
SELECT
    symbol,
    data_timestamp,
    price,
    volume,
    data_quality_score
FROM clean_market_data
WHERE symbol = 'BTC_PRICE'
    AND data_timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY data_timestamp DESC
LIMIT 100;

-- 2. 查询K线数据 (用于图表)
SELECT
    interval_start,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM clean_kline_data
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND interval_start >= '2024-01-01 00:00:00'
    AND interval_start < '2024-01-02 00:00:00'
ORDER BY interval_start;

-- 3. 查询技术指标 (RSI超买超卖信号)
SELECT
    symbol,
    data_timestamp,
    rsi_14,
    macd_histogram,
    price_change_1d
FROM feature_technical_indicators
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND (rsi_14 < 30 OR rsi_14 > 70) -- 超买超卖信号
    AND data_timestamp >= NOW() - INTERVAL '7 days'
ORDER BY data_timestamp DESC;

-- 4. 查询交易量最大的代币
SELECT
    token_address,
    COUNT(*) as transaction_count,
    SUM(amount_decimal) as total_volume,
    AVG(amount_decimal) as avg_transaction_size
FROM clean_onchain_transactions
WHERE data_timestamp >= NOW() - INTERVAL '24 hours'
    AND token_address IS NOT NULL
GROUP BY token_address
ORDER BY total_volume DESC
LIMIT 10;

-- 5. 查询数据质量统计
SELECT
    table_name,
    check_date,
    quality_score,
    record_count,
    duplicate_count,
    outlier_count
FROM metadata_data_quality
WHERE check_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY check_date DESC, quality_score ASC;

-- 6. 时间序列聚合查询 (日K线)
SELECT
    DATE(interval_start) as date,
    MIN(low_price) as low,
    MAX(high_price) as high,
    SUM(volume) as total_volume,
    COUNT(*) as periods_count
FROM clean_kline_data
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND interval_start >= '2024-01-01'
GROUP BY DATE(interval_start)
ORDER BY date;

-- 7. 技术指标筛选 (金叉死叉信号)
WITH sma_signals AS (
    SELECT
        symbol,
        data_timestamp,
        sma_5,
        sma_10,
        CASE
            WHEN sma_5 > sma_10 AND LAG(sma_5) OVER (ORDER BY data_timestamp) <= LAG(sma_10) OVER (ORDER BY data_timestamp)
                THEN 'golden_cross' -- 金叉
            WHEN sma_5 < sma_10 AND LAG(sma_5) OVER (ORDER BY data_timestamp) >= LAG(sma_10) OVER (ORDER BY data_timestamp)
                THEN 'death_cross' -- 死叉
            ELSE 'no_signal'
        END as signal
    FROM feature_technical_indicators
    WHERE symbol = 'BTC_PRICE'
        AND interval_type = '1h'
)
SELECT * FROM sma_signals
WHERE signal IN ('golden_cross', 'death_cross')
    AND data_timestamp >= NOW() - INTERVAL '30 days'
ORDER BY data_timestamp DESC;

-- ===========================================
-- 数据更新和维护示例
-- ===========================================

-- 1. 标记数据为已处理
UPDATE raw_market_data
SET is_processed = TRUE, updated_at = NOW()
WHERE id IN (
    SELECT id FROM raw_market_data
    WHERE is_processed = FALSE
    LIMIT 1000
);

-- 2. 更新数据质量评分
UPDATE clean_market_data
SET data_quality_score = 0.85, updated_at = NOW()
WHERE data_timestamp >= '2024-01-01'
    AND data_timestamp < '2024-01-02'
    AND data_quality_score IS NULL;

-- 3. 批量更新技术指标 (历史重算)
UPDATE feature_technical_indicators
SET rsi_14 = 55.5, updated_at = NOW()
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND data_timestamp >= '2024-01-01 00:00:00'
    AND data_timestamp < '2024-01-01 06:00:00';

-- 4. 清理过期数据 (保留最近90天)
DELETE FROM raw_market_data
WHERE data_timestamp < NOW() - INTERVAL '90 days'
    AND is_processed = TRUE;

-- ===========================================
-- 高级查询示例
-- ===========================================

-- 1. 相关性分析 (价格与交易量)
SELECT
    CORR(close_price, volume) as price_volume_corr,
    CORR(close_price, trade_count) as price_trades_corr,
    COUNT(*) as data_points
FROM clean_kline_data
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND interval_start >= '2024-01-01';

-- 2. 波动率计算
SELECT
    symbol,
    DATE(data_timestamp) as date,
    STDDEV(close_price) as daily_volatility,
    AVG(close_price) as avg_price,
    MAX(close_price) - MIN(close_price) as daily_range
FROM clean_kline_data
WHERE interval_type = '1h'
    AND data_timestamp >= '2024-01-01'
GROUP BY symbol, DATE(data_timestamp)
ORDER BY date DESC;

-- 3. 异常检测 (基于统计)
WITH price_stats AS (
    SELECT
        symbol,
        AVG(close_price) as avg_price,
        STDDEV(close_price) as std_price
    FROM clean_kline_data
    WHERE interval_type = '1h'
        AND data_timestamp >= '2024-01-01'
    GROUP BY symbol
)
SELECT
    k.symbol,
    k.data_timestamp,
    k.close_price,
    ABS(k.close_price - p.avg_price) / p.std_price as z_score
FROM clean_kline_data k
JOIN price_stats p ON k.symbol = p.symbol
WHERE ABS(k.close_price - p.avg_price) / p.std_price > 3.0 -- 3倍标准差
ORDER BY z_score DESC;

-- ===========================================
-- ClickHouse 查询示例
-- ===========================================

-- ClickHouse 时间序列查询 (性能优化)
SELECT
    symbol,
    interval_type,
    interval_start,
    close_price,
    volume
FROM clean_kline_data_ch
WHERE symbol = 'BTC_PRICE'
    AND interval_type = '1h'
    AND interval_start >= '2024-01-01 00:00:00'
    AND interval_start < '2024-01-02 00:00:00'
ORDER BY interval_start;

-- ClickHouse 聚合查询 (秒级响应)
SELECT
    symbol,
    toStartOfHour(data_timestamp) as hour,
    avg(rsi_14) as avg_rsi,
    max(price_change_1d) as max_daily_change,
    min(volatility_7d) as min_volatility
FROM feature_technical_indicators_ch
WHERE symbol IN ('BTC_PRICE', 'ETH_PRICE')
    AND data_timestamp >= today() - INTERVAL 7 DAY
GROUP BY symbol, hour
ORDER BY hour DESC;

-- ClickHouse 实时监控查询
SELECT
    count() as recent_updates,
    max(updated_at) as last_update
FROM clean_kline_data_ch
WHERE updated_at >= now() - INTERVAL 5 MINUTE;
