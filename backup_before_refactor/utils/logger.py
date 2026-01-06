"""
日志工具模块
提供统一的日志记录功能
"""
import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from config import config


def setup_logger(
    log_level: str = None,
    log_file: str = None,
    rotation: str = "1 day",
    retention: str = "30 days"
):
    """
    设置日志记录器

    Args:
        log_level: 日志级别
        log_file: 日志文件路径
        rotation: 日志轮转策略
        retention: 日志保留策略
    """
    # 移除默认的处理器
    logger.remove()

    # 使用配置中的参数
    log_level = log_level or config.app.LOG_LEVEL
    log_file = log_file or config.app.LOG_FILE

    # 确保日志目录存在
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # 添加文件输出
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        encoding="utf-8"
    )

    logger.info("日志系统初始化完成")


def get_logger(name: str = None):
    """
    获取指定名称的日志记录器

    Args:
        name: 记录器名称

    Returns:
        logger: 日志记录器实例
    """
    if name:
        return logger.bind(name=name)
    return logger


class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""

    @property
    def logger(self):
        """获取类相关的日志记录器"""
        return logger.bind(class_name=self.__class__.__name__)


# 初始化日志系统
setup_logger()
