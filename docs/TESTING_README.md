# PredictLab 测试指南

PredictLab 实现了完整的异常处理和测试策略，确保系统稳定可靠。本文档介绍测试框架、运行方法和最佳实践。

## 📋 目录

- [测试架构](#测试架构)
- [异常处理](#异常处理)
- [快速开始](#快速开始)
- [测试类型](#测试类型)
- [运行测试](#运行测试)
- [测试覆盖](#测试覆盖)
- [持续集成](#持续集成)
- [故障排除](#故障排除)

## 🏗️ 测试架构

### 目录结构

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
├── integration/            # 集成测试
│   └── test_full_pipeline.py   # 完整管道测试
└── fixtures/               # 测试数据和配置
```

### 核心组件

- **异常处理系统**: 统一的错误捕获、日志记录和恢复机制
- **测试数据生成器**: 自动生成各种测试数据
- **模拟对象工厂**: 创建可预测的测试依赖
- **断言工具**: 专门的测试断言函数

## ⚠️ 异常处理

### 异常层次结构

```
PredictLabError (基础异常)
├── DataSourceError (数据源异常)
│   ├── DataSourceConnectionError
│   ├── DataFetchError
│   └── APIKeyError
├── DataProcessingError (数据处理异常)
│   ├── DataValidationError
│   ├── DataCleaningError
│   └── KlineGenerationError
├── DataStorageError (数据存储异常)
│   ├── DatabaseConnectionError
│   └── DatabaseOperationError
├── AnalysisError (分析异常)
│   ├── BacktestError
│   └── StrategyError
├── VisualizationError (可视化异常)
├── SchedulerError (调度异常)
├── ConfigurationError (配置异常)
└── ValidationError (验证异常)
```

### 异常处理装饰器

```python
from utils.error_handler import handle_errors, safe_call

# 基本错误处理
@handle_errors("operation_name", retry_count=3)
def risky_operation():
    # 可能失败的操作
    pass

# 异步错误处理
@handle_async_errors("async_operation", severity=ErrorSeverity.HIGH)
async def async_risky_operation():
    pass

# 安全调用
result = safe_call(may_fail_function, default_return=None)
```

### 熔断器模式

```python
from utils.error_handler import CircuitBreaker

@CircuitBreaker(failure_threshold=5, recovery_timeout=60)
def api_call():
    # API 调用，失败时自动熔断
    pass
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行所有测试

```bash
# 使用测试运行器（推荐）
python run_tests.py all

# 或直接使用 pytest
pytest
```

### 3. 运行单元测试

```bash
python run_tests.py unit
```

### 4. 运行集成测试

```bash
python run_tests.py integration
```

### 5. 生成覆盖率报告

```bash
python run_tests.py coverage
```

## 📊 测试类型

### 单元测试 (Unit Tests)

测试单个组件的独立功能：

```python
import pytest
from modules.data_processing.data_cleaner import DataCleaner

def test_data_cleaner_init():
    cleaner = DataCleaner()
    assert cleaner is not None

def test_clean_market_data(sample_market_data):
    cleaner = DataCleaner()
    cleaned = cleaner.clean_market_data(sample_market_data)
    assert not cleaned.empty
```

### 集成测试 (Integration Tests)

测试组件间的交互：

```python
@pytest.mark.integration
async def test_data_pipeline_integration(mock_data_source, mock_storage):
    # 测试完整的数据管道
    await mock_data_source.connect()
    data = await mock_data_source.fetch_data("BTC_PRICE")

    await mock_storage.connect()
    await mock_storage.insert_raw_market_data(data)

    # 验证数据流
    stored_data = await mock_storage.get_raw_market_data("BTC_PRICE")
    assert not stored_data.empty
```

### 性能测试 (Performance Tests)

```python
@pytest.mark.slow
def test_large_dataset_processing():
    # 生成大量数据
    large_data = TestDataGenerator.generate_market_data(
        MarketDataSpec(data_points=10000)
    )

    # 测试处理性能
    start_time = time.time()
    result = process_data(large_data)
    duration = time.time() - start_time

    assert duration < 30  # 应该在30秒内完成
```

## 🏃 运行测试

### 基本命令

```bash
# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 运行特定测试文件
python run_tests.py specific tests/unit/test_data_source.py

# 运行性能测试
python run_tests.py performance

# 检查测试结构
python run_tests.py check
```

### pytest 直接命令

```bash
# 运行所有测试
pytest

# 运行带覆盖率的测试
pytest --cov=. --cov-report=html

# 运行特定标记的测试
pytest -m "integration and not slow"

# 运行特定文件的测试
pytest tests/unit/test_data_source.py::TestPredictSource::test_fetch_data

# 并行运行
pytest -n auto

# 显示最慢的测试
pytest --durations=10
```

### 环境变量

```bash
# 设置测试环境
export PREDICTLAB_ENV=testing

# 禁用日志
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

# 设置并行进程数
export PYTEST_XDIST_WORKER_COUNT=4
```

## 📈 测试覆盖

### 覆盖率目标

- **单元测试**: ≥ 80%
- **集成测试**: ≥ 70%
- **总覆盖率**: ≥ 75%

### 查看覆盖率

```bash
# 生成 HTML 报告
python run_tests.py coverage

# 查看终端报告
pytest --cov=. --cov-report=term-missing

# 查看具体文件覆盖
pytest --cov=modules.data_source --cov-report=html
```

### 覆盖率配置

pytest.ini 中的覆盖率设置：

```ini
[tool:pytest]
addopts =
    --cov=.
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
```

## 🔄 持续集成

### GitHub Actions 示例

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: python run_tests.py all
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### 本地 CI 脚本

```bash
#!/bin/bash
# ci.sh

# 安装依赖
pip install -r requirements.txt

# 运行测试
python run_tests.py all

# 检查覆盖率
coverage report --fail-under=80

# 运行静态检查（如果配置了）
# flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
# mypy .
```

## 🧪 测试数据和模拟

### 测试数据生成

```python
from tests.test_utils import TestDataGenerator, MarketDataSpec

# 生成市场数据
spec = MarketDataSpec(
    symbol="BTC_PRICE",
    base_price=40000,
    data_points=100,
    volatility=0.02
)
market_data = TestDataGenerator.generate_market_data(spec)

# 生成K线数据
kline_data = TestDataGenerator.generate_kline_data("BTC_PRICE", "1h", 50)

# 生成技术指标
indicators = TestDataGenerator.generate_technical_indicators(kline_data)

# 生成交易信号
signals = TestDataGenerator.generate_trading_signals(kline_data, 'ma_cross')
```

### 模拟对象

```python
from tests.test_utils import MockFactory

# 创建模拟数据源
mock_source = MockFactory.create_mock_data_source(success=True)

# 创建模拟存储
mock_storage = MockFactory.create_mock_storage(success=True)

# 创建模拟API响应
mock_response = MockFactory.create_mock_api_response(200, {"data": []})
```

### 自定义断言

```python
from tests.test_utils import TestAssertions

# 断言 DataFrame 结构
TestAssertions.assert_dataframe_structure(df, ['timestamp', 'price', 'volume'])

# 断言 OHLCV 完整性
TestAssertions.assert_ohlcv_integrity(kline_data)

# 断言交易信号有效性
TestAssertions.assert_signals_valid(signals_df)

# 断言回测结果
TestAssertions.assert_backtest_results(backtest_results)
```

## 🐛 故障排除

### 常见问题

#### 1. 测试超时

```bash
# 增加超时时间
pytest --timeout=300

# 或在测试上添加标记
@pytest.mark.slow
def test_slow_operation():
    pass
```

#### 2. 异步测试失败

```bash
# 确保使用正确的异步标记
@pytest.mark.asyncio
async def test_async_function():
    pass
```

#### 3. 数据库测试失败

```bash
# 检查数据库配置
export PREDICTLAB_ENV=testing

# 或者跳过数据库测试
pytest -m "not database"
```

#### 4. 覆盖率报告不生成

```bash
# 清除缓存
pytest --cache-clear

# 重新生成报告
python run_tests.py coverage
```

#### 5. 导入错误

```bash
# 检查 Python 路径
export PYTHONPATH=$PWD:$PYTHONPATH

# 或在测试文件开头添加
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
```

### 调试技巧

```python
# 启用调试模式
pytest -s -v --pdb

# 只运行失败的测试
pytest --lf

# 显示所有输出
pytest -s

# 详细的错误信息
pytest --tb=long
```

## 📝 编写测试的最佳实践

### 1. 测试命名

```python
# 好的命名
def test_data_cleaner_handles_missing_values():
def test_strategy_generates_valid_signals():
def test_storage_inserts_data_successfully():

# 不好的命名
def test_func():
def test_stuff():
```

### 2. 测试结构

```python
class TestMyComponent:
    def setup_method(self):
        # 每个测试前的设置
        pass

    def teardown_method(self):
        # 每个测试后的清理
        pass

    def test_normal_operation(self):
        # 正常情况测试
        pass

    def test_edge_cases(self):
        # 边界情况测试
        pass

    def test_error_conditions(self):
        # 错误情况测试
        pass
```

### 3. 使用夹具

```python
@pytest.fixture
def sample_data(self):
    return generate_test_data()

def test_with_sample_data(sample_data):
    result = process_data(sample_data)
    assert result is not None
```

### 4. 模拟外部依赖

```python
def test_api_call_with_mock(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": []}

    mocker.patch('requests.get', return_value=mock_response)

    result = api_call()
    assert result.success
```

### 5. 参数化测试

```python
@pytest.mark.parametrize("input_value,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input_value, expected):
    assert double(input_value) == expected
```

## 📊 测试指标

### 质量指标

- **测试通过率**: ≥ 99%
- **测试覆盖率**: ≥ 80%
- **测试执行时间**: < 5分钟
- **失败测试重试率**: < 1%

### 监控指标

```python
# 在 CI/CD 中监控
def test_quality_metrics():
    # 测试数量
    # 覆盖率
    # 执行时间
    # 失败率
    pass
```

## 🔧 维护指南

### 添加新测试

1. 确定测试类型（单元/集成）
2. 创建相应的测试文件
3. 编写测试用例
4. 添加必要的测试数据
5. 运行测试验证
6. 更新文档

### 更新现有测试

1. 分析变更影响
2. 修改相关测试
3. 运行回归测试
4. 更新测试数据
5. 验证覆盖率

### 测试重构

1. 识别重复代码
2. 提取公共夹具
3. 简化测试逻辑
4. 改进断言
5. 更新文档

---

*最后更新: 2024-01-16*
*测试覆盖率目标: ≥ 80%*
