"""
Pytest 配置和共享的测试工具
"""
import os
import sys
import pytest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, AsyncMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import config
from utils.logger import get_logger


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    # 创建测试配置，避免修改生产配置
    test_config = config.__class__(
        postgres_host="localhost",
        postgres_port=5432,
        postgres_user="test",
        postgres_password="test",
        postgres_database="predictlab_test",
        mongo_host="localhost",
        mongo_port=27017,
        mongo_database="predictlab_test"
    )
    return test_config


@pytest.fixture
def mock_logger():
    """模拟日志记录器"""
    return MagicMock()


@pytest.fixture
def sample_market_data():
    """示例市场数据"""
    base_time = datetime(2024, 1, 1, 0, 0, 0)

    # 生成1小时的分钟级数据
    timestamps = [base_time + timedelta(minutes=i) for i in range(60)]

    data = {
        'timestamp': timestamps,
        'symbol': ['BTC_PRICE'] * 60,
        'price': np.random.uniform(40000, 50000, 60),
        'volume': np.random.uniform(100, 1000, 60),
        'open_price': np.random.uniform(40000, 50000, 60),
        'high_price': np.random.uniform(45000, 55000, 60),
        'low_price': np.random.uniform(35000, 45000, 60),
        'close_price': np.random.uniform(40000, 50000, 60)
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_kline_data():
    """示例K线数据"""
    base_time = datetime(2024, 1, 1, 0, 0, 0)

    # 生成24小时的小时级K线数据
    timestamps = [base_time + timedelta(hours=i) for i in range(24)]

    data = {
        'timestamp': timestamps,
        'symbol': ['BTC_PRICE'] * 24,
        'interval_type': ['1h'] * 24,
        'open_price': np.random.uniform(40000, 50000, 24),
        'high_price': np.random.uniform(45000, 55000, 24),
        'low_price': np.random.uniform(35000, 45000, 24),
        'close_price': np.random.uniform(40000, 50000, 24),
        'volume': np.random.uniform(1000, 10000, 24),
        'trade_count': np.random.randint(50, 500, 24)
    }

    return pd.DataFrame(data)


@pytest.fixture
def sample_technical_indicators():
    """示例技术指标数据"""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    timestamps = [base_time + timedelta(hours=i) for i in range(24)]

    data = {
        'timestamp': timestamps,
        'symbol': ['BTC_PRICE'] * 24,
        'interval_type': ['1h'] * 24,
        'sma_5': np.random.uniform(40000, 50000, 24),
        'sma_10': np.random.uniform(40000, 50000, 24),
        'rsi_14': np.random.uniform(20, 80, 24),
        'macd_line': np.random.uniform(-1000, 1000, 24),
        'macd_signal': np.random.uniform(-1000, 1000, 24),
        'bb_upper': np.random.uniform(45000, 55000, 24),
        'bb_middle': np.random.uniform(40000, 50000, 24),
        'bb_lower': np.random.uniform(35000, 45000, 24)
    }

    return pd.DataFrame(data)


@pytest.fixture
def mock_data_source():
    """模拟数据源"""
    mock_ds = MagicMock()
    mock_ds.name = "mock_source"
    mock_ds.is_connected = True
    mock_ds.connect = AsyncMock(return_value=True)
    mock_ds.disconnect = AsyncMock()
    mock_ds.get_symbols = AsyncMock(return_value=["BTC_PRICE", "ETH_PRICE"])
    return mock_ds


@pytest.fixture
def mock_storage():
    """模拟存储器"""
    mock_store = MagicMock()
    mock_store.connect = AsyncMock(return_value=True)
    mock_store.disconnect = AsyncMock()
    mock_store.insert_raw_market_data = AsyncMock(return_value=True)
    mock_store.get_raw_market_data = AsyncMock(return_value=pd.DataFrame())
    return mock_store


@pytest.fixture
async def async_db_connection(test_config):
    """异步数据库连接（如果可用）"""
    # 这里可以实现真实的异步数据库连接用于集成测试
    # 目前返回模拟对象
    mock_conn = MagicMock()
    yield mock_conn


@pytest.fixture
def temp_dir(tmp_path):
    """临时目录"""
    return tmp_path


@pytest.fixture(autouse=True)
def setup_test_environment():
    """设置测试环境"""
    # 设置测试环境变量
    original_env = os.environ.get('PREDICTLAB_ENV')
    os.environ['PREDICTLAB_ENV'] = 'testing'

    yield

    # 恢复原始环境
    if original_env:
        os.environ['PREDICTLAB_ENV'] = original_env
    elif 'PREDICTLAB_ENV' in os.environ:
        del os.environ['PREDICTLAB_ENV']


# 自定义标记
def pytest_configure(config):
    """配置pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "database: marks tests that require database")
    config.addinivalue_line("markers", "async: marks tests that are async")


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    for item in items:
        # 自动标记异步测试
        if 'async' in item.name or 'async' in str(item.function.__name__):
            item.add_marker(pytest.mark.asyncio)

        # 根据文件路径自动标记
        if 'integration' in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif 'unit' in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# 测试工具类
class TestHelper:
    """测试辅助工具"""

    @staticmethod
    def assert_dataframe_equal(df1: pd.DataFrame, df2: pd.DataFrame,
                              check_dtype: bool = True, rtol: float = 1e-5):
        """断言DataFrame相等"""
        pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtype, rtol=rtol)

    @staticmethod
    def assert_dataframe_not_empty(df: pd.DataFrame):
        """断言DataFrame不为空"""
        assert not df.empty, "DataFrame is empty"
        assert len(df) > 0, "DataFrame has no rows"

    @staticmethod
    def assert_required_columns(df: pd.DataFrame, required_cols: List[str]):
        """断言DataFrame包含必需列"""
        missing_cols = [col for col in required_cols if col not in df.columns]
        assert not missing_cols, f"Missing required columns: {missing_cols}"

    @staticmethod
    def create_mock_exception(exception_class, message: str, **kwargs):
        """创建模拟异常"""
        exc = MagicMock(spec=exception_class)
        exc.message = message
        exc.error_code = kwargs.get('error_code', 'TEST_ERROR')
        exc.severity = kwargs.get('severity', 'medium')
        exc.context = kwargs.get('context', {})
        exc.to_dict.return_value = {
            'error_code': exc.error_code,
            'message': exc.message,
            'severity': exc.severity,
            'context': exc.context
        }
        exc.__str__ = MagicMock(return_value=message)
        return exc


# 导出测试工具
test_helper = TestHelper()
