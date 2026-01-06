"""
PredictLab 统一异常处理系统
提供标准化的异常类和错误处理机制
"""
from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictLabError(Exception):
    """PredictLab基础异常类"""

    def __init__(self, message: str, error_code: str = None,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: Optional[Dict[str, Any]] = None,
                 cause: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.severity = severity
        self.context = context or {}
        self.cause = cause

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于日志记录"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "context": self.context,
            "cause": str(self.cause) if self.cause else None,
            "exception_type": self.__class__.__name__
        }


# 数据源相关异常
class DataSourceError(PredictLabError):
    """数据源异常"""
    pass


class DataSourceConnectionError(DataSourceError):
    """数据源连接异常"""
    def __init__(self, source_type: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Failed to connect to data source: {source_type}",
            error_code="DATASOURCE_CONNECTION_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


class DataFetchError(DataSourceError):
    """数据获取异常"""
    def __init__(self, source_type: str, symbol: str = None, context: Optional[Dict[str, Any]] = None, cause=None):
        message = f"Failed to fetch data from {source_type}"
        if symbol:
            message += f" for symbol {symbol}"
        super().__init__(
            message,
            error_code="DATA_FETCH_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


class APIKeyError(DataSourceError):
    """API密钥异常"""
    def __init__(self, source_type: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Invalid or missing API key for {source_type}",
            error_code="API_KEY_INVALID",
            severity=ErrorSeverity.CRITICAL,
            context=context
        )


# 数据处理相关异常
class DataProcessingError(PredictLabError):
    """数据处理异常"""
    pass


class DataValidationError(DataProcessingError):
    """数据验证异常"""
    def __init__(self, validation_type: str, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Data validation failed ({validation_type}): {details}",
            error_code="DATA_VALIDATION_FAILED",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


class DataCleaningError(DataProcessingError):
    """数据清洗异常"""
    def __init__(self, stage: str, details: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Data cleaning failed at stage '{stage}': {details}",
            error_code="DATA_CLEANING_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


class KlineGenerationError(DataProcessingError):
    """K线生成异常"""
    def __init__(self, symbol: str, interval: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Failed to generate K-line data for {symbol} at interval {interval}",
            error_code="KLINE_GENERATION_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


# 数据存储相关异常
class DataStorageError(PredictLabError):
    """数据存储异常"""
    pass


class DatabaseConnectionError(DataStorageError):
    """数据库连接异常"""
    def __init__(self, db_type: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Failed to connect to {db_type} database",
            error_code="DATABASE_CONNECTION_FAILED",
            severity=ErrorSeverity.CRITICAL,
            context=context,
            cause=cause
        )


class DatabaseOperationError(DataStorageError):
    """数据库操作异常"""
    def __init__(self, operation: str, table: str = None, context: Optional[Dict[str, Any]] = None, cause=None):
        message = f"Database operation '{operation}' failed"
        if table:
            message += f" on table '{table}'"
        super().__init__(
            message,
            error_code="DATABASE_OPERATION_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


# 分析和回测相关异常
class AnalysisError(PredictLabError):
    """分析异常"""
    pass


class BacktestError(AnalysisError):
    """回测异常"""
    def __init__(self, strategy_name: str, details: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Backtest failed for strategy '{strategy_name}': {details}",
            error_code="BACKTEST_FAILED",
            severity=ErrorSeverity.MEDIUM,
            context=context,
            cause=cause
        )


class StrategyError(AnalysisError):
    """策略异常"""
    def __init__(self, strategy_name: str, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Strategy '{strategy_name}' error: {details}",
            error_code="STRATEGY_ERROR",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


# 可视化相关异常
class VisualizationError(PredictLabError):
    """可视化异常"""
    def __init__(self, chart_type: str, details: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Visualization failed for {chart_type}: {details}",
            error_code="VISUALIZATION_FAILED",
            severity=ErrorSeverity.LOW,
            context=context,
            cause=cause
        )


# 调度相关异常
class SchedulerError(PredictLabError):
    """调度异常"""
    pass


class TaskError(SchedulerError):
    """任务异常"""
    def __init__(self, task_name: str, details: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Task '{task_name}' failed: {details}",
            error_code="TASK_FAILED",
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )


class PipelineError(SchedulerError):
    """管道异常"""
    def __init__(self, pipeline_name: str, stage: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Pipeline '{pipeline_name}' failed at stage '{stage}'",
            error_code="PIPELINE_FAILED",
            severity=ErrorSeverity.CRITICAL,
            context=context,
            cause=cause
        )


# 配置相关异常
class ConfigurationError(PredictLabError):
    """配置异常"""
    def __init__(self, config_key: str, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Configuration error for '{config_key}': {details}",
            error_code="CONFIGURATION_ERROR",
            severity=ErrorSeverity.CRITICAL,
            context=context
        )


# 验证相关异常
class ValidationError(PredictLabError):
    """验证异常"""
    def __init__(self, validation_type: str, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Validation failed ({validation_type}): {details}",
            error_code="VALIDATION_FAILED",
            severity=ErrorSeverity.MEDIUM,
            context=context
        )


# 迁移相关异常
class MigrationError(PredictLabError):
    """迁移异常"""
    def __init__(self, migration_version: str, details: str, context: Optional[Dict[str, Any]] = None, cause=None):
        super().__init__(
            f"Migration '{migration_version}' failed: {details}",
            error_code="MIGRATION_FAILED",
            severity=ErrorSeverity.CRITICAL,
            context=context,
            cause=cause
        )
