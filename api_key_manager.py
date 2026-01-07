"""
通用API Key轮询管理器
从数据库 etherscan_accounts 表中读取API Keys，支持轮询和额度管理
"""

import threading
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import text
import logging

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


class APIKeyManager:
    """通用API Key轮询管理器，从数据库读取"""

    def __init__(self, db_url: str):
        """
        初始化API Key管理器，从数据库加载

        Args:
            db_url: 数据库连接URL
        """
        self.db_url = db_url
        self.engine = create_engine(db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # 轮询状态
        self.current_index = 0
        self.api_keys = []
        self.usage_count = {}
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
            self.usage_count = {}

            for account in accounts:
                api_key = account.api_key
                self.api_keys.append(api_key)
                self.usage_count[api_key] = account.daily_used or 0

            logger.info(f"从数据库加载了 {len(self.api_keys)} 个API Keys")

        except Exception as e:
            logger.error(f"加载API Keys失败: {e}")
            # 如果数据库不存在，创建一个空的列表
            self.api_keys = []
            self.usage_count = {}
        finally:
            session.close()

    def _reset_daily_usage_if_needed(self, session: Session):
        """检查是否需要重置每日使用量"""
        try:
            today = date.today()
            session.execute(text("""
                UPDATE etherscan_accounts
                SET daily_used = 0
                WHERE DATE(last_used) < :today AND daily_used > 0
            """), {'today': today})
            session.commit()
        except Exception as e:
            logger.warning(f"重置每日使用量失败: {e}")
            session.rollback()

    def get_next_key(self) -> Optional[str]:
        """
        获取下一个可用的API Key（轮询方式）

        Returns:
            API Key字符串或None（如果没有可用Key）
        """
        if not self.api_keys:
            logger.warning("没有可用的API Keys")
            return None

        with threading.Lock():
            # 尝试找到可用的API Key
            start_index = self.current_index
            checked_count = 0

            while checked_count < len(self.api_keys):
                api_key = self.api_keys[self.current_index]

                # 检查是否可用（未达到每日限额）
                if self._is_key_available(api_key):
                    self.usage_count[api_key] += 1
                    self.current_index = (self.current_index + 1) % len(self.api_keys)

                    # 更新数据库
                    self._update_key_usage(api_key)
                    return api_key

                # 移动到下一个
                self.current_index = (self.current_index + 1) % len(self.api_keys)
                checked_count += 1

            logger.error("所有API Keys都达到每日限额")
            return None

    def _is_key_available(self, api_key: str) -> bool:
        """检查API Key是否可用"""
        daily_used = self.usage_count.get(api_key, 0)
        return daily_used < 100000  # Etherscan每日限额

    def _update_key_usage(self, api_key: str):
        """更新API Key使用统计"""
        session = self.SessionLocal()
        try:
            session.execute(text("""
                UPDATE etherscan_accounts
                SET daily_used = daily_used + 1,
                    last_used = NOW()
                WHERE api_key = :api_key
            """), {'api_key': api_key})
            session.commit()
        except Exception as e:
            logger.error(f"更新API Key使用统计失败: {e}")
            session.rollback()
        finally:
            session.close()

    def get_current_key(self) -> Optional[str]:
        """
        获取当前API Key（不轮询）

        Returns:
            当前API Key字符串
        """
        if not self.api_keys:
            return None
        return self.api_keys[self.current_index]

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取使用统计信息

        Returns:
            包含使用统计的字典
        """
        with threading.Lock():
            total_usage = sum(self.usage_count.values())
            available_keys = sum(1 for key in self.api_keys if self._is_key_available(key))

            return {
                'total_keys': len(self.api_keys),
                'available_keys': available_keys,
                'total_usage': total_usage,
                'key_usage': self.usage_count.copy(),
                'current_index': self.current_index
            }

    def reset_usage(self):
        """重置使用计数"""
        session = self.SessionLocal()
        try:
            session.execute(text("UPDATE etherscan_accounts SET daily_used = 0"))
            session.commit()

            with threading.Lock():
                self.usage_count = {key: 0 for key in self.api_keys}

            logger.info("API Key使用计数已重置")
        except Exception as e:
            logger.error(f"重置使用计数失败: {e}")
            session.rollback()
        finally:
            session.close()

    def add_api_key(self, api_key: str, proxy_info: Optional[Dict] = None):
        """
        添加新的API Key到数据库

        Args:
            api_key: API Key字符串
            proxy_info: 代理信息（可选）
        """
        session = self.SessionLocal()
        try:
            # 检查是否已存在
            existing = session.query(EtherscanAccount).filter_by(api_key=api_key).first()
            if existing:
                logger.warning(f"API Key已存在: {api_key[:10]}...")
                return

            # 创建新账户
            account = EtherscanAccount(
                api_key=api_key,
                proxy_ip=proxy_info.get('ip') if proxy_info else None,
                proxy_port=proxy_info.get('port') if proxy_info else None,
                proxy_user=proxy_info.get('user') if proxy_info else None,
                proxy_pass=proxy_info.get('pass') if proxy_info else None,
                daily_used=0,
                daily_limit=100000
            )

            session.add(account)
            session.commit()

            # 重新加载
            self._load_api_keys()

            logger.info(f"成功添加API Key: {api_key[:10]}...")

        except Exception as e:
            logger.error(f"添加API Key失败: {e}")
            session.rollback()
        finally:
            session.close()
