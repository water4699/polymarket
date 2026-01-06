"""
Polymarket 数据源
用于获取 Polymarket 预测市场数据
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from config import config
from .base import BaseDataSource, DataSourceError


class PolymarketDataSource(BaseDataSource):
    """Polymarket 预测市场数据源"""

    def __init__(self):
        super().__init__(
            name="Polymarket",
            config={
                "api_key": config.api.POLYMARKET_API_KEY,
                "base_url": config.api.POLYMARKET_BASE_URL,
                "timeout": 30
            }
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """连接到 Polymarket API"""
        try:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.get('api_key', '')}",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
            )
            self.is_connected = True
            self.logger.info("成功连接到 Polymarket API")
            return True
        except Exception as e:
            self.logger.error(f"连接 Polymarket API 失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.is_connected = False
            self.logger.info("已断开 Polymarket API 连接")

    async def fetch_data(
        self,
        market_slug: str,
        start_time: datetime,
        end_time: datetime,
        data_type: str = "price"
    ) -> pd.DataFrame:
        """
        获取市场数据

        Args:
            market_slug: 市场标识
            start_time: 开始时间
            end_time: 结束时间
            data_type: 数据类型

        Returns:
            数据框
        """
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Polymarket API")

        try:
            url = f"{self.config['base_url']}/markets/{market_slug}/price-history"
            params = {
                "start_date": start_time.strftime("%Y-%m-%d"),
                "end_date": end_time.strftime("%Y-%m-%d")
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return pd.DataFrame(data)
                else:
                    raise DataSourceError(f"API 请求失败: {response.status}")

        except Exception as e:
            self.logger.error(f"获取 Polymarket 数据失败: {e}")
            # 返回模拟数据
            return self._get_mock_data(market_slug, start_time, end_time)

    async def get_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取市场列表"""
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Polymarket API")

        try:
            url = f"{self.config['base_url']}/markets"
            params = {"limit": limit}

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("markets", [])
                else:
                    raise DataSourceError(f"获取市场列表失败: {response.status}")
        except Exception as e:
            self.logger.error(f"获取市场列表失败: {e}")
            # 返回模拟数据
            return [
                {"slug": "will-btc-exceed-100k", "name": "Will BTC exceed $100k?", "status": "active"},
                {"slug": "presidential-election", "name": "2024 US Presidential Election", "status": "active"}
            ]

    async def get_symbols(self) -> List[str]:
        """获取可用的市场符号"""
        markets = await self.get_markets()
        return [market["slug"] for market in markets]

    def _get_mock_data(
        self,
        market_slug: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """生成模拟数据"""
        import numpy as np

        timestamps = pd.date_range(start_time, end_time, freq='1H')

        # 生成 Yes/No 概率数据
        np.random.seed(42)
        yes_probs = []
        current_yes_prob = 0.5

        for _ in timestamps:
            change = np.random.normal(0, 0.01)
            current_yes_prob = np.clip(current_yes_prob + change, 0.01, 0.99)
            yes_probs.append(current_yes_prob)

        return pd.DataFrame({
            "timestamp": timestamps,
            "yes_probability": yes_probs,
            "no_probability": [1 - p for p in yes_probs],
            "volume": np.random.uniform(10000, 100000, len(timestamps)),
            "market_slug": market_slug
        })
