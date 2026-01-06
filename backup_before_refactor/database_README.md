# PredictLab 数据库架构说明

## 📊 数据分层架构

PredictLab 采用三层数据架构设计，支持数据湖 + 数据仓库的混合模式：

### 🗃️ Raw Layer (原始数据层)
**存储位置**: MongoDB / PostgreSQL
**数据特性**:
- 保留完整原始 JSON 数据
- 支持多种数据源格式
- 数据哈希去重机制
- 可追溯数据源头

**适用场景**:
- 数据审计和回溯
- 原始数据重处理
- 数据质量检查

### 🧹 Clean Layer (清洗数据层)
**存储位置**: PostgreSQL
**数据特性**:
- 字段标准化和统一
- 数据类型转换
- 异常值检测和处理
- 时间序列对齐

**适用场景**:
- 业务分析和报表
- 模型训练数据准备
- API 数据服务

### 🎯 Feature Layer (特征数据层)
**存储位置**: PostgreSQL / ClickHouse
**数据特性**:
- 技术指标和统计特征
- 时间序列聚合数据
- 派生计算字段
- 历史版本管理

**适用场景**:
- 量化策略开发
- 实时分析仪表板
- 机器学习特征工程

## 🏗️ 表结构设计

### Raw Layer 表结构

#### `raw_market_data`
```sql
原始市场数据表 - 支持 Predict/Polymarket/Dune 数据
- id: 主键
- source_type: 数据源类型 (predict/polymarket/dune)
- symbol: 交易对标识
- data_timestamp: 数据时间戳
- fetch_timestamp: 采集时间戳
- raw_data: 原始JSON数据
- data_hash: 数据哈希(唯一约束)
- is_processed: 处理状态
```

#### `raw_onchain_data`
```sql
原始链上数据表 - 支持区块链事件数据
- id: 主键
- network: 网络类型 (ethereum/bsc/polygon)
- contract_address: 合约地址
- event_name: 事件名称
- block_number: 区块号
- transaction_hash: 交易哈希
- log_index: 日志索引
- raw_event_data: 原始事件数据
- data_hash: 数据哈希(唯一约束)
```

### Clean Layer 表结构

#### `clean_market_data`
```sql
清洗后市场数据表 - 标准化价格和交易数据
- id: 主键
- source_type: 数据源类型
- symbol: 交易对标识
- data_timestamp: 数据时间戳
- price/volume: 价格和成交量
- open/high/low/close: OHLC数据
- vwap: 成交量加权平均价格
- data_quality_score: 数据质量评分
- UNIQUE(source_type, symbol, data_timestamp)
```

#### `clean_kline_data`
```sql
清洗后K线数据表 - 多周期K线数据
- id: 主键
- source_type: 数据源类型
- symbol: 交易对标识
- interval_type: 周期类型 (1m/5m/1h/1d/1w/1M)
- interval_start/end: K线时间区间
- OHLC + Volume: K线数据
- data_points: 构成K线的原始数据点数
- UNIQUE(source_type, symbol, interval_type, interval_start)
```

#### `clean_onchain_transactions`
```sql
清洗后链上交易表 - 标准化区块链交易数据
- id: 主键
- network: 网络类型
- contract_address: 合约地址
- transaction_hash: 交易哈希
- from_address/to_address: 转账地址
- amount/amount_decimal: 转账金额
- gas_price/gas_used/fee: Gas费用
- UNIQUE(network, transaction_hash, log_index)
```

### Feature Layer 表结构

#### `feature_technical_indicators`
```sql
技术指标表 - 完整的量化指标集合
- id: 主键
- symbol/interval_type: 资产和周期
- data_timestamp: 时间戳
- MA系列: sma_5/10/20/50/200, ema_5/10/20
- 动量指标: rsi_6/14/21, macd, 布林带
- 成交量指标: volume_sma, obv
- 价格变化: price_change_1d/7d/30d
- 波动率: volatility_7d/30d
- UNIQUE(symbol, interval_type, data_timestamp)
```

#### `feature_market_stats`
```sql
市场统计表 - 周期性市场统计数据
- id: 主键
- symbol/stat_date/stat_period: 资产/日期/周期
- 价格统计: open/high/low/close/avg/median/std
- 成交量统计: total/avg/std/max
- 活跃度指标: trade_count, unique_traders
- 波动率指标: realized/parkinson/garman_klass
- 流动性指标: spread, depth, turnover
```

