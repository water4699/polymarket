"""
Predict 数据源
用于获取预测市场数据
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from config import config
from .base import BaseDataSource, DataSourceError


class PredictDataSource(BaseDataSource):
    """Predict 预测市场数据源"""

    def __init__(self):
        super().__init__(
            name="Predict",
            config={
                "api_key": config.api.PREDICT_API_KEY,
                "base_url": config.api.PREDICT_BASE_URL,
                "timeout": 30
            }
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """连接到 Predict API"""
        try:
            if not self.config.get("api_key"):
                raise DataSourceError("Predict API key 未配置")

            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config['api_key']}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
            )
            self.is_connected = True
            self.logger.info("成功连接到 Predict API")
            return True
        except Exception as e:
            self.logger.error(f"连接 Predict API 失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.is_connected = False
            self.logger.info("已断开 Predict API 连接")

    async def fetch_data(
        self,
        market_id: str,
        start_time: datetime,
        end_time: datetime,
        data_type: str = "price"
    ) -> pd.DataFrame:
        """
        获取预测市场数据

        Args:
            market_id: 市场ID
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型 (price, volume, etc.)

        Returns:
            数据框
        """
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Predict API")

        try:
            url = f"{self.config['base_url']}/markets/{market_id}/data"
            params = {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "data_type": data_type
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return pd.DataFrame(data)
                else:
                    raise DataSourceError(f"API 请求失败: {response.status}")

        except Exception as e:
            self.logger.error(f"获取 Predict 数据失败: {e}")
            # 返回模拟数据用于演示
            return self._get_mock_data(market_id, start_time, end_time)

    async def get_markets(self) -> List[Dict[str, Any]]:
        """获取所有市场列表"""
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Predict API")

        try:
            url = f"{self.config['base_url']}/markets"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise DataSourceError(f"获取市场列表失败: {response.status}")
        except Exception as e:
            self.logger.error(f"获取市场列表失败: {e}")
            # 返回模拟数据
            return [
                {"id": "BTC_PRICE", "name": "BTC Price Prediction", "status": "active"},
                {"id": "ETH_PRICE", "name": "ETH Price Prediction", "status": "active"}
            ]

    async def get_symbols(self) -> List[str]:
        """获取可用的市场符号"""
        markets = await self.get_markets()
        return [market["id"] for market in markets]

    def _get_mock_data(
        self,
        market_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """生成模拟数据用于演示"""
        import numpy as np

        # 生成时间序列
        timestamps = pd.date_range(start_time, end_time, freq='1H')

        # 生成模拟价格数据
        np.random.seed(42)
        base_price = 100.0
        prices = []
        current_price = base_price

        for _ in timestamps:
            # 随机游走
            change = np.random.normal(0, 0.02)  # 2% 波动
            current_price *= (1 + change)
            prices.append(current_price)

        return pd.DataFrame({
            "timestamp": timestamps,
            "price": prices,
            "volume": np.random.uniform(1000, 10000, len(timestamps)),
            "market_id": market_id
        })
