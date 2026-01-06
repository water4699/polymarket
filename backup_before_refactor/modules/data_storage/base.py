"""
数据存储基础模块
定义数据存储接口和基础类
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
from utils.logger import LoggerMixin


class StorageError(Exception):
    """存储异常"""
    pass


class BaseStorage(ABC, LoggerMixin):
    """数据存储基础抽象类"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化存储

        Args:
            name: 存储名称
            config: 配置参数
        """
        self.name = name
        self.config = config or {}
        self.is_connected = False
        self.logger.info(f"初始化存储: {name}")

    @abstractmethod
    async def connect(self) -> bool:
        """连接到存储"""
        pass

    @abstractmethod
    async def disconnect(self):
        """断开存储连接"""
        pass

    @abstractmethod
    async def insert_data(
        self,
        table_name: str,
        data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """
        插入数据

        Args:
            table_name: 表名/集合名
            data: 要插入的数据

        Returns:
            是否成功
        """
        pass

    @abstractmethod
    async def query_data(
        self,
        table_name: str,
        filters: Dict[str, Any] = None,
        limit: int = None,
        sort_by: str = None,
        ascending: bool = True
    ) -> pd.DataFrame:
        """
        查询数据

        Args:
            table_name: 表名/集合名
            filters: 过滤条件
            limit: 限制数量
            sort_by: 排序字段
            ascending: 是否升序

        Returns:
            查询结果
        """
        pass

    @abstractmethod
    async def update_data(
        self,
        table_name: str,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """
        更新数据

        Args:
            filters: 过滤条件
            update_data: 更新数据

        Returns:
            更新的行数
        """
        pass

    @abstractmethod
    async def delete_data(
        self,
        table_name: str,
        filters: Dict[str, Any]
    ) -> int:
        """
        删除数据

        Args:
            filters: 过滤条件

        Returns:
            删除的行数
        """
        pass

    def validate_config(self) -> bool:
        """验证配置"""
        return True

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 尝试简单的查询操作
            test_data = {"test": "health_check", "timestamp": datetime.now()}
            await self.insert_data("health_check", test_data)
            result = await self.query_data("health_check", {"test": "health_check"})
            await self.delete_data("health_check", {"test": "health_check"})
            return len(result) > 0
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return False
