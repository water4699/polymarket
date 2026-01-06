"""
数据清洗模块
提供数据清洗、验证和预处理功能
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from utils.logger import LoggerMixin


class DataCleaner(LoggerMixin):
    """数据清洗器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化数据清洗器

        Args:
            config: 清洗配置
        """
        self.config = config or {}
        self.logger.info("初始化数据清洗器")

    def clean_market_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗市场数据

        Args:
            df: 原始数据框

        Returns:
            清洗后的数据框
        """
        try:
            df = df.copy()

            # 1. 处理时间戳
            df = self._standardize_timestamps(df)

            # 2. 处理缺失值
            df = self._handle_missing_values(df)

            # 3. 移除异常值
            df = self._remove_outliers(df)

            # 4. 数据类型转换
            df = self._convert_data_types(df)

            # 5. 排序
            df = self._sort_data(df)

            self.logger.info(f"数据清洗完成，原始数据 {len(df)} 行")
            return df

        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            return df

    def clean_onchain_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗链上数据

        Args:
            df: 原始链上数据

        Returns:
            清洗后的数据
        """
        try:
            df = df.copy()

            # 1. 标准化地址格式
            df = self._standardize_addresses(df)

            # 2. 处理数值字段
            df = self._handle_numeric_fields(df)

            # 3. 移除无效交易
            df = self._remove_invalid_transactions(df)

            # 4. 添加计算字段
            df = self._add_calculated_fields(df)

            self.logger.info(f"链上数据清洗完成，原始数据 {len(df)} 行")
            return df

        except Exception as e:
            self.logger.error(f"链上数据清洗失败: {e}")
            return df

    def _standardize_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化时间戳"""
        timestamp_columns = ['timestamp', 'created_at', 'updated_at', 'block_timestamp']

        for col in timestamp_columns:
            if col in df.columns:
                # 尝试多种时间格式转换
                try:
                    if df[col].dtype == 'object':
                        # 字符串转时间戳
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    elif df[col].dtype in ['int64', 'float64']:
                        # 时间戳数字转datetime
                        df[col] = pd.to_datetime(df[col], unit='s', errors='coerce')
                except Exception as e:
                    self.logger.warning(f"时间戳转换失败 {col}: {e}")

        return df

    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        # 删除完全为空的行
        df = df.dropna(how='all')

        # 对数值列进行插值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if df[col].isnull().sum() > 0:
                # 使用前向填充
                df[col] = df[col].fillna(method='ffill')
                # 如果还有NaN，使用均值填充
                df[col] = df[col].fillna(df[col].mean())

        # 对分类列使用众数填充
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if df[col].isnull().sum() > 0:
                mode_value = df[col].mode()
                if not mode_value.empty:
                    df[col] = df[col].fillna(mode_value[0])

        return df

    def _remove_outliers(self, df: pd.DataFrame, z_threshold: float = 3.0) -> pd.DataFrame:
        """移除异常值"""
        numeric_columns = ['price', 'volume', 'value', 'amount']

        for col in numeric_columns:
            if col in df.columns:
                # 使用Z-score方法检测异常值
                if df[col].dtype in ['int64', 'float64']:
                    z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                    df = df[z_scores < z_threshold]

        return df

    def _convert_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换数据类型"""
        # 确保价格和数量字段是浮点数
        float_columns = ['price', 'volume', 'value', 'amount', 'yes_probability', 'no_probability']
        for col in float_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 确保地址字段是字符串
        address_columns = ['from', 'to', 'contract_address']
        for col in address_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower()

        return df

    def _sort_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """排序数据"""
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        elif 'block_number' in df.columns:
            df = df.sort_values('block_number').reset_index(drop=True)

        return df

    def _standardize_addresses(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化地址格式"""
        address_columns = ['from', 'to', 'contract_address', 'address']

        for col in address_columns:
            if col in df.columns:
                # 确保以0x开头，转小写
                df[col] = df[col].astype(str).apply(
                    lambda x: x.lower() if x.startswith('0x') else f"0x{x.lower()}" if x else x
                )

        return df

    def _handle_numeric_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理数值字段"""
        # 处理区块链数值（通常是字符串表示的wei单位）
        wei_columns = ['value', 'amount']
        for col in wei_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 处理gas价格等
        gas_columns = ['gas_price', 'gas_used']
        for col in gas_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def _remove_invalid_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除无效交易"""
        # 移除价值为0的交易
        if 'value' in df.columns:
            df = df[df['value'] > 0]

        # 移除无效地址
        address_columns = ['from', 'to']
        for col in address_columns:
            if col in df.columns:
                # 移除空地址或无效地址
                df = df[df[col].notna() & (df[col].str.len() == 42)]

        return df

    def _add_calculated_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加计算字段"""
        # 计算交易价值（ETH）
        if 'value' in df.columns:
            # 假设value是wei单位，除以10^18转换为ETH
            df['value_eth'] = df['value'] / 10**18

        # 计算gas费用
        if 'gas_price' in df.columns and 'gas_used' in df.columns:
            df['gas_fee'] = df['gas_price'] * df['gas_used'] / 10**18

        return df
