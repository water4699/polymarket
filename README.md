# PredictLab 原型版本

一个精简的数据分析平台原型，适合快速迭代开发。保留核心功能，简化分析工具。

## 项目结构

```
PredictLab/
├── modules/
│   ├── data_source/          # 数据源模块 (核心)
│   │   ├── base.py          # 数据源基类
│   │   ├── predict_source.py    # Predict API
│   │   ├── polymarket_source.py # Polymarket API
│   │   ├── onchain_source.py    # 区块链数据
│   │   └── dune_source.py       # Dune Analytics
│   ├── data_storage/         # 数据存储模块 (核心)
│   │   ├── base.py          # 存储基类
│   │   ├── postgres_storage.py  # PostgreSQL
│   │   └── mongo_storage.py     # MongoDB
│   ├── data_processing/      # 数据处理模块 (核心)
│   │   ├── data_cleaner.py      # 数据清洗
│   │   └── kline_generator.py   # K线生成
│   └── analysis/            # 简化分析工具
│       └── simple_analyzer.py   # 策略/图表/调度
├── utils/                    # 工具模块
│   └── logger.py            # 日志工具
├── config.py                # 配置文件
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖文件
├── env.example             # 配置示例
└── README.md               # 说明文档
```

## 核心功能

### 🔍 数据采集 (Data Source)
- **Predict API**: 预测市场数据
- **Polymarket API**: Polymarket 预测市场
- **OnChain Data**: 区块链交易数据
- **Dune Analytics**: 区块链分析查询

### 💾 数据存储 (Data Storage)
- **PostgreSQL**: 结构化数据存储
- **MongoDB**: 非结构化数据存储
- **三层架构**: Raw/Clean/Feature 数据分层
- **数据库迁移**: Alembic 版本控制和迁移管理

### 🔧 数据处理 (Data Processing)
- **数据清洗**: 缺失值、异常值处理
- **K线生成**: 多时间间隔K线数据
- **技术指标**: 移动平均线等基础指标

### 📊 简化分析 (Analysis)
- **简单策略**: 基础移动平均线策略
- **快速回测**: 简化的收益计算
- **文本图表**: ASCII价格走势图
- **任务调度**: 基础定时任务支持

### 🔄 任务调度 (Scheduler)
- **异步管道**: 支持完整的处理流程
- **依赖管理**: 自动处理任务依赖关系
- **错误重试**: 内置失败重试和错误隔离
- **并发控制**: 可配置的并发执行
- **状态监控**: 实时执行状态跟踪

### 🔍 数据校验 (Validation)
- **多层校验**: Raw/Clean/Feature数据质量检查
- **增量验证**: 保证更新和重算的数据一致性
- **质量监控**: 实时监控和告警系统
- **报告生成**: 支持多种格式的质量报告
- **自动化修复**: 提供数据问题的修复建议

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
# 方法1: 使用迁移系统 (推荐)
python migration_quickstart.py

# 方法2: 直接创建表结构
python init_database.py

# 验证表创建
python init_database.py --verify-only
```

### 3. 运行快速演示
```bash
python main.py --demo
```

### 4. 运行异步数据管道
```bash
# 完整数据管道 (采集→清洗→存储→K线→回测→可视化)
python main.py --pipeline --concurrent 3

# 运行到指定阶段
python main.py --pipeline-stage kline --symbols BTC_PRICE

# 运行管道演示
python pipeline_demo.py

# 运行质量监控演示
python quality_monitor_demo.py
```

### 5. 数据管理操作
```bash
# 迁移原始数据到清洗层
python data_manager.py migrate --source-type predict --symbol BTC_PRICE

# 生成K线数据
python data_manager.py klines --symbol BTC_PRICE

# 重算技术指标
python data_manager.py indicators --symbol BTC_PRICE --interval 1h

# 数据一致性校验
python data_manager.py validate --symbol BTC_PRICE --data-type all

# 增量更新安全检查
python data_manager.py safety_check --symbol BTC_PRICE --data-type clean
```

### 6. 查看可用组件
```bash
python main.py --components

# 健康检查
python main.py --health
```

## 使用示例

### 快速演示输出
```
============================================================
PredictLab 原型演示结果
============================================================

📊 数据概览:
   数据源: mock
   原始数据: 720 行
   清洗后: 720 行
   K线数据: 30 条

📈 回测结果:
   策略: simple_ma
   初始资金: 10000.00
   最终价值: 10523.45
   总收益率: 5.23%
   交易次数: 8

📋 分析图表:
=== 价格走势 ===

价格统计:
- 起始价格: 50000.00
- 结束价格: 51234.56
- 最高价格: 52345.67
- 最低价格: 48765.43
- 涨跌幅: 2.47%

数据点数: 30
时间范围: ... 到 ...

价格走势简图:
50000 | ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
      |█▆▇▆▅▆▇▅▆▇▆▅▆▇▅▆▇▆▅▆▇▅▆▇▆▅▆▇▅▆▇▆▅▆▇▅▆▇▆▅▆▇▅█
      |██████████████████████████████████████████████████
      |██████████████████████████████████████████████████
```

## 核心接口

### 数据源使用
```python
from modules.data_source.predict_source import PredictDataSource

ds = PredictDataSource()
await ds.connect()
data = await ds.fetch_data("BTC_PRICE", start_time, end_time)
```

### 数据存储使用
```python
from modules.data_storage.mongo_storage import MongoStorage

storage = MongoStorage()
await storage.connect()
await storage.insert_data("collection", data)
```

### 数据处理使用
```python
from modules.data_processing.data_cleaner import DataCleaner
from modules.data_processing.kline_generator import KlineGenerator

