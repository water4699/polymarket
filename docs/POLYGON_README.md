# Polygon Polymarket 数据抓取系统

## 🎯 功能概述

基于 Etherscan API V2 实现的 Polygon 链 Polymarket 交易数据抓取系统，支持：
- 从数据库 `etherscan_accounts` 表读取 API Keys（自动轮询，避免限额）
- 从 `data/` 目录 JSON 文件读取真实的 conditionId 和 tokenId
- 按 conditionId 或 tokenId 过滤 ERC-1155 TransferSingle 事件
- 线程安全，支持并发访问

## 🏗️ 核心组件

### 1. API Key 管理器 (`modules/api_key_manager.py`)
- 从数据库 `etherscan_accounts` 表读取 API Keys
- 支持多 Key 轮询，避免单 Key 限额
- 自动跟踪每日使用量
- 线程安全

### 2. 市场数据加载器 (`polygon.py`)
- 从 `data/polymarket_markets_*.json` 文件加载市场数据
- 提供 conditionId 和 tokenId 查询接口
- 支持市场搜索和过滤

### 3. Polygon 客户端 (`polygon.py`)
- 集成 Etherscan API V2 调用
- 支持 ERC-1155 TransferSingle 事件抓取
- 提供便捷的市场交易查询接口

## 🚀 快速开始

### 1. 初始化数据库和 API Keys

```bash
# 初始化 etherscan_accounts 表
python3 init_etherscan_accounts.py
```

编辑 `init_etherscan_accounts.py` 中的 `sample_keys` 列表，填入真实的 Polygonscan API Keys：

```python
sample_keys = [
    "YOUR_REAL_POLYGONSCAN_API_KEY_1",
    "YOUR_REAL_POLYGONSCAN_API_KEY_2",
]
```

### 2. 基本使用

```python
from polygon import PolygonClient

# 初始化客户端（自动从数据库读取 API Keys）
client = PolygonClient()

# 获取热门市场
popular_markets = client.get_popular_markets(limit=5)
for market in popular_markets:
    print(f"热门市场: {market['question'][:50]}...")

# 搜索特定市场
markets = client.market_loader.search_markets_by_question("Bitcoin")
if markets:
    market = markets[0]
    print(f"找到市场: {market['question']}")

    # 获取该市场的交易记录
    market_info, logs = client.get_market_logs(market['condition_id'], limit=10)
    print(f"获取到 {len(logs)} 条交易记录")

# 直接按 conditionId 获取交易
condition_id = "0xfc6260666d020a912a87d9000eff5116d2adfb8c30aba543427a4c1f1411f1a0"
logs = client.get_logs(condition_id=condition_id, limit=5)
print(f"ConditionId 交易记录: {len(logs)} 条")
```

## 📊 数据结构

### 市场数据 (从 JSON 文件加载)
```json
{
  "conditionId": "0xfc6260666d020a912a87d9000eff5116d2adfb8c30aba543427a4c1f1411f1a0",
  "question": "MegaETH market cap (FDV) >$2B one day after launch?",
  "clobTokenIds": "[\"tokenId1\", \"tokenId2\"]",
  "volume": "3586300.393843",
  "category": "Crypto"
}
```

### 交易记录 (API 返回)
```python
{
    'blockNumber': 12345678,
    'txHash': '0xabc123...',
    'timestamp': 1703123456,
    'from': '0xfrom_address',
    'to': '0xto_address',
    'conditionId': '0xcondition_id',
    'tokenId': 'big_integer_token_id',
    'value': 1000000
}
```

## 🔧 API 接口

### PolygonClient

#### `get_logs(condition_id=None, token_id=None, limit=20)`
获取 ERC-1155 TransferSingle 事件日志

**参数:**
- `condition_id`: 条件ID字符串 (如 "0x...")
- `token_id`: TokenId字符串
- `limit`: 返回记录数量限制

**返回:** 交易记录列表

#### `get_market_logs(market_query, limit=20)`
根据市场查询获取市场信息和交易记录

**参数:**
- `market_query`: 市场查询（conditionId 或问题关键词）
- `limit`: 返回记录数量限制

**返回:** (市场信息字典, 交易记录列表)

#### `get_popular_markets(limit=10)`
获取热门市场列表（按交易量排序）

#### `get_all_available_markets()`
获取所有可用市场

### MarketDataLoader

#### `get_market_by_condition_id(condition_id)`
根据 conditionId 获取市场信息

#### `get_token_ids_by_condition_id(condition_id)`
根据 conditionId 获取所有 tokenIds

#### `search_markets_by_question(keyword)`
根据问题关键词搜索市场

## ⚙️ 配置说明

### 环境变量 (.env)
```bash
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=predictlab
POSTGRES_USER=predictlab_user
POSTGRES_PASSWORD=your_password

# Polygon 配置
POLYGON_CHAIN_ID=137
POLYGONSCAN_V2_BASE_URL=https://api.etherscan.io/v2/api
```

### API Key 获取
1. 访问 [PolygonScan APIs](https://polygonscan.com/apis)
2. 注册账号并申请免费 API Key
3. 每日限额：5次/秒，100,000次/天
4. 在 `init_etherscan_accounts.py` 中配置多个 Key 实现轮询

## 🎯 使用场景

### 场景1：监控特定市场交易
```python
# 查找并监控比特币市场
markets = client.market_loader.search_markets_by_question("Bitcoin")
for market in markets:
    print(f"监控: {market['question']}")
    logs = client.get_logs(condition_id=market['condition_id'], limit=20)
    print(f"最新交易: {len(logs)} 条")
```

### 场景2：批量数据采集
```python
# 获取热门市场并采集所有交易数据
popular_markets = client.get_popular_markets(limit=10)

for market in popular_markets:
    token_ids = market.get('token_ids', [])
    for token_id in token_ids:
        logs = client.get_logs(token_id=str(token_id), limit=100)
        # 处理交易数据...
```

### 场景3：实时交易监控
```python
# 持续监控特定市场的交易
condition_id = "0x具体的condition_id"
while True:
    logs = client.get_logs(condition_id=condition_id, limit=5)
    if logs:
        for log in logs:
            print(f"新交易: {log['value']} 代币转移")
    time.sleep(60)  # 每分钟检查一次
```

## 🔍 故障排除

### 问题1：数据库连接失败
```
错误: role "predictlab_user" does not exist
```
**解决:** 检查数据库配置，确保 PostgreSQL 用户存在

### 问题2：没有 API Keys
```
API Keys数量: 0
```
**解决:** 运行 `python3 init_etherscan_accounts.py` 并填入真实 API Keys

### 问题3：API 调用限额
```
API 返回错误: api key rate limit
```
**解决:** 添加更多 API Keys 或等待限额重置

### 问题4：市场数据未加载
```
加载了 0 个市场数据
```
**解决:** 检查 `data/` 目录是否存在 JSON 文件

## 📈 性能优化

1. **API Key 轮询**: 自动切换 API Key，避免单点限额
2. **数据缓存**: 市场数据一次性加载到内存
3. **批量查询**: 支持一次获取多个交易记录
4. **错误重试**: 自动重试失败的 API 调用

## 🎉 特性

- ✅ **真实数据**: 使用 Polymarket 实际的 conditionId 和 tokenId
- ✅ **智能轮询**: API Key 自动轮询，避免限额中断
- ✅ **并发安全**: 线程安全的 API Key 管理
- ✅ **灵活查询**: 支持多种查询方式
- ✅ **错误处理**: 完善的错误处理和重试机制
- ✅ **易于扩展**: 模块化设计，易于添加新功能
