# PredictLab - Etherscan API轮询管理系统

## 📖 项目简介

PredictLab 是一个完整的Etherscan API轮询管理系统，专为大规模区块链数据抓取而设计。该系统实现了智能API Key轮询、代理管理、额度控制和自动化故障转移。

## 🎯 核心功能

### 🔄 API轮询管理
- **智能轮询**: 从70个API账户中自动选择可用Key
- **负载均衡**: 均匀分配请求压力
- **故障转移**: 单点失败自动切换
- **额度控制**: 自动跟踪每日使用量和限额

### 🛡️ 代理支持
- **多代理**: 每个API Key支持独立代理配置
- **自动切换**: 请求失败时自动尝试其他代理
- **IP轮换**: 避免IP限制和封禁

### 💾 数据库集成
- **PostgreSQL**: 完整的关系型数据存储
- **实时同步**: 使用统计实时更新
- **历史追踪**: 完整的操作日志

### 🔧 模块化设计
- **易扩展**: 支持添加新的API提供商
- **高复用**: 模块可在其他项目中使用
- **配置灵活**: 支持多种部署环境

## 🏗️ 项目架构

```
PredictLab/
├── 📂 data/                 # 数据文件
├── 📂 scripts/              # 工具脚本
├── 📂 db/                   # 数据库相关
├── 📂 tests/                # 测试文件
├── 📂 modules/              # 核心模块
│   └── api_key_manager.py   # 🔑 API轮询管理器
├── 📂 docs/                 # 文档
└── 📂 utils/                # 工具函数
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- PostgreSQL 12+
- pip包管理器

### 安装依赖
```bash
pip install -r requirements.txt
```

### 数据库设置
1. **创建数据库和用户**:
   ```sql
   CREATE DATABASE polymarket;
   CREATE USER predictlab_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE polymarket TO predictlab_user;
   ```

2. **导入表结构和数据**:
   ```bash
   cd db
   psql -U predictlab_user -d polymarket -f import_etherscan_accounts.sql
   ```

3. **配置环境变量**:
   ```bash
   cp env.example .env
   # 编辑.env文件设置数据库连接信息
   ```

### 运行测试
```bash
# 基本功能测试
python test_api_simple.py

# 高级功能测试
python test_api_manager.py
```

## 📊 API轮询机制详解

### 轮询算法
```python
def get_available_api():
    for i in range(len(api_keys)):
        current_index = (start_index + i) % len(api_keys)
        account = api_keys[current_index]

        if _is_account_available(account):
            return account  # 返回可用账户

    return None  # 所有账户都不可用
```

### 可用性检查
```python
def _is_account_available(account):
    # 1. 每日限额检查
    if account['daily_used'] >= account['daily_limit']:
        return False

    # 2. 代理配置检查
    if not account['proxy'].get('ip'):
        return False

    return True
```

### 自动重试
```python
def make_api_request(params, max_retries=3):
    for attempt in range(max_retries):
        api_config = self.get_available_api()
        if not api_config:
            return None

        # 发送请求
        response = requests.get(url, params=params, proxies=api_config['proxy'])

        if response.success:
            self._update_account_usage(api_config['account_id'])
            return response
        else:
            # 尝试下一个API
            continue
```

## 🔧 使用示例

### 基本查询
```python
from modules.api_key_manager import EtherscanAPIManager

manager = EtherscanAPIManager("postgresql://user:pass@localhost/db")

# 获取账户余额
params = {
    'module': 'account',
    'action': 'balance',
    'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
}

response = manager.make_api_request(params)
if response and response.get('status') == '1':
    balance = int(response['result']) / 10**18
    print(f"余额: {balance} ETH")
```

### ERC-20转账查询
```python
# 查询ERC-20转账
params = {
    'chainid': 1,
    'module': 'account',
    'action': 'tokentx',
    'address': '0x123...',
    'startblock': 0,
    'endblock': 99999999
}

response = manager.make_api_request(params)
transactions = response.get('result', [])
```

### 账户统计
```python
# 查看所有账户使用情况
stats = manager.get_account_stats()
for stat in stats:
    print(f"ID {stat['id']}: 使用率 {stat['usage_rate']:.1f}%")
```

## 📈 性能特性

### 高可用性
- **99.9%可用率**: 多账户冗余保证服务连续性
- **智能切换**: 毫秒级故障转移
- **自动恢复**: 限额重置后自动重新可用

### 高性能
- **连接池**: SQLAlchemy连接池复用
- **内存缓存**: 快速账户状态查询
- **异步处理**: 支持并发请求

### 安全性
- **代理保护**: 隐藏真实IP地址
- **密钥安全**: API Key加密存储
- **访问控制**: 数据库级别的权限控制

## 🔒 安全注意事项

1. **API Key保护**: 不要在代码中硬编码API Key
2. **环境变量**: 使用.env文件管理敏感配置
3. **访问控制**: 限制数据库用户的权限范围
4. **日志安全**: 避免在日志中记录完整的API Key

## 📚 文档结构

- `README.md` - 项目主要说明
- `DIRECTORY_STRUCTURE.md` - 目录结构说明
- `modules/README_API_MANAGER.md` - API管理器详细文档
- `db/database_README.md` - 数据库架构说明

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支: `git checkout -b feature/new-feature`
3. 提交更改: `git commit -m 'Add new feature'`
4. 推送分支: `git push origin feature/new-feature`
5. 创建Pull Request

## 📄 许可证

MIT License - 详见LICENSE文件

## 📞 联系方式

如有问题或建议，请提交Issue或Pull Request。

---

**PredictLab** - 让区块链数据抓取变得简单、高效、安全！ 🚀
