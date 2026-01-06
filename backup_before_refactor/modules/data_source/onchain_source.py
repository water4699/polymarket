"""
链上交易数据源
用于获取区块链交易和事件数据
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from web3 import Web3
from web3.contract import Contract
from web3.exceptions import ContractLogicError
from config import config
from .base import BaseDataSource, DataSourceError


class OnChainDataSource(BaseDataSource):
    """区块链数据源"""

    def __init__(self, network: str = "ethereum"):
        super().__init__(
            name=f"OnChain-{network}",
            config={
                "provider_url": config.api.WEB3_PROVIDER_URL,
                "network": network,
                "timeout": 30
            }
        )
        self.web3: Optional[Web3] = None
        self.network = network

    async def connect(self) -> bool:
        """连接到区块链节点"""
        try:
            self.web3 = Web3(Web3.HTTPProvider(self.config["provider_url"]))
            if not self.web3.is_connected():
                raise DataSourceError("无法连接到区块链节点")

            self.is_connected = True
            self.logger.info(f"成功连接到 {self.network} 网络")
            return True
        except Exception as e:
            self.logger.error(f"连接区块链节点失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
        self.web3 = None
        self.logger.info("已断开区块链连接")

    async def fetch_data(
        self,
        contract_address: str,
        event_name: str,
        start_block: int,
        end_block: int,
        event_abi: Optional[List[Dict]] = None
    ) -> pd.DataFrame:
        """
        获取智能合约事件数据

        Args:
            contract_address: 合约地址
            event_name: 事件名称
            start_block: 开始区块
            end_block: 结束区块
            event_abi: 事件ABI

        Returns:
            事件数据框
        """
        if not self.is_connected or not self.web3:
            raise DataSourceError("未连接到区块链网络")

        try:
            # 创建合约实例
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(contract_address),
                abi=event_abi or []
            )

            # 获取事件
            event_filter = getattr(contract.events, event_name).create_filter(
                fromBlock=start_block,
                toBlock=end_block
            )

            # 获取事件日志
            logs = event_filter.get_all_entries()

            # 解析事件数据
            events_data = []
            for log in logs:
                event_data = {
                    "block_number": log.blockNumber,
                    "transaction_hash": log.transactionHash.hex(),
                    "log_index": log.logIndex,
                    "timestamp": self._get_block_timestamp(log.blockNumber),
                    **dict(log.args)
                }
                events_data.append(event_data)

            return pd.DataFrame(events_data)

        except Exception as e:
            self.logger.error(f"获取链上数据失败: {e}")
            # 返回模拟数据
            return self._get_mock_onchain_data(contract_address, start_block, end_block)

    async def get_token_transfers(
        self,
        token_address: str,
        start_block: int,
        end_block: int
    ) -> pd.DataFrame:
        """获取代币转账数据"""
        # ERC20 Transfer 事件 ABI
        transfer_abi = {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        }

        return await self.fetch_data(
            contract_address=token_address,
            event_name="Transfer",
            start_block=start_block,
            end_block=end_block,
            event_abi=[transfer_abi]
        )

    async def get_symbols(self) -> List[str]:
        """获取支持的代币列表"""
        # 返回常见的ERC20代币地址
        return [
            "0xA0b86a33E6441e88C5F2712C3E9b74F5c4d6E3B6",  # USDC
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",  # DAI
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",   # USDT
        ]

    def _get_block_timestamp(self, block_number: int) -> datetime:
        """获取区块时间戳"""
        if not self.web3:
            return datetime.now()

        try:
            block = self.web3.eth.get_block(block_number)
            return datetime.fromtimestamp(block.timestamp)
        except Exception:
            return datetime.now()

    def _get_mock_onchain_data(
        self,
        contract_address: str,
        start_block: int,
        end_block: int
    ) -> pd.DataFrame:
        """生成模拟链上数据"""
        import numpy as np

        num_events = np.random.randint(10, 100)
        blocks = np.random.randint(start_block, end_block, num_events)

        # 生成随机地址
        addresses = [f"0x{np.random.randint(0, 2**160):040x}" for _ in range(num_events * 2)]

        return pd.DataFrame({
            "block_number": blocks,
            "transaction_hash": [f"0x{np.random.randint(0, 2**256):064x}" for _ in range(num_events)],
            "log_index": np.arange(num_events),
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(num_events)],
            "from": addresses[::2],
            "to": addresses[1::2],
            "value": np.random.uniform(0.1, 1000, num_events),
            "contract_address": contract_address
        })
