"""
数据源基础模块
定义数据源接口和基础类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from utils.logger import LoggerMixin
from utils.exceptions import DataSourceError, DataSourceConnectionError, DataFetchError, APIKeyError
from utils.error_handler import handle_errors, safe_call


class BaseDataSource(ABC, LoggerMixin):
    """数据源基础抽象类"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化数据源

        Args:
            name: 数据源名称
            config: 配置参数
        """
        self.name = name
        self.config = config or {}
        self.is_connected = False
        self.logger.info(f"初始化数据源: {name}")

    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据源"""
        pass

    @abstractmethod
    async def disconnect(self):
        """断开数据源连接"""
        pass

    @abstractmethod
    async def fetch_data(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1m"
    ) -> pd.DataFrame:
        """
        获取数据

        Args:
            symbol: 交易对/市场符号
            start_time: 开始时间
            end_time: 结束时间
            interval: 时间间隔

        Returns:
            数据框
        """
        pass

    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """获取可用的交易对列表"""
        pass

    @handle_errors("validate_config")
    def validate_config(self) -> bool:
        """验证配置"""
        return True

    @handle_errors("health_check", raise_errors=False)
    async def health_check(self) -> bool:
        """健康检查"""
        symbols = await safe_async_call(self.get_symbols, default_return=[])
        return len(symbols) > 0
