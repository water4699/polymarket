-- Polymarket数据表设计
-- 设计原则：规范化存储，避免数据冗余，支持复杂查询

-- ===========================================
-- 1. 市场基本信息表 (核心表)
-- ===========================================
CREATE TABLE IF NOT EXISTS markets (
    id BIGINT PRIMARY KEY,                                    -- 市场ID
    question TEXT NOT NULL,                                   -- 预测问题
    condition_id VARCHAR(66) UNIQUE NOT NULL,                 -- 条件ID (0x开头)
    slug VARCHAR(500),                                        -- URL标识
    description TEXT,                                         -- 详细描述
    resolution_source TEXT,                                   -- 结果来源

    -- 时间相关
    created_at TIMESTAMP WITH TIME ZONE,                      -- 创建时间
    updated_at TIMESTAMP WITH TIME ZONE,                      -- 更新时间
    start_date TIMESTAMP WITH TIME ZONE,                      -- 开始时间
    end_date TIMESTAMP WITH TIME ZONE,                       -- 结束时间
    closed_time TIMESTAMP WITH TIME ZONE,                     -- 关闭时间

    -- 状态相关
    active BOOLEAN DEFAULT TRUE,                              -- 是否活跃
    closed BOOLEAN DEFAULT FALSE,                             -- 是否关闭
    archived BOOLEAN DEFAULT FALSE,                           -- 是否归档
    restricted BOOLEAN DEFAULT FALSE,                         -- 是否受限
    featured BOOLEAN DEFAULT FALSE,                           -- 是否精选
    new BOOLEAN DEFAULT TRUE,                                 -- 是否新市场

    -- 交易相关
    volume DECIMAL(20,6),                                     -- 总成交量
    volume_24hr DECIMAL(20,6),                                -- 24h成交量
    volume_1wk DECIMAL(20,6),                                 -- 1周成交量
    volume_1mo DECIMAL(20,6),                                 -- 1月成交量
    volume_1yr DECIMAL(20,6),                                 -- 1年成交量
    liquidity DECIMAL(20,6),                                  -- 流动性

    -- 区块链相关
    enable_order_book BOOLEAN DEFAULT TRUE,                   -- 是否启用订单簿
    accepting_orders BOOLEAN DEFAULT TRUE,                    -- 是否接受订单
    neg_risk BOOLEAN DEFAULT FALSE,                           -- 负风险
    neg_risk_market_id VARCHAR(66),                           -- 负风险市场ID

    -- UMA相关
    uma_bond DECIMAL(20,6),                                   -- UMA保证金
    uma_reward DECIMAL(20,6),                                 -- UMA奖励
    uma_end_date TIMESTAMP WITH TIME ZONE,                    -- UMA结束时间
    uma_resolution_status VARCHAR(50),                        -- UMA解决状态

    -- 媒体相关
    image TEXT,                                               -- 图片URL
    icon TEXT,                                                -- 图标URL

    -- 提交信息
    submitted_by VARCHAR(42),                                 -- 提交者地址

    -- 分类标签 (Sports, Crypto, Politics等)
    category VARCHAR(50) NOT NULL,                            -- 分类

    -- 元数据
    data_source VARCHAR(100),                                 -- 数据来源
    sport_type VARCHAR(50),                                   -- 体育类型

    -- 时间戳
    created_at_db TIMESTAMP WITH TIME ZONE DEFAULT NOW(),     -- 入库时间
    updated_at_db TIMESTAMP WITH TIME ZONE DEFAULT NOW()      -- 更新时间
);

-- ===========================================
-- 2. 市场结果选项表
-- ===========================================
CREATE TABLE IF NOT EXISTS market_outcomes (
    id SERIAL PRIMARY KEY,
    market_id BIGINT REFERENCES markets(id) ON DELETE CASCADE,

    outcome_text VARCHAR(100) NOT NULL,                       -- 结果文本 (Yes/No等)
    outcome_price DECIMAL(10,6),                              -- 结果价格
    outcome_index INTEGER NOT NULL,                           -- 结果索引 (0,1,2...)

    UNIQUE(market_id, outcome_index)
);

