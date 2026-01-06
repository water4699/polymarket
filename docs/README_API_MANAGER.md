# Etherscan API Key 管理器

## 📖 概述

`EtherscanAPIManager` 是一个完整的API Key轮询管理器，支持：

- 🔄 **自动轮询**: 从数据库自动加载所有API Keys
- 🛡️ **代理支持**: 每个API Key可配置独立代理
- 📊 **额度管理**: 自动跟踪每日使用量和限额
- 🔄 **故障转移**: API失败时自动切换到下一个可用Key
- 💾 **数据库同步**: 自动更新使用统计到数据库
- 🎯 **易于集成**: 简单易用的接口

## 🏗️ 架构设计

### 数据库表结构

```sql
CREATE TABLE etherscan_accounts (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    proxy_ip VARCHAR(50),
    proxy_port VARCHAR(10),
    proxy_user VARCHAR(50),
    proxy_pass VARCHAR(50),
    daily_used INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 100000,
    last_used TIMESTAMP
);
```

### 类结构

```python
class EtherscanAPIManager:
    def __init__(self, db_url: str)
    def get_available_api() -> Optional[Dict]
    def make_api_request(params: Dict) -> Optional[Dict]
    def get_account_stats() -> List[Dict]
```

## 🚀 快速开始

### 1. 初始化管理器

```python
from modules.api_key_manager import EtherscanAPIManager

# 使用配置文件中的数据库连接
manager = EtherscanAPIManager(config.postgres_url)
```

### 2. 基本使用

```python
# 获取可用API配置
api_config = manager.get_available_api()
if api_config:
    print(f"API Key: {api_config['api_key']}")
    print(f"代理: {api_config['proxy']}")

# 发送API请求（自动轮询）
params = {
    'chainid': 1,
    'module': 'account',
    'action': 'balance',
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
}

response = manager.make_api_request(params)
if response and response.get('status') == '1':
    balance = int(response['result']) / 10**18
    print(f"余额: {balance} ETH")
```

### 3. 查看统计

```python
stats = manager.get_account_stats()
for stat in stats:
    print(f"ID {stat['id']}: 使用率 {stat['usage_rate']:.1f}%")
```

## 🔧 核心功能

### API轮询逻辑

1. **加载所有账户**: 从数据库加载所有API Keys
2. **检查可用性**: 验证每日限额和代理配置
3. **轮询选择**: 从当前位置开始循环查找可用API
4. **自动切换**: 失败时自动切换到下一个API
5. **状态更新**: 成功后更新使用统计

### 代理配置

```python
# 代理配置格式
proxy_config = {
    'ip': '192.168.1.1',
    'port': '8080',
    'user': 'username',
    'pass': 'password'
}

# 自动转换为requests代理格式
proxies = {
    'http': 'http://username:password@192.168.1.1:8080',
    'https': 'http://username:password@192.168.1.1:8080'
}
```

### 额度管理

- **每日重置**: 自动检测新日期并重置使用量
- **限额检查**: 避免超出API提供商的限制
- **实时更新**: 每次请求成功后更新计数
- **智能切换**: 额度不足时自动切换到其他API

## 📊 使用示例

### 在数据抓取中使用

```python
from modules.api_key_manager import EtherscanAPIManager

class ERC20TransactionCrawler:
    def __init__(self):
        self.api_manager = EtherscanAPIManager(config.postgres_url)

    def get_token_transfers(self, contract_address: str, start_block: int):
        """获取ERC20转账记录"""
        params = {
            'chainid': 1,
            'module': 'account',
            'action': 'tokentx',
            'contractaddress': contract_address,
            'startblock': start_block,
            'sort': 'asc'
        }

        response = self.api_manager.make_api_request(params)
        if response and response.get('status') == '1':
            return response.get('result', [])
        return []
```

### 批量处理优化

