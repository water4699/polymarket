"""
测试辅助工具和模拟数据生成器
提供测试所需的数据生成、断言和工具函数
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import random
import string


@dataclass
class MarketDataSpec:
    """市场数据规格"""
    symbol: str
    base_price: float = 40000.0
    volatility: float = 0.02
    trend: float = 0.0001
    volume_base: float = 1000.0
    volume_volatility: float = 0.5
    data_points: int = 100
    interval_minutes: int = 1


class TestDataGenerator:
    """测试数据生成器"""

    @staticmethod
    def generate_market_data(spec: MarketDataSpec) -> pd.DataFrame:
        """生成市场数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        timestamps = []
        prices = []
        volumes = []
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []

        current_price = spec.base_price

        for i in range(spec.data_points):
            timestamp = base_time + timedelta(minutes=i * spec.interval_minutes)
            timestamps.append(timestamp)

            # 生成价格变动
            price_change = np.random.normal(
                spec.trend * spec.interval_minutes,
                spec.volatility * np.sqrt(spec.interval_minutes)
            )
            current_price *= (1 + price_change)

            # 生成OHLC
            daily_volatility = spec.volatility * np.sqrt(spec.interval_minutes)
            open_price = current_price
            close_price = current_price * (1 + np.random.normal(0, daily_volatility))

            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, daily_volatility)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, daily_volatility)))

            open_prices.append(open_price)
            high_prices.append(high_price)
            low_prices.append(low_price)
            close_prices.append(close_price)

            # 生成成交量
            volume = spec.volume_base * (1 + np.random.normal(0, spec.volume_volatility))
            volumes.append(max(volume, 1))  # 确保成交量为正

        return pd.DataFrame({
            'timestamp': timestamps,
            'symbol': [spec.symbol] * spec.data_points,
            'price': close_prices,  # 当前价格使用收盘价
            'volume': volumes,
            'open_price': open_prices,
            'high_price': high_prices,
            'low_price': low_prices,
            'close_price': close_prices
        })

    @staticmethod
    def generate_kline_data(symbol: str, interval: str, periods: int = 100) -> pd.DataFrame:
        """生成K线数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)

        timestamps = []
        open_prices = []
        high_prices = []
        low_prices = []
        close_prices = []
        volumes = []

        current_price = 40000.0

        # 根据间隔计算时间增量
        if interval == '1m':
            delta = timedelta(minutes=1)
        elif interval == '5m':
            delta = timedelta(minutes=5)
        elif interval == '1h':
            delta = timedelta(hours=1)
        elif interval == '1d':
            delta = timedelta(days=1)
        else:
            delta = timedelta(hours=1)

        for i in range(periods):
            timestamp = base_time + i * delta
            timestamps.append(timestamp)

            # 生成OHLCV
            volatility = 0.01
            trend = 0.0001

            open_price = current_price
            price_changes = np.random.normal(trend, volatility, 4)
            prices = [open_price * (1 + change) for change in price_changes]
            prices.sort()

            low_price, _, _, high_price = prices
            close_price = prices[-1] * (1 + np.random.normal(0, volatility))

            # 确保逻辑正确
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            open_prices.append(open_price)
            high_prices.append(high_price)
            low_prices.append(low_price)
            close_prices.append(close_price)

            current_price = close_price

            # 成交量
            volume = np.random.uniform(100, 10000)
            volumes.append(volume)

        return pd.DataFrame({
            'timestamp': timestamps,
            'symbol': [symbol] * periods,
            'interval_type': [interval] * periods,
            'open_price': open_prices,
            'high_price': high_prices,
            'low_price': low_prices,
            'close_price': close_prices,
            'volume': volumes,
            'trade_count': np.random.randint(10, 1000, periods)
        })

    @staticmethod
    def generate_technical_indicators(kline_data: pd.DataFrame) -> pd.DataFrame:
        """生成技术指标数据"""
        df = kline_data.copy()

        # 简单移动平均线
        df['sma_5'] = df['close_price'].rolling(window=5).mean()
        df['sma_10'] = df['close_price'].rolling(window=10).mean()
        df['sma_20'] = df['close_price'].rolling(window=20).mean()

        # RSI
        def calculate_rsi(prices, period=14):
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        df['rsi_14'] = calculate_rsi(df['close_price'], 14)

        # MACD
        ema_12 = df['close_price'].ewm(span=12).mean()
        ema_26 = df['close_price'].ewm(span=26).mean()
        df['macd_line'] = ema_12 - ema_26
        df['macd_signal'] = df['macd_line'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd_line'] - df['macd_signal']

        # 布林带
        sma_20 = df['close_price'].rolling(window=20).mean()
        std_20 = df['close_price'].rolling(window=20).std()
        df['bb_middle'] = sma_20
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

        # 威廉指标
        df['williams_r'] = -100 * ((df['high_price'].rolling(14).max() - df['close_price']) /
                                  (df['high_price'].rolling(14).max() - df['low_price'].rolling(14).min()))

        # 随机指标
        df['stoch_k'] = 100 * ((df['close_price'] - df['low_price'].rolling(14).min()) /
                              (df['high_price'].rolling(14).max() - df['low_price'].rolling(14).min()))
        df['stoch_d'] = df['stoch_k'].rolling(3).mean()

        # OBV
        df['obv'] = (np.sign(df['close_price'].diff()) * df['volume']).cumsum()

        # 价格变化
        df['price_change_1d'] = df['close_price'].pct_change(24)  # 假设1小时数据
        df['price_change_7d'] = df['close_price'].pct_change(168)

        # 波动率
        df['volatility_7d'] = df['close_price'].pct_change().rolling(168).std() * np.sqrt(168)
        df['volatility_30d'] = df['close_price'].pct_change().rolling(720).std() * np.sqrt(720)

        return df

    @staticmethod
    def generate_trading_signals(kline_data: pd.DataFrame, strategy: str = 'ma_cross') -> pd.DataFrame:
        """生成交易信号"""
        df = kline_data.copy()

        if strategy == 'ma_cross':
            # 移动平均线交叉策略
            df['sma_short'] = df['close_price'].rolling(5).mean()
            df['sma_long'] = df['close_price'].rolling(20).mean()

            df['signal'] = 0
            df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1   # 买入
            df.loc[df['sma_short'] < df['sma_long'], 'signal'] = -1  # 卖出

        elif strategy == 'rsi':
            # RSI策略
            def calculate_rsi(prices, period=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))

            df['rsi'] = calculate_rsi(df['close_price'])

            df['signal'] = 0
            df.loc[df['rsi'] < 30, 'signal'] = 1   # 买入
            df.loc[df['rsi'] > 70, 'signal'] = -1  # 卖出

        elif strategy == 'mean_reversion':
            # 均值回归策略
            df['sma'] = df['close_price'].rolling(20).mean()
            df['std'] = df['close_price'].rolling(20).std()
            df['z_score'] = (df['close_price'] - df['sma']) / df['std']

            df['signal'] = 0
            df.loc[df['z_score'] < -2, 'signal'] = 1   # 买入
            df.loc[df['z_score'] > 2, 'signal'] = -1   # 卖出

        else:
            df['signal'] = 0  # 默认无信号

        return df

    @staticmethod
    def generate_api_response(source_type: str, symbol: str, data_points: int = 10) -> Dict[str, Any]:
        """生成API响应数据"""
        if source_type == 'predict':
            return {
                'data': [
                    {
                        'timestamp': (datetime.now() - timedelta(minutes=i)).isoformat(),
                        'symbol': symbol,
                        'price': 40000 + np.random.uniform(-1000, 1000),
                        'volume': np.random.uniform(100, 10000),
                        'open_price': 40000 + np.random.uniform(-1000, 1000),
                        'high_price': 41000 + np.random.uniform(0, 1000),
                        'low_price': 39000 + np.random.uniform(-1000, 0),
                        'close_price': 40000 + np.random.uniform(-1000, 1000)
                    } for i in range(data_points)
                ]
            }
        elif source_type == 'polymarket':
            return {
                'markets': [
                    {
                        'id': f'market_{i}',
                        'question': f'Will {symbol} exceed ${40000 + i*1000}?',
                        'endDate': (datetime.now() + timedelta(days=30)).isoformat(),
                        'yesPrice': np.random.uniform(0.1, 0.9),
                        'noPrice': 1 - np.random.uniform(0.1, 0.9),
                        'volume': np.random.uniform(10000, 1000000)
                    } for i in range(data_points)
                ]
            }

        return {}

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def generate_random_hash() -> str:
        """生成随机哈希"""
        return TestDataGenerator.generate_random_string(64)

    @staticmethod
    def add_noise_to_data(df: pd.DataFrame, columns: List[str], noise_level: float = 0.01) -> pd.DataFrame:
        """为数据添加噪声"""
        df_noisy = df.copy()

        for col in columns:
            if col in df_noisy.columns:
                noise = np.random.normal(0, noise_level, len(df_noisy))
                df_noisy[col] = df_noisy[col] * (1 + noise)

        return df_noisy

    @staticmethod
    def create_outliers(df: pd.DataFrame, columns: List[str], outlier_fraction: float = 0.05) -> pd.DataFrame:
        """创建异常值"""
        df_outliers = df.copy()
        n_outliers = int(len(df) * outlier_fraction)

        for col in columns:
            if col in df_outliers.columns:
                outlier_indices = np.random.choice(len(df), n_outliers, replace=False)

                # 创建极端值
                original_values = df_outliers.loc[outlier_indices, col]
                outlier_values = original_values * np.random.choice([0.01, 100], n_outliers)

                df_outliers.loc[outlier_indices, col] = outlier_values

        return df_outliers


class TestAssertions:
    """测试断言工具"""

    @staticmethod
    def assert_dataframe_structure(df: pd.DataFrame, expected_columns: List[str],
                                 expected_types: Dict[str, str] = None):
        """断言DataFrame结构"""
        # 检查列是否存在
        missing_cols = [col for col in expected_columns if col not in df.columns]
        assert not missing_cols, f"缺少列: {missing_cols}"

        # 检查数据类型
        if expected_types:
            for col, expected_type in expected_types.items():
                if col in df.columns:
                    if expected_type == 'datetime':
                        assert pd.api.types.is_datetime64_any_dtype(df[col]), f"列 {col} 不是日期时间类型"
                    elif expected_type == 'numeric':
                        assert pd.api.types.is_numeric_dtype(df[col]), f"列 {col} 不是数值类型"
                    elif expected_type == 'string':
                        assert pd.api.types.is_string_dtype(df[col]), f"列 {col} 不是字符串类型"

    @staticmethod
    def assert_ohlcv_integrity(df: pd.DataFrame):
        """断言OHLCV数据完整性"""
        required_cols = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
        TestAssertions.assert_dataframe_structure(df, required_cols)

        # 检查OHLC逻辑
        assert (df['high_price'] >= df['open_price']).all(), "High price should be >= open price"
        assert (df['high_price'] >= df['close_price']).all(), "High price should be >= close price"
        assert (df['low_price'] <= df['open_price']).all(), "Low price should be <= open price"
        assert (df['low_price'] <= df['close_price']).all(), "Low price should be <= close price"
        assert (df['volume'] >= 0).all(), "Volume should be non-negative"

    @staticmethod
    def assert_signals_valid(df: pd.DataFrame):
        """断言交易信号有效性"""
        assert 'signal' in df.columns, "Missing signal column"

        valid_signals = [-1, 0, 1]
        invalid_signals = df[~df['signal'].isin(valid_signals)]['signal'].unique()
        assert len(invalid_signals) == 0, f"Invalid signals found: {invalid_signals}"

    @staticmethod
    def assert_technical_indicators(df: pd.DataFrame, indicators: List[str]):
        """断言技术指标存在"""
        missing_indicators = [ind for ind in indicators if ind not in df.columns]
        assert not missing_indicators, f"Missing technical indicators: {missing_indicators}"

    @staticmethod
    def assert_backtest_results(results: Dict[str, Any]):
        """断言回测结果有效性"""
        required_keys = ['total_return', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'total_trades']

        missing_keys = [key for key in required_keys if key not in results]
        assert not missing_keys, f"Missing backtest result keys: {missing_keys}"

        # 检查数值合理性
        assert isinstance(results['total_return'], (int, float)), "total_return should be numeric"
        assert isinstance(results['win_rate'], (int, float)), "win_rate should be numeric"
        assert 0 <= results['win_rate'] <= 1, "win_rate should be between 0 and 1"

    @staticmethod
    def assert_api_response_structure(response: Dict[str, Any], expected_keys: List[str]):
        """断言API响应结构"""
        missing_keys = [key for key in expected_keys if key not in response]
        assert not missing_keys, f"Missing API response keys: {missing_keys}"

    @staticmethod
    def assert_exception_raised(func, exception_class, *args, **kwargs):
        """断言异常被抛出"""
        with pytest.raises(exception_class):
            func(*args, **kwargs)


class MockFactory:
    """模拟对象工厂"""

    @staticmethod
    def create_mock_data_source(success: bool = True):
        """创建模拟数据源"""
        from unittest.mock import MagicMock, AsyncMock

        mock_ds = MagicMock()
        mock_ds.name = "mock_data_source"
        mock_ds.is_connected = success
        mock_ds.connect = AsyncMock(return_value=success)
        mock_ds.disconnect = AsyncMock()

        if success:
            mock_ds.get_symbols = AsyncMock(return_value=["BTC_PRICE", "ETH_PRICE"])
            mock_ds.fetch_data = AsyncMock(return_value=TestDataGenerator.generate_market_data(
                MarketDataSpec(symbol="BTC_PRICE", data_points=10)
            ))
        else:
            mock_ds.get_symbols = AsyncMock(side_effect=Exception("Connection failed"))
            mock_ds.fetch_data = AsyncMock(side_effect=Exception("Fetch failed"))

        return mock_ds

    @staticmethod
    def create_mock_storage(success: bool = True):
        """创建模拟存储器"""
        from unittest.mock import MagicMock, AsyncMock

        mock_store = MagicMock()
        mock_store.is_connected = success
        mock_store.connect = AsyncMock(return_value=success)
        mock_store.disconnect = AsyncMock()

        if success:
            mock_store.insert_raw_market_data = AsyncMock(return_value=True)
            mock_store.get_raw_market_data = AsyncMock(return_value=pd.DataFrame())
            mock_store.insert_clean_market_data = AsyncMock(return_value=True)
            mock_store.get_clean_market_data = AsyncMock(return_value=pd.DataFrame())
            mock_store.insert_kline_data = AsyncMock(return_value=True)
            mock_store.get_klines = AsyncMock(return_value=pd.DataFrame())
        else:
            mock_store.insert_raw_market_data = AsyncMock(side_effect=Exception("Storage failed"))

        return mock_store

    @staticmethod
    def create_mock_api_response(status_code: int = 200, data: Dict[str, Any] = None):
        """创建模拟API响应"""
        from unittest.mock import MagicMock

        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data or {}

        return mock_response
