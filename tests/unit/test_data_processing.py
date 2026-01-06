"""
数据处理模块单元测试
测试数据清洗、K线生成和技术指标计算
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from modules.data_processing.data_cleaner import DataCleaner
from modules.data_processing.kline_generator import KlineGenerator
from utils.exceptions import DataValidationError, DataCleaningError, KlineGenerationError
from tests.conftest import test_helper


class TestDataCleaner:
    """DataCleaner 单元测试"""

    @pytest.fixture
    def cleaner(self):
        """数据清洗器实例"""
        return DataCleaner()

    @pytest.fixture
    def sample_raw_data(self):
        """示例原始数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(minutes=i) for i in range(10)]

        data = {
            'timestamp': timestamps,
            'symbol': ['BTC_PRICE'] * 10,
            'price': [40000, 40100, None, 40300, 40200, 40400, 40500, 40400, 40300, 40200],  # 包含空值
            'volume': [100, 150, 200, 180, 120, 300, 250, 180, 160, 140],
            'open_price': [39900, 40050, 40150, 40200, 40350, 40380, 40420, 40500, 40450, 40350],
            'high_price': [40200, 40300, 40200, 40400, 40300, 40600, 40600, 40500, 40400, 40300],
            'low_price': [39800, 40000, 40000, 40100, 40200, 40300, 40400, 40400, 40300, 40200],
            'close_price': [40100, 40150, 40200, 40300, 40250, 40400, 40500, 40450, 40350, 40250]
        }

        return pd.DataFrame(data)

    def test_init(self, cleaner):
        """测试初始化"""
        assert cleaner is not None
        assert hasattr(cleaner, 'logger')

    def test_clean_market_data_success(self, cleaner, sample_raw_data):
        """测试市场数据清洗成功"""
        cleaned_data = cleaner.clean_market_data(sample_raw_data)

        assert isinstance(cleaned_data, pd.DataFrame)
        assert not cleaned_data.empty

        # 检查空值是否被处理
        assert not cleaned_data['price'].isnull().any()

        # 检查数据类型
        assert pd.api.types.is_datetime64_any_dtype(cleaned_data['timestamp'])

    def test_clean_market_data_missing_required_columns(self, cleaner):
        """测试缺少必需列的数据"""
        invalid_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            'symbol': ['BTC'],
            # 缺少price列
        })

        with pytest.raises(DataValidationError):
            cleaner.clean_market_data(invalid_data)

    def test_clean_market_data_empty_dataframe(self, cleaner):
        """测试空数据框"""
        empty_data = pd.DataFrame()

        result = cleaner.clean_market_data(empty_data)
        assert result.empty

    def test_clean_market_data_outlier_detection(self, cleaner):
        """测试异常值检测"""
        # 创建包含异常值的数据
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(minutes=i) for i in range(20)]

        data = {
            'timestamp': timestamps,
            'symbol': ['BTC_PRICE'] * 20,
            'price': [40000] * 18 + [1000000, 0.01],  # 异常值
            'volume': [100] * 20
        }

        df = pd.DataFrame(data)
        cleaned_data = cleaner.clean_market_data(df)

        # 异常值应该被处理或标记
        assert len(cleaned_data) <= len(df)

    def test_validate_market_data_structure(self, cleaner, sample_raw_data):
        """测试数据结构验证"""
        # 有效数据应该通过验证
        is_valid, issues = cleaner.validate_market_data(sample_raw_data)
        assert is_valid or len(issues) == 0

    def test_validate_market_data_missing_columns(self, cleaner):
        """测试缺少列的验证"""
        invalid_data = pd.DataFrame({
            'timestamp': [datetime.now()],
            # 缺少symbol和price
        })

        is_valid, issues = cleaner.validate_market_data(invalid_data)
        assert not is_valid
        assert len(issues) > 0

    def test_handle_missing_values_fill(self, cleaner):
        """测试缺失值填充"""
        data = {
            'timestamp': [datetime.now(), datetime.now() + timedelta(minutes=1)],
            'symbol': ['BTC', 'BTC'],
            'price': [40000, None],
            'volume': [100, 150]
        }
        df = pd.DataFrame(data)

        result = cleaner.handle_missing_values(df, strategy='fill')

        # 空值应该被填充
        assert not result['price'].isnull().any()

    def test_detect_outliers_iqr_method(self, cleaner, sample_raw_data):
        """测试IQR异常值检测"""
        outliers = cleaner.detect_outliers(sample_raw_data, method='iqr', column='price')

        assert isinstance(outliers, pd.Series)
        assert len(outliers) == len(sample_raw_data)


