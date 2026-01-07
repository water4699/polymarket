"""
数据源模块单元测试
测试数据源的基础功能和异常处理
"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from modules.data_source.base import BaseDataSource
from modules.data_source.predict_source import PredictSource
from modules.data_source.polymarket_source import PolymarketSource
from utils.exceptions import DataSourceConnectionError, DataFetchError, APIKeyError
from tests.conftest import test_helper


class MockDataSource(BaseDataSource):
    """测试用的模拟数据源"""

    async def connect(self) -> bool:
        return True

    async def disconnect(self):
        pass

    async def fetch_data(self, symbol: str, start_time: datetime,
                        end_time: datetime, interval: str = "1m") -> pd.DataFrame:
        # 返回模拟数据
        data = {
            'timestamp': [start_time, end_time],
            'symbol': [symbol, symbol],
            'price': [100.0, 101.0]
        }
        return pd.DataFrame(data)

    async def get_symbols(self) -> list:
        return ['BTC_PRICE', 'ETH_PRICE']


class TestBaseDataSource:
    """BaseDataSource 单元测试"""

    @pytest.fixture
    def data_source(self):
        """测试数据源实例"""
        return MockDataSource("test_source")

    def test_init(self, data_source):
        """测试初始化"""
        assert data_source.name == "test_source"
        assert data_source.is_connected == False
        assert data_source.config == {}

    @pytest.mark.asyncio
    async def test_connect(self, data_source):
        """测试连接"""
        result = await data_source.connect()
        assert result == True

    @pytest.mark.asyncio
    async def test_fetch_data(self, data_source):
        """测试数据获取"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        df = await data_source.fetch_data("BTC_PRICE", start_time, end_time)

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        test_helper.assert_required_columns(df, ['timestamp', 'symbol', 'price'])

    @pytest.mark.asyncio
    async def test_get_symbols(self, data_source):
        """测试获取符号列表"""
        symbols = await data_source.get_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0

    def test_validate_config(self, data_source):
        """测试配置验证"""
        result = data_source.validate_config()
        assert result == True

    @pytest.mark.asyncio
    async def test_health_check(self, data_source):
        """测试健康检查"""
        result = await data_source.health_check()
        assert result == True


class TestPredictSource:
    """PredictSource 单元测试"""

    @pytest.fixture
    def predict_source(self):
        """Predict API 数据源"""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://api.predict.example.com'
        }
        return PredictSource(config)

    @pytest.mark.asyncio
    async def test_connect_success(self, predict_source):
        """测试连接成功"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            result = await predict_source.connect()
            assert result == True
            assert predict_source.is_connected == True

    @pytest.mark.asyncio
    async def test_connect_failure(self, predict_source):
        """测试连接失败"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            with pytest.raises(DataSourceConnectionError):
                await predict_source.connect()

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, predict_source, sample_market_data):
        """测试数据获取成功"""
        with patch('requests.get') as mock_get:
            # 模拟API响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'data': sample_market_data.to_dict('records')
            }
            mock_get.return_value = mock_response

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            df = await predict_source.fetch_data("BTC_PRICE", start_time, end_time)

            assert isinstance(df, pd.DataFrame)
            assert not df.empty

    @pytest.mark.asyncio
    async def test_fetch_data_api_error(self, predict_source):
        """测试API错误"""
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 500

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            with pytest.raises(DataFetchError):
                await predict_source.fetch_data("BTC_PRICE", start_time, end_time)

    @pytest.mark.asyncio
    async def test_get_symbols(self, predict_source):
        """测试获取符号列表"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'symbols': ['BTC_PRICE', 'ETH_PRICE', 'SOL_PRICE']
            }
            mock_get.return_value = mock_response

            symbols = await predict_source.get_symbols()
            assert isinstance(symbols, list)
            assert 'BTC_PRICE' in symbols

    def test_validate_config_missing_key(self):
        """测试缺少API密钥的配置验证"""
        config = {}  # 缺少api_key
        source = PredictSource(config)

        with pytest.raises(APIKeyError):
            source.validate_config()


class TestPolymarketSource:
    """PolymarketSource 单元测试"""

    @pytest.fixture
    def polymarket_source(self):
        """Polymarket 数据源"""
        config = {
            'api_key': 'test_key',
            'base_url': 'https://api.polymarket.example.com'
        }
        return PolymarketSource(config)

    @pytest.mark.asyncio
    async def test_fetch_data_polymarket_format(self, polymarket_source):
        """测试Polymarket特定数据格式"""
        with patch('requests.get') as mock_get:
            # 模拟Polymarket API响应
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'markets': [
                    {
                        'id': 'test_market',
                        'question': 'Will BTC exceed $100k?',
                        'endDate': '2024-12-31T00:00:00Z',
                        'yesPrice': 0.6,
                        'noPrice': 0.4,
                        'volume': 1000000
                    }
                ]
            }
            mock_get.return_value = mock_response

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            df = await polymarket_source.fetch_data("BTC_MARKET", start_time, end_time)

            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            # 检查Polymarket特定的字段
            assert 'yes_probability' in df.columns or 'yesPrice' in df.columns


class TestDataSourceErrorHandling:
    """数据源错误处理测试"""

    @pytest.fixture
    def failing_data_source(self):
        """总是失败的数据源"""
        class FailingDataSource(BaseDataSource):
            async def connect(self):
                raise ConnectionError("Network unreachable")

            async def disconnect(self):
                pass

            async def fetch_data(self, symbol, start_time, end_time, interval="1m"):
                raise Exception("API rate limit exceeded")

            async def get_symbols(self):
                raise Exception("Service unavailable")

        return FailingDataSource("failing_source")

    @pytest.mark.asyncio
    async def test_connect_error_handling(self, failing_data_source):
        """测试连接错误处理"""
        with pytest.raises(Exception):  # 会被转换为PredictLabError
            await failing_data_source.connect()

    @pytest.mark.asyncio
    async def test_fetch_error_handling(self, failing_data_source):
        """测试获取数据错误处理"""
        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()

        with pytest.raises(Exception):  # 会被转换为PredictLabError
            await failing_data_source.fetch_data("BTC_PRICE", start_time, end_time)

    @pytest.mark.asyncio
    async def test_health_check_error_handling(self, failing_data_source):
        """测试健康检查错误处理"""
        # 健康检查应该返回False而不是抛出异常
        result = await failing_data_source.health_check()
        assert result == False


class TestDataSourceIntegration:
    """数据源集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_data_flow(self, mock_data_source, sample_market_data):
        """测试完整数据流程"""
        # 连接
        connected = await mock_data_source.connect()
        assert connected

        # 获取符号
        symbols = await mock_data_source.get_symbols()
        assert len(symbols) > 0

        # 健康检查
        healthy = await mock_data_source.health_check()
        assert healthy

        # 断开连接
        await mock_data_source.disconnect()
        assert mock_data_source.is_connected == False
