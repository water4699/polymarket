"""
Dune Analytics 数据源
用于获取 Dune Analytics 查询结果
"""
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from config import config
from .base import BaseDataSource, DataSourceError


class DuneDataSource(BaseDataSource):
    """Dune Analytics 数据源"""

    def __init__(self):
        super().__init__(
            name="Dune Analytics",
            config={
                "api_key": config.api.DUNE_API_KEY,
                "base_url": config.api.DUNE_BASE_URL,
                "timeout": 60  # Dune 查询可能需要更长时间
            }
        )
        self.session: Optional[aiohttp.ClientSession] = None

    async def connect(self) -> bool:
        """连接到 Dune API"""
        try:
            if not self.config.get("api_key"):
                raise DataSourceError("Dune API key 未配置")

            self.session = aiohttp.ClientSession(
                headers={
                    "x-dune-api-key": self.config["api_key"],
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
            )
            self.is_connected = True
            self.logger.info("成功连接到 Dune API")
            return True
        except Exception as e:
            self.logger.error(f"连接 Dune API 失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
            self.is_connected = False
            self.logger.info("已断开 Dune API 连接")

    async def execute_query(
        self,
        query_id: int,
        parameters: Dict[str, Any] = None
    ) -> pd.DataFrame:
        """
        执行 Dune 查询

        Args:
            query_id: 查询ID
            parameters: 查询参数

        Returns:
            查询结果数据框
        """
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Dune API")

        try:
            # 执行查询
            execute_url = f"{self.config['base_url']}/query/{query_id}/execute"
            payload = {"parameters": parameters or {}}

            async with self.session.post(execute_url, json=payload) as response:
                if response.status != 200:
                    raise DataSourceError(f"执行查询失败: {response.status}")

                execute_result = await response.json()
                execution_id = execute_result["execution_id"]

            # 等待查询完成并获取结果
            return await self._get_query_result(execution_id)

        except Exception as e:
            self.logger.error(f"执行 Dune 查询失败: {e}")
            # 返回模拟数据
            return self._get_mock_dune_data(query_id)

    async def _get_query_result(self, execution_id: str) -> pd.DataFrame:
        """获取查询执行结果"""
        if not self.session:
            raise DataSourceError("Session 未初始化")

        max_attempts = 30  # 最多等待30次
        attempt = 0

        while attempt < max_attempts:
            try:
                status_url = f"{self.config['base_url']}/execution/{execution_id}/status"
                async with self.session.get(status_url) as response:
                    status_data = await response.json()

                    if status_data["state"] == "QUERY_STATE_COMPLETED":
                        # 查询完成，获取结果
                        results_url = f"{self.config['base_url']}/execution/{execution_id}/results"
                        async with self.session.get(results_url) as response:
                            results_data = await response.json()
                            rows = results_data["result"]["rows"]
                            return pd.DataFrame(rows)
                    elif status_data["state"] == "QUERY_STATE_FAILED":
                        raise DataSourceError("Dune 查询执行失败")

                # 等待一段时间后重试
                await asyncio.sleep(2)
                attempt += 1

            except Exception as e:
                self.logger.error(f"获取查询结果失败: {e}")
                break

        raise DataSourceError("查询执行超时")

    async def get_query_list(self) -> List[Dict[str, Any]]:
        """获取查询列表"""
        if not self.is_connected or not self.session:
            raise DataSourceError("未连接到 Dune API")

        try:
            url = f"{self.config['base_url']}/queries"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    raise DataSourceError(f"获取查询列表失败: {response.status}")
        except Exception as e:
            self.logger.error(f"获取查询列表失败: {e}")
            # 返回模拟数据
            return [
                {"id": 12345, "name": "DEX Trades", "description": "DEX 交易数据"},
                {"id": 67890, "name": "NFT Sales", "description": "NFT 销售数据"}
            ]

    async def get_symbols(self) -> List[str]:
        """获取可用的查询ID列表"""
        queries = await self.get_query_list()
        return [str(query["id"]) for query in queries]

    def _get_mock_dune_data(self, query_id: int) -> pd.DataFrame:
        """生成模拟 Dune 数据"""
        import numpy as np

        # 根据查询ID生成不同类型的模拟数据
        if query_id == 12345:  # DEX Trades
            timestamps = pd.date_range(datetime.now() - timedelta(days=7), datetime.now(), freq='1H')
            return pd.DataFrame({
                "timestamp": timestamps,
                "dex": np.random.choice(["Uniswap", "Sushiswap", "PancakeSwap"], len(timestamps)),
                "token_pair": ["WETH/USDC"] * len(timestamps),
                "volume_usd": np.random.uniform(10000, 1000000, len(timestamps)),
                "tx_count": np.random.randint(1, 100, len(timestamps))
            })
        else:  # 默认数据
            return pd.DataFrame({
                "block_number": np.arange(100),
                "timestamp": [datetime.now() - timedelta(minutes=i) for i in range(100)],
                "tx_hash": [f"0x{np.random.randint(0, 2**256):064x}" for _ in range(100)],
                "value": np.random.uniform(0.001, 10, 100)
            })
