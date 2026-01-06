"""
K线生成模块
生成各种时间间隔的K线数据
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from utils.logger import LoggerMixin


class KlineGenerator(LoggerMixin):
    """K线生成器"""

    # 支持的时间间隔
    INTERVALS = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '1h': '1H',
        '4h': '4H',
        '1d': '1D',
        '1w': '1W',
        '1M': '1M'
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化K线生成器

        Args:
            config: 生成配置
        """
        self.config = config or {}
        self.logger.info("初始化K线生成器")

    def generate_klines(
        self,
        df: pd.DataFrame,
        interval: str,
        price_col: str = 'price',
        volume_col: str = 'volume',
        timestamp_col: str = 'timestamp'
    ) -> pd.DataFrame:
        """
        生成K线数据

        Args:
            df: 原始数据框
            interval: 时间间隔 ('1m', '5m', '1h', etc.)
            price_col: 价格列名
            volume_col: 交易量列名
            timestamp_col: 时间戳列名

        Returns:
            K线数据框
        """
        try:
            if df.empty:
                return pd.DataFrame()

            # 确保时间戳是datetime类型
            df = df.copy()
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])

            # 设置时间戳为索引
            df = df.set_index(timestamp_col)

            # 获取pandas频率字符串
            freq = self.INTERVALS.get(interval)
            if not freq:
                raise ValueError(f"不支持的时间间隔: {interval}")

            # 重采样生成K线
            kline_data = df.resample(freq).agg({
                price_col: ['first', 'last', 'max', 'min'],
                volume_col: 'sum' if volume_col in df.columns else 'count'
            })

            # 展平多层列名
            kline_data.columns = ['open', 'close', 'high', 'low', 'volume']

            # 重置索引
            kline_data = kline_data.reset_index()

            # 添加时间戳列
            kline_data['timestamp'] = kline_data[timestamp_col]

            # 重新排列列
            columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            kline_data = kline_data[columns]

            # 移除NaN值
            kline_data = kline_data.dropna()

            self.logger.info(f"生成 {interval} K线数据，{len(kline_data)} 条记录")
            return kline_data

        except Exception as e:
            self.logger.error(f"生成K线失败: {e}")
            return pd.DataFrame()

    def generate_multi_interval_klines(
        self,
        df: pd.DataFrame,
        intervals: List[str],
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        生成多个时间间隔的K线

        Args:
            df: 原始数据框
            intervals: 时间间隔列表
            **kwargs: 传递给generate_klines的参数

        Returns:
            间隔到K线数据的映射
        """
        results = {}
        for interval in intervals:
            try:
                kline_data = self.generate_klines(df, interval, **kwargs)
                if not kline_data.empty:
                    results[interval] = kline_data
            except Exception as e:
                self.logger.error(f"生成 {interval} K线失败: {e}")

        return results

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        添加技术指标

        Args:
            df: K线数据框

        Returns:
            包含技术指标的K线数据
        """
        try:
            df = df.copy()

            # 移动平均线
            df['ma5'] = df['close'].rolling(window=5).mean()
            df['ma10'] = df['close'].rolling(window=10).mean()
            df['ma20'] = df['close'].rolling(window=20).mean()

            # RSI
            df['rsi'] = self._calculate_rsi(df['close'])

            # MACD
            macd_data = self._calculate_macd(df['close'])
            df = pd.concat([df, macd_data], axis=1)

            # 布林带
            bb_data = self._calculate_bollinger_bands(df['close'])
            df = pd.concat([df, bb_data], axis=1)

            self.logger.info("添加技术指标完成")
            return df

        except Exception as e:
            self.logger.error(f"添加技术指标失败: {e}")
            return df

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(
        self,
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """计算MACD指标"""
        fast_ema = prices.ewm(span=fast_period, adjust=False).mean()
        slow_ema = prices.ewm(span=slow_period, adjust=False).mean()
        macd = fast_ema - slow_ema
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal

        return pd.DataFrame({
            'macd': macd,
            'macd_signal': signal,
            'macd_histogram': histogram
        })

    def _calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: int = 2
    ) -> pd.DataFrame:
        """计算布林带"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return pd.DataFrame({
            'bb_upper': upper_band,
            'bb_middle': sma,
            'bb_lower': lower_band
        })

    def resample_klines(
        self,
        df: pd.DataFrame,
        from_interval: str,
        to_interval: str
    ) -> pd.DataFrame:
        """
        将K线数据重采样到更大的时间间隔

        Args:
            df: 原始K线数据
            from_interval: 原始间隔
            to_interval: 目标间隔

        Returns:
            重采样后的K线数据
        """
        try:
            # 将timestamp设为索引
            df = df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')

            # 获取目标频率
            to_freq = self.INTERVALS.get(to_interval)
            if not to_freq:
                raise ValueError(f"不支持的目标间隔: {to_interval}")

            # 重采样
            resampled = df.resample(to_freq).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            })

            # 重置索引
            resampled = resampled.reset_index()

            self.logger.info(f"K线重采样完成: {from_interval} -> {to_interval}")
            return resampled

        except Exception as e:
            self.logger.error(f"K线重采样失败: {e}")
            return df
