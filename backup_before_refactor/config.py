"""
配置管理模块
包含数据库配置、API密钥、全局参数等
"""
import os
from typing import Dict, Any
from pydantic import BaseSettings, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    # PostgreSQL 配置
    POSTGRES_HOST: str = Field(default="localhost", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(default=5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="predictlab", env="POSTGRES_DB")
    POSTGRES_USER: str = Field(default="predictlab_user", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="", env="POSTGRES_PASSWORD")

    # MongoDB 配置
    MONGODB_HOST: str = Field(default="localhost", env="MONGODB_HOST")
    MONGODB_PORT: int = Field(default=27017, env="MONGODB_PORT")
    MONGODB_DB: str = Field(default="predictlab", env="MONGODB_DB")
    MONGODB_USER: str = Field(default="", env="MONGODB_USER")
    MONGODB_PASSWORD: str = Field(default="", env="MONGODB_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False


class APIConfig(BaseSettings):
    """API 配置"""
    # Predict API
    PREDICT_API_KEY: str = Field(default="", env="PREDICT_API_KEY")
    PREDICT_BASE_URL: str = Field(default="https://api.predict.io", env="PREDICT_BASE_URL")

    # Polymarket API
    POLYMARKET_API_KEY: str = Field(default="", env="POLYMARKET_API_KEY")
    POLYMARKET_BASE_URL: str = Field(default="https://api.polymarket.com", env="POLYMARKET_BASE_URL")

    # Dune Analytics
    DUNE_API_KEY: str = Field(default="", env="DUNE_API_KEY")
    DUNE_BASE_URL: str = Field(default="https://api.dune.com", env="DUNE_BASE_URL")

    # 区块链节点
    WEB3_PROVIDER_URL: str = Field(default="https://mainnet.infura.io/v3/YOUR_PROJECT_ID", env="WEB3_PROVIDER_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


class AppConfig(BaseSettings):
    """应用配置"""
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="logs/predictlab.log", env="LOG_FILE")

    # 数据处理配置
    BATCH_SIZE: int = Field(default=1000, env="BATCH_SIZE")
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")

    # 回测配置
    INITIAL_CAPITAL: float = Field(default=10000.0, env="INITIAL_CAPITAL")
    COMMISSION: float = Field(default=0.001, env="COMMISSION")  # 0.1% 手续费

    # 时间配置
    TIMEZONE: str = Field(default="UTC", env="TIMEZONE")
    DATA_RETENTION_DAYS: int = Field(default=365, env="DATA_RETENTION_DAYS")

    class Config:
        env_file = ".env"
        case_sensitive = False


class Config:
    """全局配置管理器"""
    def __init__(self):
        self.database = DatabaseConfig()
        self.api = APIConfig()
        self.app = AppConfig()

    @property
    def postgres_url(self) -> str:
        """PostgreSQL 连接 URL"""
        return f"postgresql://{self.database.POSTGRES_USER}:{self.database.POSTGRES_PASSWORD}@{self.database.POSTGRES_HOST}:{self.database.POSTGRES_PORT}/{self.database.POSTGRES_DB}"

    @property
    def mongodb_url(self) -> str:
        """MongoDB 连接 URL"""
        if self.database.MONGODB_USER and self.database.MONGODB_PASSWORD:
            return f"mongodb://{self.database.MONGODB_USER}:{self.database.MONGODB_PASSWORD}@{self.database.MONGODB_HOST}:{self.database.MONGODB_PORT}/{self.database.MONGODB_DB}"
        return f"mongodb://{self.database.MONGODB_HOST}:{self.database.MONGODB_PORT}/{self.database.MONGODB_DB}"

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置信息（脱敏）"""
        return {
            "database": {
                "postgres_host": self.database.POSTGRES_HOST,
                "postgres_port": self.database.POSTGRES_PORT,
                "postgres_db": self.database.POSTGRES_DB,
                "mongodb_host": self.database.MONGODB_HOST,
                "mongodb_port": self.database.MONGODB_PORT,
                "mongodb_db": self.database.MONGODB_DB,
            },
            "api": {
                "predict_configured": bool(self.api.PREDICT_API_KEY),
                "polymarket_configured": bool(self.api.POLYMARKET_API_KEY),
                "dune_configured": bool(self.api.DUNE_API_KEY),
                "web3_configured": bool(self.api.WEB3_PROVIDER_URL and "YOUR_PROJECT_ID" not in self.api.WEB3_PROVIDER_URL),
            },
            "app": {
                "log_level": self.app.LOG_LEVEL,
                "batch_size": self.app.BATCH_SIZE,
                "max_workers": self.app.MAX_WORKERS,
                "initial_capital": self.app.INITIAL_CAPITAL,
                "commission": self.app.COMMISSION,
                "timezone": self.app.TIMEZONE,
            }
        }


# 全局配置实例
config = Config()