-- ===========================================
-- 3. 市场事件表
-- ===========================================
CREATE TABLE IF NOT EXISTS market_events (
    id SERIAL PRIMARY KEY,
    market_id BIGINT REFERENCES markets(id) ON DELETE CASCADE,

    event_id BIGINT,                                          -- 事件ID
    ticker VARCHAR(200),                                      -- 股票代码
    event_slug VARCHAR(500),                                  -- 事件标识
    title TEXT,                                               -- 事件标题
    event_description TEXT,                                   -- 事件描述

    event_start_date TIMESTAMP WITH TIME ZONE,                -- 事件开始时间
    event_end_date TIMESTAMP WITH TIME ZONE,                  -- 事件结束时间
    event_created_at TIMESTAMP WITH TIME ZONE,                -- 事件创建时间

    active BOOLEAN DEFAULT TRUE,
    closed BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,

    volume DECIMAL(20,6),
    liquidity DECIMAL(20,6),
    comment_count INTEGER DEFAULT 0,

    UNIQUE(market_id, event_id)
);

-- ===========================================
-- 4. 合约地址表
-- ===========================================
CREATE TABLE IF NOT EXISTS contract_addresses (
    id SERIAL PRIMARY KEY,
    market_id BIGINT REFERENCES markets(id) ON DELETE CASCADE,

    conditional_tokens VARCHAR(42),                           -- Conditional Tokens合约
    clob_exchange VARCHAR(42),                                -- CLOB交易所合约
    fee_module VARCHAR(42),                                   -- 费用模块合约

    UNIQUE(market_id)
);

-- ===========================================
-- 5. CLOB代币ID表
-- ===========================================
CREATE TABLE IF NOT EXISTS clob_token_ids (
    id SERIAL PRIMARY KEY,
    market_id BIGINT REFERENCES markets(id) ON DELETE CASCADE,

    token_id TEXT NOT NULL,                                   -- 代币ID (大整数字符串)
    token_index INTEGER NOT NULL,                             -- 代币索引 (0=Yes, 1=No等)
    outcome_text VARCHAR(100),                                -- 对应结果 (Yes/No等)

    UNIQUE(market_id, token_index)
);

-- ===========================================
-- 6. 市场奖励表
-- ===========================================
CREATE TABLE IF NOT EXISTS market_rewards (
    id SERIAL PRIMARY KEY,
    market_id BIGINT REFERENCES markets(id) ON DELETE CASCADE,

    reward_id BIGINT,                                         -- 奖励ID
    asset_address VARCHAR(42),                                -- 资产合约地址
    rewards_amount DECIMAL(20,6),                             -- 奖励金额
    rewards_daily_rate DECIMAL(10,6),                         -- 每日奖励率

    start_date DATE,                                          -- 开始日期
    end_date DATE,                                            -- 结束日期

    UNIQUE(market_id, reward_id)
);

-- ===========================================
-- 7. 数据文件元数据表
-- ===========================================
CREATE TABLE IF NOT EXISTS data_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,                           -- 文件名
    file_path TEXT,                                           -- 文件路径
    timestamp TIMESTAMP WITH TIME ZONE,                       -- 文件时间戳
    total_markets INTEGER,                                    -- 市场总数
    category VARCHAR(50),                                     -- 分类

    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),      -- 处理时间
    status VARCHAR(20) DEFAULT 'completed',                   -- 处理状态

    UNIQUE(filename)
);

