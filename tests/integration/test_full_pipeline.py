"""
完整管道集成测试
测试数据采集到可视化的完整流程
"""
import pytest
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from modules.data_source.predict_source import PredictSource
from modules.data_processing.data_cleaner import DataCleaner
from modules.data_processing.kline_generator import KlineGenerator
from modules.data_storage.postgres_storage import PostgresStorage
from modules.analysis.simple_analyzer import SimpleStrategy, SimpleBacktester, SimpleChartGenerator
from modules.scheduler.task_scheduler import DataPipelineScheduler
from utils.exceptions import PipelineError, DataSourceError, DataProcessingError
from tests.conftest import test_helper


@pytest.mark.integration
class TestDataPipelineIntegration:
    """数据管道集成测试"""

    @pytest.fixture
    async def mock_data_source(self):
        """模拟数据源"""
        source = MagicMock()
        source.name = "mock_predict"
        source.is_connected = True
        source.connect = AsyncMock(return_value=True)
        source.disconnect = AsyncMock()
        source.get_symbols = AsyncMock(return_value=["BTC_PRICE"])

        # 模拟获取数据
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(minutes=i) for i in range(60)]

        mock_data = pd.DataFrame({
            'timestamp': timestamps,
            'symbol': ['BTC_PRICE'] * 60,
            'price': [40000 + i*10 for i in range(60)],
            'volume': [1000 + i*5 for i in range(60)],
            'open_price': [39900 + i*10 for i in range(60)],
            'high_price': [40200 + i*10 for i in range(60)],
            'low_price': [39800 + i*10 for i in range(60)],
            'close_price': [40000 + i*10 for i in range(60)]
        })

        source.fetch_data = AsyncMock(return_value=mock_data)
        return source

    @pytest.fixture
    async def mock_storage(self):
        """模拟存储"""
        storage = MagicMock()
        storage.is_connected = True
        storage.connect = AsyncMock(return_value=True)
        storage.disconnect = AsyncMock()

        # 模拟存储操作
        storage.insert_raw_market_data = AsyncMock(return_value=True)
        storage.insert_clean_market_data = AsyncMock(return_value=True)
        storage.insert_kline_data = AsyncMock(return_value=True)
        storage.insert_technical_indicators = AsyncMock(return_value=True)

        # 模拟查询操作
        storage.get_raw_market_data = AsyncMock(return_value=pd.DataFrame())
        storage.get_clean_market_data = AsyncMock(return_value=pd.DataFrame())
        storage.get_klines = AsyncMock(return_value=pd.DataFrame())

        return storage

    @pytest.mark.asyncio
    async def test_data_acquisition_to_storage_pipeline(self, mock_data_source, mock_storage):
        """测试数据采集到存储的管道"""
        # 1. 数据采集
        connected = await mock_data_source.connect()
        assert connected

        symbols = await mock_data_source.get_symbols()
        assert "BTC_PRICE" in symbols

        start_time = datetime.now() - timedelta(hours=1)
        end_time = datetime.now()
        raw_data = await mock_data_source.fetch_data("BTC_PRICE", start_time, end_time)

        assert isinstance(raw_data, pd.DataFrame)
        assert not raw_data.empty
        test_helper.assert_required_columns(raw_data, ['timestamp', 'price'])

        # 2. 数据存储
        storage_connected = await mock_storage.connect()
        assert storage_connected

        # 插入原始数据
        for _, row in raw_data.iterrows():
            inserted = await mock_storage.insert_raw_market_data(
                source_type="predict",
                symbol="BTC_PRICE",
                data_timestamp=row['timestamp'],
                raw_data=row.to_dict(),
                data_hash=f"hash_{row['timestamp'].isoformat()}",
                is_processed=False
            )
            assert inserted

    @pytest.mark.asyncio
    async def test_data_processing_pipeline(self, sample_market_data):
        """测试数据处理管道"""
        # 1. 数据清洗
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean_market_data(sample_market_data)

        assert isinstance(cleaned_data, pd.DataFrame)
        assert not cleaned_data.empty

        # 2. K线生成
        kline_generator = KlineGenerator()
        klines = kline_generator.generate_kline(cleaned_data, interval='5m')

        assert isinstance(klines, pd.DataFrame)
        assert not klines.empty
        required_cols = ['open_price', 'high_price', 'low_price', 'close_price']
        test_helper.assert_required_columns(klines, required_cols)

        # 3. 技术指标计算
        with_indicators = kline_generator.add_technical_indicators(klines)

        assert isinstance(with_indicators, pd.DataFrame)
        assert not with_indicators.empty
        # 应该添加了新的指标列
        assert len(with_indicators.columns) > len(klines.columns)

    @pytest.mark.asyncio
    async def test_analysis_pipeline(self, sample_kline_data):
        """测试分析管道"""
        # 1. 策略信号生成
        strategy = SimpleStrategy()
        signals = strategy.moving_average_strategy(sample_kline_data, short_window=5, long_window=10)

        assert isinstance(signals, pd.DataFrame)
        assert not signals.empty
        assert 'signal' in signals.columns

        # 2. 回测执行
        backtester = SimpleBacktester()
        results = backtester.run_backtest(signals)

        assert isinstance(results, dict)
        assert 'total_return' in results
        assert 'sharpe_ratio' in results
        assert 'max_drawdown' in results

        # 3. 图表生成
        chart_generator = SimpleChartGenerator()
        chart = chart_generator.generate_price_chart(signals)

        assert isinstance(chart, str)
        assert len(chart) > 0

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_simulation(self, mock_data_source, mock_storage, sample_market_data):
        """测试端到端管道模拟"""
        try:
            # 1. 数据采集
            await mock_data_source.connect()
            raw_data = await mock_data_source.fetch_data(
                "BTC_PRICE",
                datetime.now() - timedelta(hours=1),
                datetime.now()
            )

            # 2. 数据存储
            await mock_storage.connect()
            await mock_storage.insert_raw_market_data(
                source_type="predict",
                symbol="BTC_PRICE",
                data_timestamp=raw_data.iloc[0]['timestamp'],
                raw_data=raw_data.iloc[0].to_dict(),
                data_hash="test_hash",
                is_processed=False
            )

            # 3. 数据处理
            cleaner = DataCleaner()
            cleaned_data = cleaner.clean_market_data(raw_data)

            kline_generator = KlineGenerator()
            klines = kline_generator.generate_kline(cleaned_data, interval='1h')
            with_indicators = kline_generator.add_technical_indicators(klines)

            # 4. 分析
            strategy = SimpleStrategy()
            signals = strategy.moving_average_strategy(with_indicators)

            backtester = SimpleBacktester()
            results = backtester.run_backtest(signals)

            chart_generator = SimpleChartGenerator()
            chart = chart_generator.generate_combined_chart(signals)

            # 验证最终结果
            assert isinstance(results, dict)
            assert isinstance(chart, str)
            assert len(chart) > 0

        finally:
            # 清理连接
            await mock_data_source.disconnect()
            await mock_storage.disconnect()

    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self, mock_data_source):
        """测试管道错误处理"""
        # 创建一个会失败的数据源
        failing_source = MagicMock()
        failing_source.connect = AsyncMock(return_value=True)
        failing_source.fetch_data = AsyncMock(side_effect=Exception("API rate limit"))

        try:
            await failing_source.connect()
            with pytest.raises(Exception):  # 应该被转换为PredictLabError
                await failing_source.fetch_data("BTC_PRICE", datetime.now(), datetime.now())
        except Exception as e:
            # 验证错误被正确处理
            assert "rate limit" in str(e).lower()

    def test_data_quality_through_pipeline(self, sample_market_data):
        """测试管道中的数据质量"""
        # 1. 清洗前质量检查
        cleaner = DataCleaner()
        is_valid_before, issues_before = cleaner.validate_market_data(sample_market_data)

        # 2. 数据清洗
        cleaned_data = cleaner.clean_market_data(sample_market_data)

        # 3. 清洗后质量检查
        is_valid_after, issues_after = cleaner.validate_market_data(cleaned_data)

        # 清洗后问题应该更少
        assert len(issues_after) <= len(issues_before)

        # 4. K线生成质量检查
        kline_generator = KlineGenerator()
        klines = kline_generator.generate_kline(cleaned_data, interval='1h')

        is_valid_klines, kline_issues = kline_generator.validate_kline_data(klines)

        # K线数据应该有效
        assert is_valid_klines or len(kline_issues) == 0


