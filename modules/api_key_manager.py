"""
Etherscan API Key 轮询管理器
支持自动轮询、代理切换、额度管理和数据库更新
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import text
import requests
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()


class EtherscanAccount(Base):
    """Etherscan账户模型"""
    __tablename__ = 'etherscan_accounts'

    id = Column(Integer, primary_key=True)
    api_key = Column(String(100), unique=True, nullable=False)
    proxy_ip = Column(String(50))
    proxy_port = Column(String(10))
    proxy_user = Column(String(50))
    proxy_pass = Column(String(50))
    daily_used = Column(Integer, default=0)
    daily_limit = Column(Integer, default=100000)  # Etherscan每日限额
    last_used = Column(DateTime)


class EtherscanAPIManager:
    """Etherscan API Key 轮询管理器"""

    def __init__(self, db_url: str):
        """
        初始化管理器

        Args:
            db_url: 数据库连接URL
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # API基础配置
        self.base_url = "https://api.etherscan.io/v2/api"
        self.request_timeout = 30

        # 轮询状态
        self.current_index = 0
        self.api_keys = []
        self._load_api_keys()

    def _load_api_keys(self):
        """从数据库加载所有API Keys"""
        session = self.SessionLocal()
        try:
            # 重置今日使用量（如果是新的一天）
            self._reset_daily_usage_if_needed(session)

            # 加载所有账户
            accounts = session.query(EtherscanAccount).all()
            self.api_keys = []

            for account in accounts:
                self.api_keys.append({
                    'id': account.id,
                    'api_key': account.api_key,
                    'proxy': {
                        'ip': account.proxy_ip,
                        'port': account.proxy_port,
                        'user': account.proxy_user,
                        'pass': account.proxy_pass
                    },
                    'daily_used': account.daily_used or 0,
                    'daily_limit': account.daily_limit or 100000,
                    'last_used': account.last_used
                })

            logger.info(f"加载了 {len(self.api_keys)} 个API Keys")

        except Exception as e:
            logger.error(f"加载API Keys失败: {e}")
        finally:
            session.close()

    def _reset_daily_usage_if_needed(self, session: Session):
        """检查是否需要重置每日使用量"""
        try:
            # 获取今天日期
            today = date.today()

            # 查询昨天之前使用过的账户，重置计数
            session.execute(text("""
                UPDATE etherscan_accounts
                SET daily_used = 0
                WHERE DATE(last_used) < :today AND daily_used > 0
            """), {'today': today})

            session.commit()
            logger.info("已重置昨日使用量")

        except Exception as e:
            logger.warning(f"重置每日使用量失败: {e}")
            session.rollback()

    def _get_proxy_config(self, proxy_info: Dict) -> Optional[Dict]:
        """获取代理配置"""
        if not proxy_info or not proxy_info.get('ip'):
            return None

        proxy_url = f"http://{proxy_info['user']}:{proxy_info['pass']}@{proxy_info['ip']}:{proxy_info['port']}"
        return {
            'http': proxy_url,
            'https': proxy_url
        }

    def get_available_api(self) -> Optional[Dict]:
        """
        获取可用的API Key和代理配置

        Returns:
            包含API key和代理信息的字典，格式：
            {
                'api_key': str,
                'proxy': dict or None,
                'account_id': int
            }
        """
        if not self.api_keys:
            logger.warning("没有可用的API Keys")
            self._load_api_keys()  # 重新加载
            if not self.api_keys:
                return None

        # 从当前位置开始轮询
        start_index = self.current_index
        checked_count = 0

        while checked_count < len(self.api_keys):
            account = self.api_keys[self.current_index]

            # 检查是否可用
            if self._is_account_available(account):
                logger.info(f"选择API Key: {account['api_key'][:10]}... (账户ID: {account['id']})")
                return {
                    'api_key': account['api_key'],
                    'proxy': self._get_proxy_config(account['proxy']),
                    'account_id': account['id']
                }

            # 移动到下一个
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            checked_count += 1

        logger.error("所有API Keys都不可用")
        return None

    def _is_account_available(self, account: Dict) -> bool:
        """检查账户是否可用"""
        # 检查每日限额
        if account['daily_used'] >= account['daily_limit']:
            logger.warning(f"API Key {account['api_key'][:10]}... 达到每日限额")
            return False

        # 检查代理配置（可选）
        proxy = account['proxy']
        if proxy and proxy.get('ip'):
            # 可以添加代理可用性检查
            pass

        return True

    def make_api_request(self, params: Dict, max_retries: int = 3) -> Optional[Dict]:
        """
        发送Etherscan API请求，支持自动重试和API Key轮询

        Args:
            params: API请求参数
            max_retries: 最大重试次数

        Returns:
            API响应数据或None
        """
        for attempt in range(max_retries):
            # 获取可用API
            api_config = self.get_available_api()
            if not api_config:
                logger.error("没有可用的API配置")
                return None

            # 准备请求参数
            request_params = params.copy()
            request_params['apikey'] = api_config['api_key']

            try:
                # 发送请求
                response = requests.get(
                    self.base_url,
                    params=request_params,
                    proxies=api_config['proxy'],
                    timeout=self.request_timeout
                )

                response.raise_for_status()
                data = response.json()

                # 检查API响应
                if data.get('status') == '1':
                    # 请求成功，更新数据库
                    self._update_account_usage(api_config['account_id'])
                    logger.info(f"API请求成功 (账户ID: {api_config['account_id']})")
                    return data
                else:
                    # API返回错误
                    error_msg = data.get('message', 'Unknown error')
                    logger.warning(f"API返回错误: {error_msg}")

                    # 如果是API key相关错误，标记为已用完
                    if 'api key' in error_msg.lower():
                        self._mark_account_exhausted(api_config['account_id'])
                        continue  # 尝试下一个API

                    # 其他错误直接返回
                    return data

            except requests.exceptions.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                # 网络错误，尝试下一个API
                continue

            except Exception as e:
                logger.error(f"未知错误: {e}")
                return None

        logger.error(f"所有重试都失败 ({max_retries} 次)")
        return None

    def _update_account_usage(self, account_id: int):
        """更新账户使用统计"""
        session = self.SessionLocal()
        try:
            # 更新使用量和时间
            session.execute(text("""
                UPDATE etherscan_accounts
                SET daily_used = daily_used + 1,
                    last_used = NOW()
                WHERE id = :account_id
            """), {'account_id': account_id})

            # 更新内存中的数据
            for account in self.api_keys:
                if account['id'] == account_id:
                    account['daily_used'] += 1
                    account['last_used'] = datetime.now()
                    break

            session.commit()
            logger.debug(f"更新账户 {account_id} 使用统计")

        except Exception as e:
            logger.error(f"更新账户使用统计失败: {e}")
            session.rollback()
        finally:
            session.close()

    def _mark_account_exhausted(self, account_id: int):
        """标记账户已耗尽"""
        session = self.SessionLocal()
        try:
            # 将使用量设为限额，防止继续使用
            session.execute(text("""
                UPDATE etherscan_accounts
                SET daily_used = daily_limit
                WHERE id = :account_id
            """), {'account_id': account_id})

            # 更新内存中的数据
            for account in self.api_keys:
                if account['id'] == account_id:
                    account['daily_used'] = account['daily_limit']
                    break

            session.commit()
            logger.info(f"标记账户 {account_id} 为已耗尽")

        except Exception as e:
            logger.error(f"标记账户耗尽失败: {e}")
            session.rollback()
        finally:
            session.close()

    def get_account_stats(self) -> List[Dict]:
        """获取所有账户的统计信息"""
        session = self.SessionLocal()
        try:
            accounts = session.query(EtherscanAccount).all()
            stats = []

            for account in accounts:
                stats.append({
                    'id': account.id,
                    'api_key': account.api_key[:10] + '...',
                    'daily_used': account.daily_used or 0,
                    'daily_limit': account.daily_limit or 100000,
                    'usage_rate': (account.daily_used or 0) / (account.daily_limit or 100000) * 100,
                    'last_used': account.last_used,
                    'has_proxy': bool(account.proxy_ip)
                })

            return stats

        except Exception as e:
            logger.error(f"获取账户统计失败: {e}")
            return []
        finally:
            session.close()