-- ===========================================
-- 8. 原始JSON数据存储表
-- ===========================================
CREATE TABLE IF NOT EXISTS raw_json_data (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,                           -- 文件名
    category VARCHAR(50),                                     -- 数据分类
    file_timestamp TIMESTAMP WITH TIME ZONE,                  -- 文件时间戳
    total_markets INTEGER,                                    -- 市场总数

    -- 原始JSON数据 (压缩存储)
    metadata_json TEXT,                                       -- 元数据JSON
    markets_json TEXT,                                        -- 市场数据JSON (可能很大)

    -- 文件信息
    file_size_bytes BIGINT,                                   -- 文件大小(字节)
    compression_type VARCHAR(20) DEFAULT 'none',              -- 压缩类型

    -- 时间戳
    stored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),         -- 存储时间
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),      -- 最后更新时间

    -- 唯一约束
    UNIQUE(filename, category)
);

-- ===========================================
-- 索引优化
-- ===========================================

-- 市场表索引
CREATE INDEX IF NOT EXISTS idx_markets_category ON markets(category);
CREATE INDEX IF NOT EXISTS idx_markets_active ON markets(active);
CREATE INDEX IF NOT EXISTS idx_markets_closed ON markets(closed);
CREATE INDEX IF NOT EXISTS idx_markets_created_at ON markets(created_at);
CREATE INDEX IF NOT EXISTS idx_markets_end_date ON markets(end_date);
CREATE INDEX IF NOT EXISTS idx_markets_condition_id ON markets(condition_id);

-- 结果表索引
CREATE INDEX IF NOT EXISTS idx_market_outcomes_market_id ON market_outcomes(market_id);

-- 事件表索引
CREATE INDEX IF NOT EXISTS idx_market_events_market_id ON market_events(market_id);
CREATE INDEX IF NOT EXISTS idx_market_events_event_id ON market_events(event_id);

-- 合约表索引
CREATE INDEX IF NOT EXISTS idx_contract_addresses_market_id ON contract_addresses(market_id);

-- 代币表索引
CREATE INDEX IF NOT EXISTS idx_clob_token_ids_market_id ON clob_token_ids(market_id);
CREATE INDEX IF NOT EXISTS idx_clob_token_ids_token_id ON clob_token_ids(token_id);

-- 原始JSON数据表索引
CREATE INDEX IF NOT EXISTS idx_raw_json_filename ON raw_json_data(filename);
CREATE INDEX IF NOT EXISTS idx_raw_json_category ON raw_json_data(category);
CREATE INDEX IF NOT EXISTS idx_raw_json_timestamp ON raw_json_data(file_timestamp);

-- ===========================================
-- 数据完整性约束
-- ===========================================

-- 确保市场ID为正数
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_markets_id_positive') THEN
        ALTER TABLE markets ADD CONSTRAINT chk_markets_id_positive CHECK (id > 0);
    END IF;
END
$$;

-- 确保交易量为非负数
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_markets_volume_non_negative') THEN
        ALTER TABLE markets ADD CONSTRAINT chk_markets_volume_non_negative CHECK (volume >= 0);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_markets_liquidity_non_negative') THEN
        ALTER TABLE markets ADD CONSTRAINT chk_markets_liquidity_non_negative CHECK (liquidity >= 0);
    END IF;
END
$$;

-- 确保时间逻辑
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'chk_markets_dates_logical') THEN
        ALTER TABLE markets ADD CONSTRAINT chk_markets_dates_logical
            CHECK (start_date <= end_date AND created_at <= updated_at);
    END IF;
END
$$;

-- ===========================================
-- 视图定义
-- ===========================================

-- 活跃市场视图
CREATE OR REPLACE VIEW active_markets AS
SELECT * FROM markets
WHERE active = TRUE AND closed = FALSE
ORDER BY created_at DESC;

-- 高流动性市场视图
CREATE OR REPLACE VIEW high_liquidity_markets AS
SELECT * FROM markets
WHERE liquidity > 10000
ORDER BY liquidity DESC;

-- 近期结束市场视图
CREATE OR REPLACE VIEW recently_closed_markets AS
SELECT * FROM markets
WHERE closed = TRUE AND closed_time > NOW() - INTERVAL '30 days'
ORDER BY closed_time DESC;
