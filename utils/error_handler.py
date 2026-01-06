"""
PredictLab 错误处理装饰器和工具
提供统一的错误处理、日志记录和恢复机制
"""
import functools
import time
from typing import Callable, Any, Optional, Dict, Union
from contextlib import contextmanager

from utils.exceptions import PredictLabError, ErrorSeverity
from utils.logger import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """错误处理器"""

    @staticmethod
    @contextmanager
    def handle_errors(operation_name: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                     log_errors: bool = True, raise_errors: bool = True):
        """错误处理上下文管理器"""
        start_time = time.time()

        try:
            logger.info(f"开始执行操作: {operation_name}")
            yield
            execution_time = time.time() - start_time
            logger.info(f"操作 '{operation_name}' 完成，耗时: {execution_time:.2f}秒")
        except PredictLabError as e:
            execution_time = time.time() - start_time
            if log_errors:
                ErrorHandler._log_error(e, operation_name, execution_time)
            if raise_errors:
                raise
        except Exception as e:
            execution_time = time.time() - start_time
            # 将未知异常转换为PredictLabError
            predictlab_error = PredictLabError(
                f"Unexpected error in {operation_name}: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                severity=severity,
                context={"operation": operation_name, "execution_time": execution_time},
                cause=e
            )
            if log_errors:
                ErrorHandler._log_error(predictlab_error, operation_name, execution_time)
            if raise_errors:
                raise predictlab_error from e

    @staticmethod
    def _log_error(error: PredictLabError, operation_name: str, execution_time: float):
        """记录错误信息"""
        error_dict = error.to_dict()
        error_dict.update({
            "operation": operation_name,
            "execution_time": execution_time
        })

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error in {operation_name}", extra=error_dict)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error in {operation_name}", extra=error_dict)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error in {operation_name}", extra=error_dict)
        else:
            logger.info(f"Low severity error in {operation_name}", extra=error_dict)


def handle_errors(operation_name: str = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 log_errors: bool = True, raise_errors: bool = True,
                 retry_count: int = 0, retry_delay: float = 1.0):
    """
    错误处理装饰器

    Args:
        operation_name: 操作名称，如果为None则使用函数名
        severity: 错误严重程度
        log_errors: 是否记录错误
        raise_errors: 是否重新抛出错误
        retry_count: 重试次数
        retry_delay: 重试延迟（秒）
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            last_exception = None

            for attempt in range(retry_count + 1):
                try:
                    with ErrorHandler.handle_errors(
                        op_name, severity, log_errors, raise_errors
                    ):
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retry_count:
                        logger.warning(f"操作 '{op_name}' 第 {attempt + 1} 次尝试失败，{retry_delay} 秒后重试: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # 指数退避
                    else:
                        if raise_errors:
                            raise
                        else:
                            logger.error(f"操作 '{op_name}' 在 {retry_count + 1} 次尝试后仍然失败: {e}")
                            return None

            return None

        return wrapper
    return decorator


def handle_async_errors(operation_name: str = None, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       log_errors: bool = True, raise_errors: bool = True,
                       retry_count: int = 0, retry_delay: float = 1.0):
    """
    异步错误处理装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            last_exception = None

            for attempt in range(retry_count + 1):
                try:
                    async with AsyncErrorHandler.handle_errors(
                        op_name, severity, log_errors, raise_errors
                    ):
                        return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < retry_count:
                        logger.warning(f"异步操作 '{op_name}' 第 {attempt + 1} 次尝试失败，{retry_delay} 秒后重试: {e}")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 1.5  # 指数退避
                    else:
                        if raise_errors:
                            raise
                        else:
                            logger.error(f"异步操作 '{op_name}' 在 {retry_count + 1} 次尝试后仍然失败: {e}")
                            return None

            return None

        return wrapper
    return decorator


class AsyncErrorHandler:
    """异步错误处理器"""

    @staticmethod
    @contextmanager
    async def handle_errors(operation_name: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                           log_errors: bool = True, raise_errors: bool = True):
        """异步错误处理上下文管理器"""
        import asyncio
        start_time = time.time()

        try:
            logger.info(f"开始执行异步操作: {operation_name}")
            yield
            execution_time = time.time() - start_time
            logger.info(f"异步操作 '{operation_name}' 完成，耗时: {execution_time:.2f}秒")
        except PredictLabError as e:
            execution_time = time.time() - start_time
            if log_errors:
                ErrorHandler._log_error(e, operation_name, execution_time)
            if raise_errors:
                raise
        except Exception as e:
            execution_time = time.time() - start_time
            # 将未知异常转换为PredictLabError
            predictlab_error = PredictLabError(
                f"Unexpected async error in {operation_name}: {str(e)}",
                error_code="ASYNC_UNEXPECTED_ERROR",
                severity=severity,
                context={"operation": operation_name, "execution_time": execution_time},
                cause=e
            )
            if log_errors:
                ErrorHandler._log_error(predictlab_error, operation_name, execution_time)
            if raise_errors:
                raise predictlab_error from e


def safe_call(func: Callable, *args, default_return: Any = None,
             log_errors: bool = True, **kwargs) -> Any:
    """
    安全调用函数，如果出错返回默认值

    Args:
        func: 要调用的函数
        *args: 位置参数
        default_return: 默认返回值
        log_errors: 是否记录错误
        **kwargs: 关键字参数

    Returns:
        函数返回值或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"安全调用失败 {func.__name__}: {e}")
        return default_return


async def safe_async_call(func: Callable, *args, default_return: Any = None,
                         log_errors: bool = True, **kwargs) -> Any:
    """
    安全调用异步函数
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"安全异步调用失败 {func.__name__}: {e}")
        return default_return


class CircuitBreaker:
    """熔断器模式实现"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0,
                 expected_exception: Exception = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    logger.info("熔断器进入半开状态，尝试恢复")
                else:
                    raise PredictLabError(
                        f"熔断器开启，拒绝调用 {func.__name__}",
                        error_code="CIRCUIT_BREAKER_OPEN",
                        severity=ErrorSeverity.HIGH
                    )

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self._reset()
                return result
            except self.expected_exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"熔断器开启，失败次数达到阈值: {self.failure_count}")

                raise e

        return wrapper

    def _reset(self):
        """重置熔断器"""
        self.failure_count = 0
        self.state = "CLOSED"
        logger.info("熔断器重置")


class RateLimiter:
    """速率限制器"""

    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls = []
        self.lock = None
        if calls_per_minute > 0:
            try:
                import threading
                self.lock = threading.Lock()
            except ImportError:
                pass

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.calls_per_minute <= 0:
                return func(*args, **kwargs)

            current_time = time.time()
            minute_ago = current_time - 60

            if self.lock:
                with self.lock:
                    # 清理过期调用
                    self.calls = [call for call in self.calls if call > minute_ago]

                    if len(self.calls) >= self.calls_per_minute:
                        sleep_time = 60 - (current_time - self.calls[0])
                        if sleep_time > 0:
                            logger.warning(f"速率限制激活，等待 {sleep_time:.1f} 秒")
                            time.sleep(sleep_time)

                    self.calls.append(current_time)
            else:
                # 无锁版本（单线程）
                self.calls = [call for call in self.calls if call > minute_ago]

                if len(self.calls) >= self.calls_per_minute:
                    sleep_time = 60 - (current_time - self.calls[0])
                    if sleep_time > 0:
                        time.sleep(sleep_time)

                self.calls.append(current_time)

            return func(*args, **kwargs)

        return wrapper
