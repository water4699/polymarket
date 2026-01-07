"""
Polygon 链数据抓取模块
使用 Etherscan API V2 进行数据获取，从数据库读取API Keys，从data目录读取市场数据
"""

import requests
import json
import os
from typing import List, Dict, Optional, Union, Tuple
import logging
from modules.api_key_manager import APIKeyManager
from config import config

logger = logging.getLogger(__name__)


class MarketDataLoader:
    """从data目录加载Polymarket市场数据"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化市场数据加载器

        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.markets_data = {}
        self._load_all_market_data()

    def _load_all_market_data(self):
        """加载所有市场数据文件"""
        if not os.path.exists(self.data_dir):
            logger.warning(f"数据目录不存在: {self.data_dir}")
            return

        # 查找所有polymarket_markets_*.json文件
        for filename in os.listdir(self.data_dir):
            if filename.startswith("polymarket_markets_") and filename.endswith(".json"):
                filepath = os.path.join(self.data_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 提取市场数据
                    markets = data.get('markets', [])
                    for market in markets:
                        condition_id = market.get('conditionId')
                        if condition_id:
                            # 解析tokenIds
                            clob_token_ids = market.get('clobTokenIds', '[]')
                            if isinstance(clob_token_ids, str):
                                try:
                                    token_ids = json.loads(clob_token_ids)
                                except:
                                    token_ids = []
                            else:
                                token_ids = clob_token_ids if isinstance(clob_token_ids, list) else []

                            self.markets_data[condition_id] = {
                                'market_id': market.get('id'),
                                'question': market.get('question'),
                                'token_ids': token_ids,
                                'category': market.get('category', 'Unknown'),
                                'active': market.get('active', True),
                                'volume': market.get('volume'),
                                'full_data': market
                            }

                    logger.info(f"从 {filename} 加载了 {len(markets)} 个市场")

                except Exception as e:
                    logger.error(f"加载文件失败 {filename}: {e}")

        logger.info(f"总共加载了 {len(self.markets_data)} 个市场数据")

    def get_market_by_condition_id(self, condition_id: str) -> Optional[Dict]:
        """
        根据conditionId获取市场信息

        Args:
            condition_id: 条件ID

        Returns:
            市场信息字典或None
        """
        return self.markets_data.get(condition_id)

    def get_token_ids_by_condition_id(self, condition_id: str) -> List[str]:
        """
        根据conditionId获取所有tokenIds

        Args:
            condition_id: 条件ID

        Returns:
            tokenId列表
        """
        market = self.get_market_by_condition_id(condition_id)
        return market.get('token_ids', []) if market else []

    def get_all_condition_ids(self) -> List[str]:
        """
        获取所有conditionIds

        Returns:
            conditionId列表
        """
        return list(self.markets_data.keys())

    def get_all_token_ids(self) -> List[str]:
        """
        获取所有tokenIds

        Returns:
            tokenId列表
        """
        all_token_ids = []
        for market in self.markets_data.values():
            all_token_ids.extend(market.get('token_ids', []))
        return all_token_ids

    def search_markets_by_question(self, keyword: str) -> List[Dict]:
        """
        根据问题关键词搜索市场

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的市场列表
        """
        results = []
        keyword_lower = keyword.lower()

        for condition_id, market in self.markets_data.items():
            question = market.get('question', '').lower()
            if keyword_lower in question:
                results.append({
                    'condition_id': condition_id,
                    **market
                })

        return results


class PolygonClient:
    """Polygon 链客户端"""

    def __init__(self, db_url: Optional[str] = None):
        """
        初始化Polygon客户端

        Args:
            db_url: 数据库连接URL，如果不提供则从配置中获取
        """
        if db_url is None:
            db_url = config.postgres_url

        if not db_url:
            raise ValueError("必须提供数据库连接URL")

        self.api_key_manager = APIKeyManager(db_url)
        self.base_url = config.api.POLYGONSCAN_V2_BASE_URL
        self.chain_id = config.api.POLYGON_CHAIN_ID
        self.contract_address = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"  # Polymarket ERC1155合约
        self.transfer_single_topic = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"

        # 初始化市场数据加载器
        self.market_loader = MarketDataLoader()

    def get_logs(self, condition_id: Optional[str] = None, token_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        获取ERC-1155 TransferSingle事件logs

        Args:
            condition_id: conditionId过滤器（字符串格式，如"0x..."）
            token_id: tokenId过滤器（字符串格式）
            limit: 返回记录数量限制

        Returns:
            交易记录列表
        """
        # 构建API参数
        params = {
            'chainid': self.chain_id,
            'module': 'logs',
            'action': 'getLogs',
            'address': self.contract_address,
            'topic0': self.transfer_single_topic,
            'fromBlock': '0',
            'toBlock': 'latest'
        }

        # 获取API响应
        response_data = self._make_request(params)
        if not response_data or 'result' not in response_data:
            logger.warning("API请求失败或无结果")
            return []

        logs = response_data['result']
        if not logs:
            return []

        # 解析和过滤结果
        results = []
        for log in reversed(logs):  # 从最新的开始
            parsed_log = self._parse_transfer_log(log)
            if not parsed_log:
                continue

            # 应用过滤器
            if condition_id is not None:
                # conditionId是tokenId的高128位
                token_id_val = parsed_log.get('tokenId', 0)
                if isinstance(token_id_val, str):
                    try:
                        token_id_int = int(token_id_val, 16) if token_id_val.startswith('0x') else int(token_id_val)
                    except ValueError:
                        continue
                else:
                    token_id_int = token_id_val

                expected_condition_id = f"0x{token_id_int >> 128:064x}"
                if expected_condition_id != condition_id:
                    continue

            if token_id is not None:
                token_id_val = parsed_log.get('tokenId')
                if token_id_val is None:
                    continue

                # 统一转换为字符串比较
                if isinstance(token_id_val, str):
                    parsed_token_id_str = token_id_val
                else:
                    parsed_token_id_str = str(token_id_val)

                filter_token_id_str = str(token_id)
                if parsed_token_id_str != filter_token_id_str:
                    continue

            results.append(parsed_log)
            if len(results) >= limit:
                break

        return results

    def get_market_logs(self, market_query: str, limit: int = 20) -> Tuple[Dict, List[Dict]]:
        """
        根据市场查询获取市场信息和交易记录

        Args:
            market_query: 市场查询（conditionId或问题关键词）
            limit: 返回记录数量限制

        Returns:
            (市场信息, 交易记录列表)
        """
        # 首先查找市场
        market_info = None
        condition_id = None

        # 检查是否是conditionId
        if market_query.startswith('0x'):
            market_info = self.market_loader.get_market_by_condition_id(market_query)
            condition_id = market_query
        else:
            # 按问题关键词搜索
            markets = self.market_loader.search_markets_by_question(market_query)
            if markets:
                market_info = markets[0]  # 取第一个匹配的结果
                condition_id = market_info['condition_id']

        if not condition_id:
            logger.warning(f"未找到市场: {market_query}")
            return {}, []

        # 获取交易记录
        logs = self.get_logs(condition_id=condition_id, limit=limit)

        return market_info or {}, logs

    def get_market_trades_by_condition_and_token(self, condition_id: str, token_id: Optional[str] = None, limit: int = 20) -> Dict:
        """
        根据 condition_id 和可选的 token_id 获取预测活动的交易信息

        Args:
            condition_id: 预测活动的 conditionId
            token_id: 可选的特定 tokenId，如果提供则只获取该token的交易
            limit: 每个tokenId返回的交易记录数量限制

        Returns:
            包含市场信息和交易数据的字典
            {
                'market_info': {...},  # 市场基本信息
                'token_trades': {      # 按tokenId分组的交易记录
                    'tokenId1': [trade1, trade2, ...],
                    'tokenId2': [trade1, trade2, ...]
                },
                'total_trades': 总交易数,
                'tokens_count': token数量
            }
        """
        result = {
            'market_info': {},
            'token_trades': {},
            'total_trades': 0,
            'tokens_count': 0
        }

        # 1. 获取市场信息
        market_info = self.market_loader.get_market_by_condition_id(condition_id)
        if not market_info:
            logger.warning(f"未找到 conditionId 对应的市场: {condition_id}")
            return result

        result['market_info'] = market_info

        # 2. 获取该市场的所有 tokenIds
        token_ids = market_info.get('token_ids', [])
        if not token_ids:
            logger.warning(f"市场 {condition_id} 没有 tokenIds")
            return result

        result['tokens_count'] = len(token_ids)

        # 3. 如果指定了 token_id，只获取该 token 的交易
        if token_id:
            if token_id not in token_ids:
                logger.warning(f"指定的 tokenId {token_id} 不属于市场 {condition_id}")
                return result
            token_ids = [token_id]

        # 4. 为每个 tokenId 获取交易记录
        for tid in token_ids:
            try:
                # 将 tokenId 转换为字符串格式进行API调用
                token_id_str = str(tid)

                # 获取该 token 的交易记录
                trades = self.get_logs(token_id=token_id_str, limit=limit)

                if trades:
                    result['token_trades'][tid] = trades
                    result['total_trades'] += len(trades)
                    logger.info(f"TokenId {tid}: 获取到 {len(trades)} 条交易记录")

            except Exception as e:
                logger.error(f"获取 tokenId {tid} 交易失败: {e}")
                continue

        logger.info(f"市场 {condition_id} 总共获取到 {result['total_trades']} 条交易记录，涉及 {len(result['token_trades'])} 个token")
        return result

    def get_recent_market_trades(self, condition_id: str, limit_per_token: int = 20) -> List[Dict]:
        """
        获取预测活动的最近交易记录（所有token合并，按时间倒序）

        Args:
            condition_id: 预测活动的 conditionId
            limit_per_token: 每个token获取的交易数量限制

        Returns:
            合并后的交易记录列表，按时间倒序排序
        """
        # 获取详细的交易数据
        detailed_data = self.get_market_trades_by_condition_and_token(
            condition_id=condition_id,
            limit=limit_per_token
        )

        if not detailed_data['token_trades']:
            return []

        # 合并所有token的交易记录
        all_trades = []
        for token_trades in detailed_data['token_trades'].values():
            all_trades.extend(token_trades)

        # 按时间戳倒序排序（最新的在前面）
        all_trades.sort(key=lambda x: x.get('timestamp', 0), reverse=True)

        return all_trades

    def get_popular_markets(self, limit: int = 10) -> List[Dict]:
        """
        获取热门市场列表

        Args:
            limit: 返回数量限制

        Returns:
            热门市场列表
        """
        markets = []
        for condition_id, market in self.market_loader.markets_data.items():
            volume = market.get('volume')
            if volume:
                try:
                    volume_num = float(volume)
                    markets.append({
                        'condition_id': condition_id,
                        'volume': volume_num,
                        **market
                    })
                except:
                    continue

        # 按交易量排序
        markets.sort(key=lambda x: x['volume'], reverse=True)
        return markets[:limit]

    def get_all_available_markets(self) -> List[Dict]:
        """
        获取所有可用市场

        Returns:
            市场列表
        """
        return [
            {'condition_id': cid, **market}
            for cid, market in self.market_loader.markets_data.items()
        ]

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """
        发送API请求，支持重试和API Key轮询

        Args:
            params: 请求参数

        Returns:
            API响应数据
        """
        max_retries = 3
        timeout = 30

        for attempt in range(max_retries):
            try:
                # 获取API Key
                api_key = self.api_key_manager.get_next_key()

                # 构建完整参数
                request_params = params.copy()
                request_params['apikey'] = api_key

                # 发送请求
                response = requests.get(
                    self.base_url,
                    params=request_params,
                    timeout=timeout
                )

                response.raise_for_status()
                data = response.json()

                # 检查响应状态
                if data.get('status') == '1' and 'result' in data:
                    logger.debug(f"API请求成功 (尝试 {attempt + 1})")
                    return data
                else:
                    error_msg = data.get('message', 'Unknown error')
                    logger.warning(f"API返回错误: {error_msg}")

                    # 如果是API Key相关错误，继续尝试下一个Key
                    if 'api key' in error_msg.lower():
                        continue

                    # 其他错误返回结果
                    return data

            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error(f"所有重试都失败: {e}")
                    return None
                continue

            except Exception as e:
                logger.error(f"未知错误: {e}")
                return None

        return None

    def _parse_transfer_log(self, log: Dict) -> Optional[Dict]:
        """
        解析ERC-1155 TransferSingle日志

        Args:
            log: 原始日志数据

        Returns:
            解析后的交易记录
        """
        try:
            # 确保所有字段都是字符串类型
            block_number_str = str(log.get('blockNumber', '')).replace('0x', '')
            tx_hash = str(log.get('transactionHash', ''))
            timestamp_str = str(log.get('timeStamp', '')).replace('0x', '')

            # 基础字段 - 确保是有效的十六进制字符串
            if not block_number_str or not timestamp_str:
                return None

            block_number = int(block_number_str, 16)
            timestamp = int(timestamp_str, 16)

            # topics: [topic0, operator, from, to]
            topics = log.get('topics', [])
            if not isinstance(topics, list) or len(topics) < 4:
                return None

            # 确保topics中的地址是字符串
            from_addr = '0x' + str(topics[2]).replace('0x', '')[-40:]
            to_addr = '0x' + str(topics[3]).replace('0x', '')[-40:]

            # 解析data: id(32bytes) + value(32bytes)
            data = str(log.get('data', '')).replace('0x', '')
            if len(data) < 128:  # 至少需要64*2=128个字符
                return None

            # 确保数据是有效的十六进制
            try:
                token_id = int(data[:64], 16)
                value = int(data[64:128], 16)
            except ValueError:
                return None

            # 计算conditionId (tokenId的高位部分)
            condition_id = token_id >> 128  # 右移128位获取高128位

            return {
                'blockNumber': block_number,
                'txHash': tx_hash,
                'timestamp': timestamp,
                'from': from_addr,
                'to': to_addr,
                'conditionId': condition_id,
                'tokenId': token_id,
                'value': value
            }

        except (ValueError, KeyError, IndexError, TypeError) as e:
            logger.warning(f"解析日志失败: {e}, 日志数据: {log}")
            return None
