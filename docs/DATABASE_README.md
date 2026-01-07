# Polymarket数据库设计与使用指南

## 📋 概述

本项目提供了完整的Polymarket预测市场数据存储解决方案，包括数据库表设计、数据导入脚本和使用示例。

## 🏗️ 数据库表结构

### 核心表说明

#### 1. `markets` - 市场基本信息表
存储预测市场的核心信息，是整个数据库的核心表。

**关键字段：**
- `id`: 市场唯一标识
- `question`: 预测问题
- `condition_id`: 区块链条件ID
- `category`: 分类（Sports/Crypto/Politics）
- `volume`: 交易量
- `liquidity`: 流动性
- `active/closed`: 状态标识

#### 2. `market_outcomes` - 市场结果选项表
存储每个市场的预测结果选项（如Yes/No）。

#### 3. `market_events` - 市场事件表
存储市场相关的Polymarket事件信息。

#### 4. `contract_addresses` - 合约地址表
存储区块链合约地址信息。

#### 5. `clob_token_ids` - CLOB代币ID表
存储去中心化订单簿的代币ID，用于区块链查询。

#### 6. `market_rewards` - 市场奖励表
存储市场奖励机制信息。

#### 7. `data_files` - 数据文件元数据表
记录导入的数据文件信息。

#### 8. `raw_json_data` - 原始JSON数据存储表 ⭐ **新增**
完整存储原始JSON文件内容，支持数据追溯和完整性验证。

**关键字段：**
- `filename`: 文件名
- `metadata_json`: 元数据JSON字符串
- `markets_json`: 市场数据JSON字符串
- `file_size_bytes`: 原始文件大小
- `compression_type`: 压缩类型

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install psycopg2-binary

# 创建PostgreSQL数据库
createdb polymarket
```

### 2. 创建表结构

```bash
# 运行表创建脚本
psql -d polymarket -f polymarket_db_schema.sql
```

### 3. 导入数据

```python
# 运行导入脚本
python3 import_polymarket_data.py
```

### 4. 测试原始JSON存储 ⭐

```python
# 运行测试脚本验证原始JSON存储功能
python3 test_raw_json_storage.py
```

## 📊 数据表关系

```
markets (1) ──── (N) market_outcomes
    │
    ├── (N) market_events
    │
    ├── (1) contract_addresses
    │
    ├── (N) clob_token_ids
    │
    └── (N) market_rewards

raw_json_data (1) ──── (1) data_files
```

## 🔍 查询示例

### 查询活跃市场

```sql
SELECT id, question, category, volume, liquidity
FROM markets
WHERE active = TRUE AND closed = FALSE
ORDER BY volume DESC
LIMIT 10;
```

### 查询特定分类的市场

```sql
SELECT * FROM markets
WHERE category = 'Crypto'
ORDER BY created_at DESC;
```

### 查询代币ID（用于区块链查询）

```sql
SELECT m.question, c.token_id, c.outcome_text
FROM markets m
JOIN clob_token_ids c ON m.id = c.market_id
WHERE m.category = 'Sports'
ORDER BY m.id, c.token_index;
```

### 查询高交易量市场

```sql
SELECT * FROM high_liquidity_markets
WHERE category = 'Politics';
```

## 📈 性能优化

### 索引说明

- 主要查询字段都建立了索引
- 支持按分类、状态、时间范围查询
- 外键约束确保数据完整性

### 视图说明

- `active_markets`: 活跃市场视图
- `high_liquidity_markets`: 高流动性市场视图
- `recently_closed_markets`: 近期结束市场视图

## 🛠️ 维护脚本

### 数据更新

```python
from import_polymarket_data import PolymarketDataImporter

importer = PolymarketDataImporter()
importer.connect()
# 导入新数据文件
importer.import_file('data/new_markets.json', 'Crypto')
importer.disconnect()
```

### 数据清理

```sql
-- 删除过期数据
DELETE FROM markets WHERE end_date < NOW() - INTERVAL '1 year';

-- 清理重复数据
DELETE FROM market_outcomes a USING market_outcomes b
WHERE a.id < b.id AND a.market_id = b.market_id AND a.outcome_index = b.outcome_index;
```

## 📊 数据统计

### 市场统计

```sql
-- 各分类市场数量
SELECT category, COUNT(*) as market_count
FROM markets
GROUP BY category
ORDER BY market_count DESC;