```python
def batch_process_addresses(addresses: List[str]):
    """批量处理多个地址"""
    manager = EtherscanAPIManager(config.postgres_url)
    results = []

    for address in addresses:
        # 自动使用可用API
        params = {
            'chainid': 1,
            'module': 'account',
            'action': 'balance',
            'address': address
        }

        response = manager.make_api_request(params)
        if response:
            results.append({
                'address': address,
                'balance': response.get('result', '0')
            })

        # 小延迟避免请求过快
        time.sleep(0.1)

    return results
```

## 🧪 测试

运行测试脚本：

```bash
python test_api_manager.py
```

测试内容包括：
- ✅ API管理器初始化
- ✅ 数据库连接检查
- ✅ API轮询功能
- ✅ 真实API请求
- ✅ 统计信息查询

## ⚙️ 配置选项

### 初始化参数

```python
manager = EtherscanAPIManager(
    db_url="postgresql://user:pass@localhost/dbname"
)
```

### 默认配置

- `base_url`: "https://api.etherscan.io/v2/api"
- `request_timeout`: 30秒
- `daily_limit`: 100,000次/天

## 🔍 故障排除

### 常见问题

1. **没有可用API**
   - 检查数据库中是否有账户记录
   - 确认API Keys是否正确
   - 查看每日限额是否已用完

2. **数据库连接失败**
   - 检查PostgreSQL服务是否运行
   - 确认连接字符串正确
   - 验证用户权限

3. **代理连接失败**
   - 检查代理服务器是否可用
   - 确认代理认证信息正确
   - 考虑使用无代理模式

### 日志调试

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 查看详细的轮询和请求日志
manager = EtherscanAPIManager(db_url)
```

## 📈 性能优化

### 连接池

- 使用SQLAlchemy连接池复用数据库连接
- 自动管理连接生命周期

### 缓存策略

- 内存缓存账户信息
- 定期刷新数据库数据
- 智能跳过已耗尽的API

### 并发安全

- 线程安全的轮询逻辑
- 原子性数据库更新
- 避免竞态条件

## 🔄 扩展功能

### 添加新API提供商

```python
class CustomAPIManager(EtherscanAPIManager):
    def __init__(self, db_url):
        super().__init__(db_url)
        self.base_url = "https://custom-api.com/v1"

    def _is_account_available(self, account):
        # 自定义可用性检查逻辑
        return super()._is_account_available(account) and custom_check(account)
```

### 自定义额度策略

```python
def set_custom_limits(manager, account_id, new_limit):
    """设置自定义限额"""
    session = manager.SessionLocal()
    try:
        session.execute(text("""
            UPDATE etherscan_accounts
            SET daily_limit = :limit
            WHERE id = :account_id
        """), {'limit': new_limit, 'account_id': account_id})
        session.commit()
    finally:
        session.close()
```

## 📋 API参考

### EtherscanAPIManager

#### 方法

- `__init__(db_url: str)` - 初始化管理器
- `get_available_api() -> Optional[Dict]` - 获取可用API配置
- `make_api_request(params: Dict) -> Optional[Dict]` - 发送API请求
- `get_account_stats() -> List[Dict]` - 获取账户统计
- `_load_api_keys()` - 重新加载API Keys
- `_update_account_usage(account_id: int)` - 更新使用统计

#### 返回格式

**get_available_api()**:
```python
{
    'api_key': 'API_KEY_STRING',
    'proxy': {'http': 'proxy_url', 'https': 'proxy_url'} or None,
    'account_id': 123
}
```

**make_api_request()**:
```python
{
    'status': '1',
    'message': 'OK',
    'result': 'API_RESPONSE_DATA'
}
```

## 🎯 最佳实践

1. **初始化时机**: 在应用启动时创建单一管理器实例
2. **错误处理**: 总是检查API请求的返回值
3. **监控告警**: 定期检查账户使用率和错误率
4. **备份策略**: 准备多个备用API Key
5. **速率控制**: 在循环请求间添加适当延迟

这个API管理器为大规模数据抓取提供了稳定可靠的基础设施支持！🚀