# 使用示例
if __name__ == "__main__":
    # 数据库连接URL（请根据实际情况修改）
    DATABASE_URL = "postgresql://predictlab_user:your_password@localhost:5432/polymarket"

    # 创建管理器
    manager = EtherscanAPIManager(DATABASE_URL)

    # 示例1: 获取可用API
    print("=== 获取可用API ===")
    api_config = manager.get_available_api()
    if api_config:
        print(f"可用API: {api_config['api_key'][:15]}...")
        print(f"代理: {api_config['proxy'] is not None}")
    else:
        print("没有可用API")

    # 示例2: 发送API请求
    print("\n=== 发送API请求 ===")
    test_params = {
        'chainid': 1,
        'module': 'account',
        'action': 'balance',
        'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
    }

    response = manager.make_api_request(test_params)
    if response:
        print("请求成功!")
        print(f"状态: {response.get('status')}")
        print(f"消息: {response.get('message')}")
    else:
        print("请求失败")

    # 示例3: 查看统计
    print("\n=== 账户统计 ===")
    stats = manager.get_account_stats()
    for stat in stats[:3]:  # 只显示前3个
        print(f"ID {stat['id']}: {stat['api_key']} | 使用率: {stat['usage_rate']:.1f}% | 代理: {stat['has_proxy']}")