-- 平均交易量统计
SELECT category,
       AVG(volume) as avg_volume,
       MAX(volume) as max_volume,
       MIN(volume) as min_volume
FROM markets
WHERE volume > 0
GROUP BY category;
```

### 区块链数据统计

```sql
-- 唯一合约地址统计
SELECT 'conditional_tokens' as contract_type, COUNT(DISTINCT conditional_tokens) as unique_count
FROM contract_addresses
WHERE conditional_tokens IS NOT NULL
UNION ALL
SELECT 'clob_exchange' as contract_type, COUNT(DISTINCT clob_exchange) as unique_count
FROM contract_addresses
WHERE clob_exchange IS NOT NULL;
```

## 🔧 配置说明

### 数据库配置

```python
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'polymarket',
    'user': 'your_username',
    'password': 'your_password'
}
```

### 环境变量

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=polymarket
export DB_USER=postgres
export DB_PASSWORD=your_password
```

## 🐛 故障排除

### 常见问题

1. **连接失败**
   - 检查PostgreSQL服务是否运行
   - 验证用户名和密码
   - 确认数据库存在

2. **导入失败**
   - 检查JSON文件格式
   - 验证数据类型匹配
   - 查看错误日志详情

3. **查询性能慢**
   - 检查是否建立了必要的索引
   - 考虑添加复合索引
   - 使用EXPLAIN ANALYZE分析查询

## 📚 API参考

### PolymarketDataImporter类

```python
class PolymarketDataImporter:
    def __init__(self, db_config=None)        # 初始化
    def connect(self)                         # 连接数据库
    def disconnect(self)                      # 断开连接
    def create_tables(self)                   # 创建表结构
    def import_file(self, file_path, category) # 导入单个文件
    def import_all_files(self)               # 导入所有文件
```

## 🔄 数据更新策略

### 增量更新

1. 下载新的JSON数据文件
2. 运行导入脚本（会自动处理重复数据）
3. 更新统计信息

### 定期维护

- 每周清理过期数据
- 每月重建索引
- 每季度归档历史数据

## 📞 技术支持

如有问题，请检查：
1. 数据库连接配置
2. 数据文件格式
3. 错误日志信息
4. 表结构完整性

## 🗄️ 原始JSON数据存储 ⭐

### 设计目的

- **数据追溯**: 保存完整的原始数据，支持审计和追溯
- **完整性验证**: 对比结构化数据和原始数据的一致性
- **数据恢复**: 从原始JSON重建结构化数据
- **历史版本**: 保留数据演变的历史记录

### 核心特性

- **完整存储**: 保留原始JSON文件的完整内容
- **分类管理**: 按Sports/Crypto/Politics分类存储
- **元数据记录**: 文件大小、时间戳、处理状态
- **高效查询**: 支持按文件名、分类、时间范围查询

### 查询原始JSON数据

```sql
-- 查看所有存储的原始JSON文件
SELECT filename, category, total_markets, file_size_bytes,
       stored_at, last_updated
FROM raw_json_data
ORDER BY stored_at DESC;

-- 检索特定文件的原始数据
SELECT metadata_json, markets_json
FROM raw_json_data
WHERE filename = 'polymarket_markets_Sports_20260106_162432.json';

-- 按分类统计存储情况
SELECT category,
       COUNT(*) as file_count,
       SUM(file_size_bytes) as total_size,
       AVG(total_markets) as avg_markets_per_file
FROM raw_json_data
GROUP BY category
ORDER BY file_count DESC;
```

### 数据完整性验证

```sql
-- 对比结构化数据和原始JSON的一致性
SELECT
    r.filename,
    r.category,
    r.total_markets as json_markets_count,
    COUNT(m.id) as structured_markets_count,
    CASE WHEN r.total_markets = COUNT(m.id) THEN '✅ 一致'
         ELSE '❌ 不一致' END as integrity_status
FROM raw_json_data r
LEFT JOIN markets m ON m.category = r.category
GROUP BY r.filename, r.category, r.total_markets
ORDER BY r.stored_at DESC;
```

---

**注意**: 本数据库设计针对Polymarket数据的特点进行了优化，如有特殊需求可根据实际情况调整表结构。原始JSON存储功能确保数据的完整追溯性。