cleaner = DataCleaner()
kline_gen = KlineGenerator()

clean_data = cleaner.clean_market_data(raw_data)
klines = kline_gen.generate_klines(clean_data, interval='1h')
```

### 简化分析使用
```python
from modules.analysis.simple_analyzer import (
    SimpleStrategy, SimpleBacktester, SimpleChartGenerator
)

strategy = SimpleStrategy()
backtester = SimpleBacktester()
chart_gen = SimpleChartGenerator()

result = backtester.run_backtest(klines, strategy)
chart = chart_gen.plot_price_chart(klines)
```

### 异步任务调度
```python
from modules.scheduler.task_scheduler import DataPipelineScheduler

# 创建调度器
scheduler = DataPipelineScheduler()

# 配置数据管道
pipeline_config = {
    'symbols': ['BTC_PRICE', 'ETH_PRICE'],
    'source_types': ['predict'],
    'intervals': ['1h', '1d'],
    'days_back': 7
}

# 创建并执行管道
scheduler.create_data_pipeline(pipeline_config)
results = await scheduler.execute_pipeline(max_concurrent=3)

# 查看执行状态
status = scheduler.get_pipeline_status()
print(f"进度: {status['progress']:.1%}")
```

## 配置说明

创建 `.env` 文件配置API密钥（可选，原型版本支持模拟数据）:

```env
# 可选：真实API配置
PREDICT_API_KEY=your_key
POLYMARKET_API_KEY=your_key
DUNE_API_KEY=your_key
WEB3_PROVIDER_URL=https://...

# 可选：数据库配置
POSTGRES_HOST=localhost
POSTGRES_USER=user
POSTGRES_PASSWORD=pass
MONGODB_HOST=localhost
```

## 🗄️ 数据库迁移管理

PredictLab 使用 Alembic 进行数据库版本控制，支持多环境迁移和安全回滚。

### 迁移命令

```bash
# 快速开始 (推荐)
python migration_quickstart.py

# 迁移管理器
python migration_manager.py status --env development
python migration_manager.py upgrade --env development
python migration_manager.py downgrade --revision 001 --env development

# 创建新迁移
python migration_manager.py create --message "添加新字段"

# 查看历史
python migration_manager.py history --env development
```

### 多环境支持

```bash
# 开发环境
export PREDICTLAB_ENV=development
python migration_manager.py upgrade

# 测试环境
export PREDICTLAB_ENV=testing
python migration_manager.py upgrade

# 生产环境 (需谨慎)
export PREDICTLAB_ENV=production
export DATABASE_URL="postgresql://..."
python migration_manager.py upgrade
```

### 迁移文件结构

```
alembic/
├── alembic.ini          # 配置
├── env.py              # 环境配置
├── script.py.mako      # 迁移模板
├── environments.py     # 多环境支持
└── versions/           # 迁移文件
    ├── 001_initial_schema.py      # 初始结构
    └── 002_add_validation_columns.py  # 增量迁移
```

### 迁移最佳实践

- **小步快跑**: 每个迁移只做一件事
- **可逆操作**: 确保所有迁移都可以回滚
- **测试验证**: 在测试环境验证迁移
- **备份先行**: 生产环境迁移前备份数据
- **版本管理**: 迁移文件纳入版本控制

详见 [migration_README.md](migration_README.md)

## 🛡️ 异常处理和测试

PredictLab 实现了完整的异常处理和测试策略，确保系统稳定可靠。

### 异常处理系统

每个模块都配备了统一的异常处理机制：

```python
from utils.error_handler import handle_errors, safe_call

# 错误处理装饰器
@handle_errors("operation_name", retry_count=3)
def risky_operation():
    pass

# 安全调用
result = safe_call(may_fail_function, default_return=None)
```

### 测试运行

```bash
# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 生成覆盖率报告
python run_tests.py coverage

# 运行性能测试
python run_tests.py performance
```

### 测试结构

```
tests/
├── conftest.py              # pytest 配置和共享夹具
├── pytest.ini              # pytest 配置文件
├── test_utils.py           # 测试辅助工具
├── run_tests.py            # 测试运行脚本
├── unit/                   # 单元测试
│   ├── test_data_source.py     # 数据源测试
│   ├── test_data_processing.py # 数据处理测试
│   ├── test_data_storage.py    # 数据存储测试
│   └── test_analysis.py        # 分析测试
└── integration/            # 集成测试
    └── test_full_pipeline.py   # 完整管道测试
```

### 测试覆盖目标

- **单元测试**: ≥ 80%
- **集成测试**: ≥ 70%
- **总覆盖率**: ≥ 75%

详见 [TESTING_README.md](TESTING_README.md)

## 扩展指南

### 添加新数据源
1. 继承 `BaseDataSource`
2. 实现 `connect()`, `fetch_data()` 方法
3. 在 `main.py` 中注册

### 添加新策略
1. 继承或修改 `SimpleStrategy`
2. 实现 `generate_signals()` 方法
3. 传入 `SimpleBacktester.run_backtest()`

### 扩展分析功能
在 `simple_analyzer.py` 中添加新功能，保持接口简单。

## 注意事项

- 原型版本优先速度而非完整性
- 支持模拟数据，无需真实API密钥即可运行
- 核心模块接口稳定，适合后续扩展
- 简化分析工具满足基本原型需求

## 下一步扩展

当原型验证完成后，可以：
1. 扩展真实数据源集成
2. 添加专业回测引擎
3. 引入完整可视化库
4. 实现生产级调度系统
5. 添加更多技术指标和策略
