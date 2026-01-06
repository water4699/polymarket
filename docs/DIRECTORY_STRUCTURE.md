# PredictLab 项目目录结构

## 📂 目录结构说明

```
PredictLab/
├── 📄 根目录文件
│   ├── main.py                 # 🚀 主程序入口
│   ├── config.py               # ⚙️ 全局配置文件
│   ├── test.py                 # 🧪 主测试文件
│   ├── requirements.txt        # 📦 Python依赖
│   ├── pytest.ini             # 🧪 测试配置
│   ├── alembic.ini            # 🗄️ 数据库迁移配置
│   ├── README.md              # 📖 项目说明
│   └── .env                   # 🔐 环境变量配置
│
├── 🗂️ data/                   # 📊 数据文件目录
│   └── etherscan 副本.csv     # Etherscan API账户数据
│
├── 🗂️ scripts/                # 🛠️ 脚本工具目录
│   ├── install_dependencies.py # 依赖安装脚本
│   ├── run_tests.py           # 测试运行脚本
│   ├── refactor_project.py    # 项目重构脚本
│   └── verify_refactor.py     # 重构验证脚本
│
├── 🗂️ db/                     # 🗄️ 数据库相关
│   ├── database_schema.sql    # 数据库表结构
│   ├── database_examples.sql  # SQL查询示例
│   ├── import_etherscan_accounts.sql # 数据导入脚本
│   ├── init_database.py       # 数据库初始化
│   ├── data_manager.py        # 数据管理器
│   ├── migration_manager.py   # 迁移管理
│   ├── alembic/               # Alembic迁移工具
│   └── logs/                  # 数据库日志
│
├── 🗂️ tests/                  # 🧪 测试文件目录
│   ├── conftest.py            # 测试配置
│   ├── test_utils.py          # 测试工具
│   ├── simple_test.py         # 简单测试
│   ├── test_rpc_node.py       # RPC节点测试
│   ├── fixtures/              # 测试固件
│   ├── integration/           # 集成测试
│   └── unit/                  # 单元测试
│
├── 🗂️ modules/                # 🏗️ 核心模块
│   ├── data_source/           # 📡 数据源模块
│   ├── data_processing/       # 🔄 数据处理模块
│   ├── data_storage/          # 💾 数据存储模块
│   ├── analysis/              # 📈 分析模块
│   └── scheduler/             # ⏰ 调度模块
│
├── 🗂️ docs/                   # 📚 文档目录
│   ├── database_README.md     # 数据库文档
│   └── scheduler_README.md    # 调度器文档
│
├── 🗂️ examples/               # 💡 示例代码
│   ├── pipeline_demo.py       # 管道演示
│   └── quality_monitor_demo.py # 质量监控演示
│
├── 🗂️ utils/                  # 🔧 工具模块
│   ├── logger.py              # 日志工具
│   ├── error_handler.py       # 错误处理
│   ├── exceptions.py          # 自定义异常
│   └── __init__.py
│
└── 🗂️ backup_before_refactor/ # 📦 重构前备份
```

## 📋 文件分类规则

### 🚀 核心文件（根目录）
- 主程序入口：`main.py`
- 全局配置：`config.py`
- 环境配置：`.env`, `requirements.txt`

### 📊 数据文件（data/）
- CSV数据文件
- JSON数据文件
- 原始数据文件

### 🛠️ 脚本文件（scripts/）
- 安装脚本
- 构建脚本
- 维护脚本
- 工具脚本

### 🗄️ 数据库文件（db/）
- 表结构定义
- 迁移脚本
- 初始化脚本
- 数据导入脚本

### 🧪 测试文件（tests/）
- 单元测试
- 集成测试
- 测试配置
- 测试工具

### 📚 文档文件（docs/）
- README文件
- API文档
- 使用指南
- 架构说明

## 🧹 清理说明

### ✅ 已清理的文件
- `import_accounts_direct.py` - 临时导入脚本
- `import_etherscan_accounts.py` - 临时导入脚本
- `setup_database.py` - 数据库设置脚本
- `test_db_connection.py` - 连接测试脚本
- `test_postgres_only.py` - PostgreSQL测试脚本

### 📁 文件移动记录
- `etherscan 副本.csv` → `data/etherscan 副本.csv`
- `import_etherscan_accounts.sql` → `db/import_etherscan_accounts.sql`
- `install_dependencies.py` → `scripts/install_dependencies.py`
- `run_tests.py` → `scripts/run_tests.py`
- `refactor_project.py` → `scripts/refactor_project.py`
- `verify_refactor.py` → `scripts/verify_refactor.py`
- `simple_test.py` → `tests/simple_test.py`
- `test_rpc_node.py` → `tests/test_rpc_node.py`

## 🎯 使用指南

### 运行主程序
```bash
python main.py
```

### 运行测试
```bash
python scripts/run_tests.py
```

### 数据库操作
```bash
cd db
python init_database.py
psql -U predictlab_user -d polymarket -f import_etherscan_accounts.sql
```

### 安装依赖
```bash
python scripts/install_dependencies.py
```

现在项目结构清晰有序，各文件各司其职！🎉