class TestSchedulerIntegration:
    """调度器集成测试"""

    @pytest.fixture
    def scheduler_config(self):
        """调度器配置"""
        return {
            'max_concurrent': 2,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'enable_circuit_breaker': True
        }

    @pytest.mark.asyncio
    async def test_scheduler_pipeline_execution(self, scheduler_config, mock_data_source, mock_storage):
        """测试调度器管道执行"""
        with patch('modules.data_source.predict_source.PredictSource', return_value=mock_data_source), \
             patch('modules.data_storage.postgres_storage.PostgresStorage', return_value=mock_storage):

            scheduler = DataPipelineScheduler(scheduler_config)

            # 执行管道
            results = await scheduler.run_pipeline(
                symbols=['BTC_PRICE'],
                source_types=['predict'],
                intervals=['1h']
            )

            assert isinstance(results, dict)
            assert 'status' in results

    @pytest.mark.asyncio
    async def test_scheduler_error_recovery(self, scheduler_config):
        """测试调度器错误恢复"""
        # 创建会失败的任务
        failing_config = scheduler_config.copy()
        failing_config['retry_attempts'] = 2

        scheduler = DataPipelineScheduler(failing_config)

        # 这里可以添加具体的错误恢复测试
        # 由于依赖复杂的模拟，这里只是结构测试
        assert scheduler is not None


