# PredictLab 数据库快速开始指南

## 🚀 快速设置

### 1. 环境准备
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量 (复制并编辑)
cp env.example .env
# 编辑 .env 文件，配置数据库连接
```

### 2. 初始化数据库
```bash
# 创建所有表结构
python init_database.py

# 验证表创建
python init_database.py --verify-only
```

### 3. 数据管理操作
```bash
# 迁移原始数据到清洗层
python data_manager.py migrate --source-type predict --symbol BTC_PRICE --days 30

# 生成K线数据
python data_manager.py klines --symbol BTC_PRICE

# 重算技术指标
python data_manager.py indicators --symbol BTC_PRICE --interval 1h

# 清理过期数据
python data_manager.py cleanup --days 90
```

## 📊 数据流示例

### 1. 插入原始数据
```python
from modules.data_storage.postgres_storage import PostgresStorage

storage = PostgresStorage()
await storage.connect()

# 插入原始市场数据
raw_data = {
    "price": 45000.50,
    "volume": 1234567.89,
    "timestamp": "2024-01-01T12:00:00Z"
}
await storage.insert_raw_market_data("predict", "BTC_PRICE", datetime.now(), raw_data)
```

### 2. 查询清洗后的数据
```python
# 查询最新价格
latest_price = await storage.get_latest_price("BTC_PRICE")
print(f"BTC 最新价格: {latest_price}")

# 查询K线数据
klines = await storage.get_klines("BTC_PRICE", "1h", start_time, end_time)
print(f"获取到 {len(klines)} 条K线数据")
```

### 3. 获取技术指标
```python
# 获取技术指标
indicators = await storage.get_technical_indicators(
    "BTC_PRICE", "1h", start_time, end_time,
    ["rsi_14", "macd_line", "sma_20"]
)
print(f"技术指标数据: {len(indicators)} 条")
```

## 🔍 查询示例

### 基础查询
```sql
-- 最新市场数据
SELECT * FROM clean_market_data
WHERE symbol = 'BTC_PRICE'
ORDER BY data_timestamp DESC
LIMIT 10;

-- 技术指标筛选
SELECT * FROM feature_technical_indicators
WHERE symbol = 'BTC_PRICE'
  AND rsi_14 < 30  -- 超卖信号
  AND data_timestamp >= CURRENT_DATE - INTERVAL '7 days';
```

### 聚合查询
```sql
-- 日K线聚合
SELECT
    DATE(interval_start) as date,
    MIN(low_price) as low,
    MAX(high_price) as high,
    SUM(volume) as volume
FROM clean_kline_data
WHERE symbol = 'BTC_PRICE' AND interval_type = '1h'
GROUP BY DATE(interval_start)
ORDER BY date DESC;

-- 波动率计算
SELECT
    symbol,
    DATE(data_timestamp) as date,
    STDDEV(close_price) as volatility
FROM clean_kline_data
WHERE interval_type = '1h'
GROUP BY symbol, DATE(data_timestamp);
```

## 🏗️ 架构优势

### 分层设计
- **Raw Layer**: 数据审计和重处理
- **Clean Layer**: 业务查询和分析
- **Feature Layer**: 高级指标和统计

### 性能优化
- 时间序列索引优化查询
- 分区表支持大数据量
- 支持 PostgreSQL 和 ClickHouse

### 数据质量
- 数据哈希去重机制
- 质量评分系统
- 异常检测和标记

## 📈 扩展指南

### 添加新数据源
1. 在 `metadata_data_sources` 表中添加配置
2. 实现对应的数据采集逻辑
3. 更新清洗规则

### 添加新指标
1. 在 `feature_technical_indicators` 表中添加字段
2. 实现指标计算逻辑
3. 更新查询接口

### 性能调优
- 定期重建索引
- 监控查询性能
- 考虑分区策略

## 🔧 维护任务

### 日常维护
```bash
# 每周执行
python data_manager.py migrate  # 数据迁移
python data_manager.py indicators  # 指标重算

# 每月执行
python data_manager.py cleanup --days 90  # 清理过期数据
```

### 监控检查
```sql
-- 数据质量监控
SELECT
    table_name,
    check_date,
    quality_score,
    record_count
FROM metadata_data_quality
WHERE check_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY quality_score ASC;

-- 数据新鲜度检查
SELECT
    'raw_market_data' as table_name,
    MAX(fetch_timestamp) as latest_data,
    NOW() - MAX(fetch_timestamp) as age
FROM raw_market_data

UNION ALL

SELECT
    'clean_market_data' as table_name,
    MAX(updated_at) as latest_data,
    NOW() - MAX(updated_at) as age
FROM clean_market_data;
```

这个数据库架构提供了从原型到生产的完整数据管理解决方案！ 🎯
