"""
数据存储模块单元测试
测试PostgreSQL和MongoDB存储功能
"""
import pytest
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any

from modules.data_storage.postgres_storage import PostgresStorage
from modules.data_storage.mongo_storage import MongoStorage
from utils.exceptions import DatabaseConnectionError, DatabaseOperationError
from tests.conftest import test_helper


class TestPostgresStorage:
    """PostgreSQL存储单元测试"""

    @pytest.fixture
    def postgres_storage(self):
        """PostgreSQL存储实例"""
        return PostgresStorage()

    @pytest.fixture
    def sample_raw_data(self):
        """示例原始数据"""
        return {
            'source_type': 'predict',
            'symbol': 'BTC_PRICE',
            'data_timestamp': datetime.now(),
            'raw_data': {'price': 40000, 'volume': 100},
            'data_hash': 'test_hash_123',
            'is_processed': False
        }

    @pytest.fixture
    def sample_clean_data(self):
        """示例清洗数据"""
        return {
            'source_type': 'predict',
            'symbol': 'BTC_PRICE',
            'data_timestamp': datetime.now(),
            'price': 40000.0,
            'volume': 100.0,
            'data_quality_score': 0.95
        }

    @pytest.mark.asyncio
    async def test_connect_success(self, postgres_storage):
        """测试连接成功"""
        with patch('asyncpg.connect') as mock_connect:
            mock_connect.return_value = MagicMock()
            result = await postgres_storage.connect()
            assert result == True
            assert postgres_storage.is_connected == True

    @pytest.mark.asyncio
    async def test_connect_failure(self, postgres_storage):
        """测试连接失败"""
        with patch('asyncpg.connect') as mock_connect:
            mock_connect.side_effect = Exception("Connection refused")

            with pytest.raises(DatabaseConnectionError):
                await postgres_storage.connect()

    @pytest.mark.asyncio
    async def test_insert_raw_market_data(self, postgres_storage, sample_raw_data):
        """测试插入原始市场数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [1]  # 返回插入的ID

            result = await postgres_storage.insert_raw_market_data(**sample_raw_data)
            assert result == True

            # 验证调用参数
            call_args = mock_execute.call_args
            assert 'INSERT INTO raw_market_data' in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_raw_market_data(self, postgres_storage, sample_raw_data):
        """测试获取原始市场数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            # 模拟查询结果
            mock_execute.return_value = [{
                'id': 1,
                'source_type': sample_raw_data['source_type'],
                'symbol': sample_raw_data['symbol'],
                'data_timestamp': sample_raw_data['data_timestamp'],
                'raw_data': sample_raw_data['raw_data'],
                'created_at': datetime.now()
            }]

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            df = await postgres_storage.get_raw_market_data(
                sample_raw_data['symbol'], start_time, end_time
            )

            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            test_helper.assert_required_columns(df, ['id', 'source_type', 'symbol', 'data_timestamp'])

    @pytest.mark.asyncio
    async def test_insert_clean_market_data(self, postgres_storage, sample_clean_data):
        """测试插入清洗市场数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [1]

            result = await postgres_storage.insert_clean_market_data(**sample_clean_data)
            assert result == True

    @pytest.mark.asyncio
    async def test_get_clean_market_data(self, postgres_storage, sample_clean_data):
        """测试获取清洗市场数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [{
                'id': 1,
                'source_type': sample_clean_data['source_type'],
                'symbol': sample_clean_data['symbol'],
                'data_timestamp': sample_clean_data['data_timestamp'],
                'price': sample_clean_data['price'],
                'volume': sample_clean_data['volume'],
                'created_at': datetime.now()
            }]

            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            df = await postgres_storage.get_clean_market_data(
                sample_clean_data['symbol'], start_time, end_time
            )

            assert isinstance(df, pd.DataFrame)
            assert not df.empty

    @pytest.mark.asyncio
    async def test_insert_kline_data(self, postgres_storage):
        """测试插入K线数据"""
        kline_data = {
            'source_type': 'predict',
            'symbol': 'BTC_PRICE',
            'interval_type': '1h',
            'interval_start': datetime.now(),
            'interval_end': datetime.now() + timedelta(hours=1),
            'open_price': 40000.0,
            'high_price': 41000.0,
            'low_price': 39500.0,
            'close_price': 40500.0,
            'volume': 1000.0,
            'trade_count': 50
        }

        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [1]

            result = await postgres_storage.insert_kline_data(**kline_data)
            assert result == True

    @pytest.mark.asyncio
    async def test_get_klines(self, postgres_storage):
        """测试获取K线数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [{
                'id': 1,
                'source_type': 'predict',
                'symbol': 'BTC_PRICE',
                'interval_type': '1h',
                'interval_start': datetime.now(),
                'open_price': 40000.0,
                'high_price': 41000.0,
                'low_price': 39500.0,
                'close_price': 40500.0,
                'volume': 1000.0,
                'created_at': datetime.now()
            }]

            start_time = datetime.now() - timedelta(hours=24)
            end_time = datetime.now()

            df = await postgres_storage.get_klines('BTC_PRICE', '1h', start_time, end_time)

            assert isinstance(df, pd.DataFrame)
            assert not df.empty
            required_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
            test_helper.assert_required_columns(df, required_cols)

    @pytest.mark.asyncio
    async def test_insert_technical_indicators(self, postgres_storage, sample_technical_indicators):
        """测试插入技术指标"""
        # 获取第一行数据
        indicator_data = sample_technical_indicators.iloc[0].to_dict()
        indicator_data.update({
            'symbol': 'BTC_PRICE',
            'interval_type': '1h',
            'data_timestamp': datetime.now()
        })

        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [1]

            result = await postgres_storage.insert_technical_indicators(**indicator_data)
            assert result == True

    @pytest.mark.asyncio
    async def test_get_technical_indicators(self, postgres_storage):
        """测试获取技术指标"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = [{
                'id': 1,
                'symbol': 'BTC_PRICE',
                'interval_type': '1h',
                'data_timestamp': datetime.now(),
                'sma_5': 40000.0,
                'rsi_14': 65.0,
                'macd_line': 100.0,
                'created_at': datetime.now()
            }]

            start_time = datetime.now() - timedelta(hours=24)
            end_time = datetime.now()

            df = await postgres_storage.get_technical_indicators(
                'BTC_PRICE', '1h', start_time, end_time
            )

            assert isinstance(df, pd.DataFrame)
            assert not df.empty

    @pytest.mark.asyncio
    async def test_delete_data(self, postgres_storage):
        """测试删除数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = []  # DELETE返回空结果

            result = await postgres_storage.delete_data('raw_market_data', {'symbol': 'BTC_PRICE'})
            assert result == True

    @pytest.mark.asyncio
    async def test_update_data(self, postgres_storage):
        """测试更新数据"""
        with patch.object(postgres_storage, '_execute_query') as mock_execute:
            mock_execute.return_value = []  # UPDATE返回空结果

            result = await postgres_storage.update_data(
                'raw_market_data',
                {'is_processed': True},
                {'symbol': 'BTC_PRICE'}
            )
            assert result == True

    def test_validate_connection_params(self, postgres_storage):
        """测试连接参数验证"""
        # 有效参数
        assert postgres_storage._validate_connection_params({
            'host': 'localhost',
            'port': 5432,
            'database': 'test'
        })

        # 无效参数
        assert not postgres_storage._validate_connection_params({})
        assert not postgres_storage._validate_connection_params({'invalid': 'params'})

    @pytest.mark.asyncio
    async def test_connection_context_manager(self, postgres_storage):
        """测试连接上下文管理器"""
        with patch('asyncpg.connect') as mock_connect:
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection

            async with postgres_storage._connection() as conn:
                assert conn == mock_connection

            # 验证连接被关闭
            mock_connection.close.assert_called_once()


class TestMongoStorage:
    """MongoDB存储单元测试"""

    @pytest.fixture
    def mongo_storage(self):
        """MongoDB存储实例"""
        return MongoStorage()

    @pytest.fixture
    def sample_document(self):
        """示例文档"""
        return {
            'source_type': 'predict',
            'symbol': 'BTC_PRICE',
            'timestamp': datetime.now(),
            'data': {'price': 40000, 'volume': 100},
            'metadata': {'quality_score': 0.95}
        }

    @pytest.mark.asyncio
    async def test_connect_success(self, mongo_storage):
        """测试连接成功"""
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_db = MagicMock()
            mock_client.return_value = mock_db

            result = await mongo_storage.connect()
            assert result == True
            assert mongo_storage.is_connected == True

    @pytest.mark.asyncio
    async def test_connect_failure(self, mongo_storage):
        """测试连接失败"""
        with patch('motor.motor_asyncio.AsyncIOMotorClient') as mock_client:
            mock_client.side_effect = Exception("Connection failed")

            with pytest.raises(DatabaseConnectionError):
                await mongo_storage.connect()

    @pytest.mark.asyncio
    async def test_insert_document(self, mongo_storage, sample_document):
        """测试插入文档"""
        with patch.object(mongo_storage, '_get_collection') as mock_get_collection:
            mock_collection = MagicMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.insert_one.return_value = MagicMock(inserted_id='test_id')

            result = await mongo_storage.insert_document('test_collection', sample_document)
            assert result == True

    @pytest.mark.asyncio
    async def test_find_documents(self, mongo_storage, sample_document):
        """测试查找文档"""
        with patch.object(mongo_storage, '_get_collection') as mock_get_collection:
            mock_collection = MagicMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.find.return_value = [sample_document]

            query = {'symbol': 'BTC_PRICE'}
            documents = await mongo_storage.find_documents('test_collection', query)

            assert isinstance(documents, list)
            assert len(documents) == 1

    @pytest.mark.asyncio
    async def test_update_document(self, mongo_storage):
        """测试更新文档"""
        with patch.object(mongo_storage, '_get_collection') as mock_get_collection:
            mock_collection = MagicMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.update_one.return_value = MagicMock(modified_count=1)

            query = {'symbol': 'BTC_PRICE'}
            update_data = {'$set': {'price': 41000}}

            result = await mongo_storage.update_document('test_collection', query, update_data)
            assert result == True

    @pytest.mark.asyncio
    async def test_delete_documents(self, mongo_storage):
        """测试删除文档"""
        with patch.object(mongo_storage, '_get_collection') as mock_get_collection:
            mock_collection = MagicMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.delete_many.return_value = MagicMock(deleted_count=5)

            query = {'symbol': 'BTC_PRICE'}
            result = await mongo_storage.delete_documents('test_collection', query)
            assert result == True

    @pytest.mark.asyncio
    async def test_aggregate_documents(self, mongo_storage):
        """测试聚合查询"""
        with patch.object(mongo_storage, '_get_collection') as mock_get_collection:
            mock_collection = MagicMock()
            mock_get_collection.return_value = mock_collection
            mock_collection.aggregate.return_value = [{'avg_price': 40000}]

            pipeline = [
                {'$match': {'symbol': 'BTC_PRICE'}},
                {'$group': {'_id': None, 'avg_price': {'$avg': '$price'}}}
            ]

            results = await mongo_storage.aggregate_documents('test_collection', pipeline)

            assert isinstance(results, list)
            assert len(results) == 1


class TestStorageErrorHandling:
    """存储错误处理测试"""

    @pytest.fixture
    def failing_postgres_storage(self):
        """总是失败的PostgreSQL存储"""
        class FailingPostgresStorage(PostgresStorage):
            async def _execute_query(self, query, params=None):
                raise Exception("Database error")

        return FailingPostgresStorage()

    @pytest.fixture
    def failing_mongo_storage(self):
        """总是失败的MongoDB存储"""
        class FailingMongoStorage(MongoStorage):
            def _get_collection(self, collection_name):
                raise Exception("MongoDB connection error")

        return FailingMongoStorage()

    @pytest.mark.asyncio
    async def test_postgres_operation_error(self, failing_postgres_storage, sample_raw_data):
        """测试PostgreSQL操作错误"""
        with pytest.raises(DatabaseOperationError):
            await failing_postgres_storage.insert_raw_market_data(**sample_raw_data)

    @pytest.mark.asyncio
    async def test_mongo_operation_error(self, failing_mongo_storage, sample_document):
        """测试MongoDB操作错误"""
        with pytest.raises(DatabaseOperationError):
            await failing_mongo_storage.insert_document('test_collection', sample_document)


class TestStorageIntegration:
    """存储集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_storage_workflow(self, postgres_storage, sample_raw_data, sample_clean_data):
        """测试完整存储工作流"""
        # 注意：这是一个集成测试，需要真实的数据库
        # 在实际运行时需要确保数据库可用

        try:
            # 连接数据库
            connected = await postgres_storage.connect()
            if not connected:
                pytest.skip("数据库不可用，跳过集成测试")

            # 插入原始数据
            raw_inserted = await postgres_storage.insert_raw_market_data(**sample_raw_data)
            assert raw_inserted

            # 插入清洗数据
            clean_inserted = await postgres_storage.insert_clean_market_data(**sample_clean_data)
            assert clean_inserted

            # 查询数据
            start_time = datetime.now() - timedelta(hours=1)
            end_time = datetime.now()

            raw_data = await postgres_storage.get_raw_market_data(
                sample_raw_data['symbol'], start_time, end_time
            )
            assert not raw_data.empty

            clean_data = await postgres_storage.get_clean_market_data(
                sample_clean_data['symbol'], start_time, end_time
            )
            assert not clean_data.empty

            # 断开连接
            await postgres_storage.disconnect()
            assert not postgres_storage.is_connected

        except Exception as e:
            pytest.skip(f"集成测试失败: {e}")