#### `feature_onchain_metrics`
```sql
链上指标表 - 区块链网络统计指标
- id: 主键
- network/contract_address: 网络和合约
- metric_date/period: 日期和周期
- 交易统计: count/volume/avg_size
- Gas统计: price/used/fees
- 地址活跃度: active/new/dormant
- 大额交易: whale/large_transactions
```

## 🗂️ 元数据表

### `metadata_data_sources`
数据源配置表 - API端点、密钥、状态管理

### `metadata_symbols`
资产配置表 - 代币信息、合约地址、分类标签

### `metadata_data_quality`
数据质量表 - 质量评分、异常统计、问题追踪

## 🏪 存储引擎选择

### PostgreSQL (默认)
- **优势**: ACID事务、复杂查询、JSON支持
- **适用**: Clean Layer、Feature Layer、元数据
- **特点**: 关系型数据库，适合OLTP和复杂分析

### ClickHouse (可选)
- **优势**: 列式存储、高性能聚合、时间序列优化
- **适用**: 大规模时间序列数据、实时分析
- **特点**: OLAP数据库，适合大数据量分析

### MongoDB (可选)
- **优势**: 灵活schema、文档存储、水平扩展
- **适用**: Raw Layer原始数据存储
- **特点**: NoSQL数据库，适合半结构化数据

## 🔄 数据流设计

```
数据源 → Raw Layer → Clean Layer → Feature Layer
    ↓         ↓         ↓         ↓
 采集器 → 清洗器 → 聚合器 → 分析器
```

### 数据更新策略

#### 增量更新
- Raw Layer: 基于数据哈希去重
- Clean Layer: UPSERT操作，支持覆盖更新
- Feature Layer: 历史版本保留，支持重算

#### 历史重算
- 支持指定时间范围重新计算指标
- 版本控制，避免数据混乱
- 渐进式更新，减少计算压力

#### 多周期支持
- 分钟级K线: 1m, 5m, 15m, 30m
- 小时级K线: 1h, 4h
- 日线及以上: 1d, 1w, 1M
- 自动聚合生成高级别K线

## 📈 索引策略

### 时间序列索引
```sql
-- 时间范围查询优化
CREATE INDEX idx_symbol_timestamp ON clean_market_data(symbol, data_timestamp DESC);

-- 分区键索引 (ClickHouse)
ORDER BY (symbol, interval_type, data_timestamp)
PARTITION BY toYYYYMM(data_timestamp)
```

### 查询模式索引
```sql
-- 技术指标筛选
CREATE INDEX idx_rsi_signal ON feature_technical_indicators(rsi_14)
WHERE rsi_14 < 30 OR rsi_14 > 70;

-- 资产分类查询
CREATE INDEX idx_symbol_category ON metadata_symbols(category, is_active);
```

### 复合索引
```sql
-- 多维度查询优化
CREATE INDEX idx_kline_multi ON clean_kline_data(symbol, interval_type, interval_start DESC);
```

## 🔍 查询模式

### 实时查询
- 最新价格和指标
- 实时监控仪表板
- 警报触发条件

### 历史分析
- 回测数据准备
- 趋势分析和统计
- 相关性研究

### 批量处理
- 指标重算
- 数据质量检查
- 统计报表生成

## 🚀 性能优化

### 分区策略
- **时间分区**: 按月/日分割历史数据
- **资产分区**: 高频资产独立分区
- **自动清理**: TTL策略清理过期数据

### 缓存策略
- 热门资产数据缓存
- 计算结果缓存
- 元数据缓存

### 并发控制
- 读写分离部署
- 乐观锁机制
- 批量操作优化

## 📋 维护任务

### 日常维护
- 数据质量检查
- 索引重建优化
- 统计信息更新

### 定期清理
- 过期数据清理
- 重复数据去重
- 存储空间优化

### 监控告警
- 数据延迟监控
- 质量下降告警
- 性能指标监控

## 🔗 集成说明

### 数据接入
```python
# 存储原始数据
await storage.insert_raw_data(source_type, symbol, raw_data)

# 存储清洗数据
await storage.insert_clean_data(source_type, symbol, clean_data)

# 存储特征数据
await storage.insert_features(symbol, interval, features)
```

### 查询接口
```python
# 获取K线数据
klines = await storage.get_klines(symbol, interval, start_time, end_time)

# 获取技术指标
indicators = await storage.get_indicators(symbol, interval, indicator_list)

# 获取市场统计
stats = await storage.get_market_stats(symbol, period, stat_date)
```

这个数据库架构设计支持PredictLab从原型到生产的完整演进过程，既保证了数据的一致性和质量，又提供了优秀的查询性能和扩展性。