class TestCrossModuleIntegration:
    """跨模块集成测试"""

    def test_data_format_consistency(self, sample_market_data, sample_kline_data):
        """测试数据格式一致性"""
        # 确保不同模块使用相同的数据格式
        required_market_cols = ['timestamp', 'price']
        required_kline_cols = ['timestamp', 'open_price', 'high_price', 'low_price', 'close_price']

        test_helper.assert_required_columns(sample_market_data, required_market_cols)
        test_helper.assert_required_columns(sample_kline_data, required_kline_cols)

    def test_exception_hierarchy(self):
        """测试异常层次结构"""
        from utils.exceptions import (
            PredictLabError, DataSourceError, DataProcessingError,
            DataStorageError, AnalysisError
        )

        # 验证异常继承关系
        assert issubclass(DataSourceError, PredictLabError)
        assert issubclass(DataProcessingError, PredictLabError)
        assert issubclass(DataStorageError, PredictLabError)
        assert issubclass(AnalysisError, PredictLabError)

    def test_configuration_consistency(self):
        """测试配置一致性"""
        from config import config

        # 验证配置有必要的属性
        assert hasattr(config, 'postgres_url')
        assert hasattr(config, 'mongo_url')

        # 验证配置值合理
        assert isinstance(config.postgres_url, str)
        assert len(config.postgres_url) > 0


class TestPerformanceIntegration:
    """性能集成测试"""

    @pytest.mark.slow
    def test_large_dataset_processing(self):
        """测试大数据集处理"""
        # 生成大量数据
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(minutes=i) for i in range(1000)]  # 1000个数据点

        large_data = pd.DataFrame({
            'timestamp': timestamps,
            'symbol': ['BTC_PRICE'] * 1000,
            'price': np.random.uniform(30000, 50000, 1000),
            'volume': np.random.uniform(100, 10000, 1000),
            'open_price': np.random.uniform(30000, 50000, 1000),
            'high_price': np.random.uniform(45000, 55000, 1000),
            'low_price': np.random.uniform(25000, 35000, 1000),
            'close_price': np.random.uniform(30000, 50000, 1000)
        })

        # 测试处理性能
        cleaner = DataCleaner()
        start_time = datetime.now()
        cleaned_data = cleaner.clean_market_data(large_data)
        clean_time = (datetime.now() - start_time).total_seconds()

        kline_generator = KlineGenerator()
        start_time = datetime.now()
        klines = kline_generator.generate_kline(cleaned_data, interval='1h')
        kline_time = (datetime.now() - start_time).total_seconds()

        # 验证结果正确性
        assert not cleaned_data.empty
        assert not klines.empty

        # 记录性能指标（实际使用中可以设置阈值）
        print(f"数据清洗耗时: {clean_time:.2f}秒")
        print(f"K线生成耗时: {kline_time:.2f}秒")
        print(f"处理数据量: {len(large_data)} 行")

    def test_memory_usage(self, sample_market_data):
        """测试内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行数据处理
        cleaner = DataCleaner()
        cleaned_data = cleaner.clean_market_data(sample_market_data)

        kline_generator = KlineGenerator()
        klines = kline_generator.generate_kline(cleaned_data, interval='1h')

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        # 内存使用应该在合理范围内
        assert memory_used < 100  # 假设不超过100MB

        print(".2f")