class TestKlineGenerator:
    """KlineGenerator 单元测试"""

    @pytest.fixture
    def kline_generator(self):
        """K线生成器实例"""
        return KlineGenerator()

    @pytest.fixture
    def sample_tick_data(self):
        """示例tick数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        # 生成1小时的分钟级数据
        timestamps = []
        prices = []
        volumes = []

        for i in range(60):  # 60分钟
            timestamps.extend([base_time + timedelta(minutes=i) + timedelta(seconds=j)
                             for j in range(60)])  # 每分钟60个tick
            # 价格在区间内波动
            base_price = 40000 + np.sin(i / 10) * 1000
            tick_prices = np.random.normal(base_price, 100, 60)
            prices.extend(tick_prices)

            # 成交量
            volumes.extend(np.random.uniform(10, 100, 60))

        data = {
            'timestamp': timestamps,
            'symbol': ['BTC_PRICE'] * len(timestamps),
            'price': prices,
            'volume': volumes
        }

        return pd.DataFrame(data)

    def test_init(self, kline_generator):
        """测试初始化"""
        assert kline_generator is not None
        assert hasattr(kline_generator, 'logger')

    def test_generate_kline_1m(self, kline_generator, sample_tick_data):
        """测试1分钟K线生成"""
        klines = kline_generator.generate_kline(sample_tick_data, interval='1m')

        assert isinstance(klines, pd.DataFrame)
        assert not klines.empty

        # 检查必需列
        required_cols = ['timestamp', 'symbol', 'open_price', 'high_price',
                        'low_price', 'close_price', 'volume']
        test_helper.assert_required_columns(klines, required_cols)

        # 检查OHLC逻辑
        assert (klines['high_price'] >= klines['low_price']).all()
        assert (klines['high_price'] >= klines['open_price']).all()
        assert (klines['high_price'] >= klines['close_price']).all()
        assert (klines['low_price'] <= klines['open_price']).all()
        assert (klines['low_price'] <= klines['close_price']).all()

    def test_generate_kline_1h(self, kline_generator, sample_tick_data):
        """测试1小时K线生成"""
        klines = kline_generator.generate_kline(sample_tick_data, interval='1h')

        assert isinstance(klines, pd.DataFrame)
        assert not klines.empty

        # 应该有1小时的数据
        expected_count = 1
        assert len(klines) == expected_count

    def test_generate_kline_invalid_interval(self, kline_generator, sample_tick_data):
        """测试无效间隔"""
        with pytest.raises(KlineGenerationError):
            kline_generator.generate_kline(sample_tick_data, interval='invalid')

    def test_calculate_sma(self, kline_generator, sample_kline_data):
        """测试SMA计算"""
        sma = kline_generator.calculate_sma(sample_kline_data, period=5)

        assert isinstance(sma, pd.Series)
        assert len(sma) == len(sample_kline_data)

        # 前几个值应该是NaN
        assert pd.isna(sma.iloc[0])
        assert pd.isna(sma.iloc[3])  # 5周期SMA，前4个是NaN

    def test_calculate_rsi(self, kline_generator, sample_kline_data):
        """测试RSI计算"""
        rsi = kline_generator.calculate_rsi(sample_kline_data, period=14)

        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(sample_kline_data)

        # RSI应该在0-100之间
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_calculate_macd(self, kline_generator, sample_kline_data):
        """测试MACD计算"""
        macd_result = kline_generator.calculate_macd(sample_kline_data)

        assert isinstance(macd_result, dict)
        assert 'macd_line' in macd_result
        assert 'signal_line' in macd_result
        assert 'histogram' in macd_result

        # 检查长度
        assert len(macd_result['macd_line']) == len(sample_kline_data)

    def test_calculate_bollinger_bands(self, kline_generator, sample_kline_data):
        """测试布林带计算"""
        bb_result = kline_generator.calculate_bollinger_bands(sample_kline_data, period=20)

        assert isinstance(bb_result, dict)
        assert 'upper' in bb_result
        assert 'middle' in bb_result
        assert 'lower' in bb_result

        # 上轨应该高于下轨
        assert (bb_result['upper'] >= bb_result['lower']).all()

    def test_add_technical_indicators(self, kline_generator, sample_kline_data):
        """测试添加技术指标"""
        result_df = kline_generator.add_technical_indicators(sample_kline_data)

        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == len(sample_kline_data)

        # 检查是否添加了指标列
        indicator_cols = ['sma_5', 'rsi_14', 'macd_line', 'bb_upper']
        for col in indicator_cols:
            assert col in result_df.columns

    def test_resample_ohlcv(self, kline_generator, sample_tick_data):
        """测试OHLCV重采样"""
        ohlcv = kline_generator.resample_ohlcv(sample_tick_data, '5T')  # 5分钟

        assert isinstance(ohlcv, pd.DataFrame)
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        test_helper.assert_required_columns(ohlcv, required_cols)

    def test_validate_kline_data(self, kline_generator, sample_kline_data):
        """测试K线数据验证"""
        is_valid, issues = kline_generator.validate_kline_data(sample_kline_data)

        # 对于有效的K线数据应该通过验证
        assert is_valid or len(issues) == 0


class TestDataProcessingIntegration:
    """数据处理集成测试"""

    @pytest.fixture
    def processing_pipeline(self, cleaner, kline_generator):
        """处理管道"""
        return {
            'cleaner': cleaner,
            'kline_generator': kline_generator
        }

    def test_full_processing_pipeline(self, processing_pipeline, sample_raw_data):
        """测试完整处理管道"""
        cleaner = processing_pipeline['cleaner']
        kline_gen = processing_pipeline['kline_generator']

        # 1. 清洗数据
        cleaned_data = cleaner.clean_market_data(sample_raw_data)
        assert not cleaned_data.empty

        # 2. 生成K线
        klines = kline_gen.generate_kline(cleaned_data, interval='5m')
        assert not klines.empty

        # 3. 添加技术指标
        with_indicators = kline_gen.add_technical_indicators(klines)
        assert not with_indicators.empty

        # 检查最终结果
        assert len(with_indicators.columns) > len(klines.columns)

    def test_error_handling_in_pipeline(self, processing_pipeline):
        """测试管道中的错误处理"""
        cleaner = processing_pipeline['cleaner']

        # 测试无效数据
        invalid_data = pd.DataFrame({
            'invalid_column': [1, 2, 3]
        })

        # 应该抛出验证错误
        with pytest.raises(DataValidationError):
            cleaner.clean_market_data(invalid_data)


class TestDataProcessingEdgeCases:
    """数据处理边界情况测试"""

    @pytest.fixture
    def cleaner(self):
        return DataCleaner()

    @pytest.fixture
    def kline_generator(self):
        return KlineGenerator()

    def test_empty_dataframe_handling(self, cleaner, kline_generator):
        """测试空数据框处理"""
        empty_df = pd.DataFrame()

        # 清洗器应该返回空数据框
        result = cleaner.clean_market_data(empty_df)
        assert result.empty

        # K线生成器应该抛出错误
        with pytest.raises(KlineGenerationError):
            kline_generator.generate_kline(empty_df)

    def test_single_row_data(self, cleaner, kline_generator):
        """测试单行数据"""
        single_row = pd.DataFrame({
            'timestamp': [datetime.now()],
            'symbol': ['BTC'],
            'price': [40000],
            'volume': [100]
        })

        # 应该能够处理单行数据
        cleaned = cleaner.clean_market_data(single_row)
        assert len(cleaned) == 1

    def test_duplicate_timestamps(self, cleaner):
        """测试重复时间戳"""
        duplicate_time = datetime.now()
        data = {
            'timestamp': [duplicate_time, duplicate_time, duplicate_time + timedelta(minutes=1)],
            'symbol': ['BTC', 'BTC', 'BTC'],
            'price': [40000, 40100, 40200]
        }
        df = pd.DataFrame(data)

        cleaned = cleaner.clean_market_data(df)

        # 应该去重
        assert len(cleaned) <= len(df)

    def test_extreme_values(self, cleaner):
        """测试极端值"""
        data = {
            'timestamp': [datetime.now(), datetime.now() + timedelta(minutes=1)],
            'symbol': ['BTC', 'BTC'],
            'price': [1e-10, 1e20],  # 极端价格
            'volume': [0, 1e15]     # 极端成交量
        }
        df = pd.DataFrame(data)

        cleaned = cleaner.clean_market_data(df)

        # 应该处理极端值
        assert not cleaned.empty
