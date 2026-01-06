"""
数据校验器模块
提供完整的数据完整性校验、质量检查和异常处理机制
支持 Raw/Clean/Feature 三层数据的全面校验
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from utils.logger import LoggerMixin


class ValidationLevel(Enum):
    """校验级别"""
    BASIC = "basic"      # 基础校验（数据存在性、格式）
    STANDARD = "standard"  # 标准校验（完整性、一致性）
    STRICT = "strict"    # 严格校验（业务规则、质量标准）
    COMPREHENSIVE = "comprehensive"  # 全面校验（所有规则）


class ValidationResult(Enum):
    """校验结果"""
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    ERROR = "error"


@dataclass
class ValidationRule:
    """校验规则定义"""
    rule_id: str
    name: str
    description: str
    level: ValidationLevel
    validator_func: Callable
    error_message: str
    fix_suggestion: Optional[str] = None
    critical: bool = False  # 是否为关键规则，失败时停止处理


@dataclass
class ValidationIssue:
    """校验问题"""
    rule_id: str
    level: str
    result: ValidationResult
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    affected_records: int = 0


@dataclass
class ValidationReport:
    """校验报告"""
    data_type: str  # raw, clean, feature
    symbol: Optional[str]
    time_range: Tuple[datetime, datetime]
    validation_level: ValidationLevel
    total_records: int
    issues: List[ValidationIssue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    @property
    def is_pass(self) -> bool:
        """是否通过校验"""
        critical_issues = [issue for issue in self.issues if issue.result in [ValidationResult.FAIL, ValidationResult.ERROR]]
        return len(critical_issues) == 0

    @property
    def score(self) -> float:
        """质量评分 (0-100)"""
        if self.total_records == 0:
            return 100.0

        error_weight = 1.0
        warning_weight = 0.3

        error_penalty = sum(issue.affected_records for issue in self.issues
                          if issue.result == ValidationResult.ERROR) * error_weight
        warning_penalty = sum(issue.affected_records for issue in self.issues
                             if issue.result == ValidationResult.WARNING) * warning_weight

        total_penalty = error_penalty + warning_penalty
        max_penalty = self.total_records * error_weight

        if max_penalty == 0:
            return 100.0

        return max(0.0, (1.0 - total_penalty / max_penalty) * 100.0)


class DataValidator(LoggerMixin):
    """
    数据校验器
    提供三层数据架构的完整校验功能
    """

    def __init__(self):
        self.raw_rules = self._init_raw_validation_rules()
        self.clean_rules = self._init_clean_validation_rules()
        self.feature_rules = self._init_feature_validation_rules()
        self.logger.info("数据校验器初始化完成")

    def validate_raw_data(self, data: Any, source_type: str,
                         validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
        """
        校验 Raw 数据

        Args:
            data: 原始数据 (dict, list, DataFrame)
            source_type: 数据源类型
            validation_level: 校验级别

        Returns:
            校验报告
        """
        self.logger.info(f"开始校验 Raw 数据: {source_type}, 级别: {validation_level.value}")

        # 转换为标准格式
        df = self._normalize_raw_data(data, source_type)

        # 创建报告
        report = ValidationReport(
            data_type="raw",
            symbol=self._extract_symbol_from_raw(data, source_type),
            time_range=self._extract_time_range_from_raw(data),
            validation_level=validation_level,
            total_records=len(df) if hasattr(df, '__len__') else 1
        )

        # 执行校验规则
        applicable_rules = [rule for rule in self.raw_rules if rule.level.value <= validation_level.value]

        for rule in applicable_rules:
            try:
                issue = rule.validator_func(df, source_type)
                if issue:
                    report.issues.append(issue)
            except Exception as e:
                error_issue = ValidationIssue(
                    rule_id=rule.rule_id,
                    level="error",
                    result=ValidationResult.ERROR,
                    message=f"校验规则执行失败: {str(e)}",
                    details={"exception": str(e)}
                )
                report.issues.append(error_issue)

        # 生成摘要
        report.summary = self._generate_report_summary(report)

        self.logger.info(f"Raw 数据校验完成，质量评分: {report.score:.1f}")
        return report

    def validate_clean_data(self, df: pd.DataFrame, source_type: str, symbol: str,
                           validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
        """
        校验 Clean 数据

        Args:
            df: 清洗后的数据框
            source_type: 数据源类型
            symbol: 资产符号
            validation_level: 校验级别

        Returns:
            校验报告
        """
        self.logger.info(f"开始校验 Clean 数据: {symbol}, 级别: {validation_level.value}")

        # 创建报告
        report = ValidationReport(
            data_type="clean",
            symbol=symbol,
            time_range=self._extract_time_range_from_clean(df),
            validation_level=validation_level,
            total_records=len(df)
        )

        # 执行校验规则
        applicable_rules = [rule for rule in self.clean_rules if rule.level.value <= validation_level.value]

        for rule in applicable_rules:
            try:
                issue = rule.validator_func(df, source_type, symbol)
                if issue:
                    report.issues.append(issue)
            except Exception as e:
                error_issue = ValidationIssue(
                    rule_id=rule.rule_id,
                    level="error",
                    result=ValidationResult.ERROR,
                    message=f"校验规则执行失败: {str(e)}",
                    details={"exception": str(e)}
                )
                report.issues.append(error_issue)

        # 生成摘要
        report.summary = self._generate_report_summary(report)

        self.logger.info(f"Clean 数据校验完成，质量评分: {report.score:.1f}")
        return report

    def validate_feature_data(self, df: pd.DataFrame, symbol: str, interval_type: str,
                             validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationReport:
        """
        校验 Feature 数据

        Args:
            df: 特征数据框
            symbol: 资产符号
            interval_type: 时间间隔
            validation_level: 校验级别

        Returns:
            校验报告
        """
        self.logger.info(f"开始校验 Feature 数据: {symbol} {interval_type}, 级别: {validation_level.value}")

        # 创建报告
        report = ValidationReport(
            data_type="feature",
            symbol=symbol,
            time_range=self._extract_time_range_from_feature(df),
            validation_level=validation_level,
            total_records=len(df)
        )

        # 执行校验规则
        applicable_rules = [rule for rule in self.feature_rules if rule.level.value <= validation_level.value]

        for rule in applicable_rules:
            try:
                issue = rule.validator_func(df, symbol, interval_type)
                if issue:
                    report.issues.append(issue)
            except Exception as e:
                error_issue = ValidationIssue(
                    rule_id=rule.rule_id,
                    level="error",
                    result=ValidationResult.ERROR,
                    message=f"校验规则执行失败: {str(e)}",
                    details={"exception": str(e)}
                )
                report.issues.append(error_issue)

        # 生成摘要
        report.summary = self._generate_report_summary(report)

        self.logger.info(f"Feature 数据校验完成，质量评分: {report.score:.1f}")
        return report

    def validate_incremental_update(self, existing_data: pd.DataFrame, new_data: pd.DataFrame,
                                   symbol: str, data_type: str = "clean") -> ValidationReport:
        """
        校验增量更新数据的一致性

        Args:
            existing_data: 现有数据
            new_data: 新增数据
            symbol: 资产符号
            data_type: 数据类型 (raw/clean/feature)

        Returns:
            增量更新校验报告
        """
        self.logger.info(f"开始校验增量更新: {symbol} {data_type}")

        # 合并数据进行校验
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)

        # 创建报告
        report = ValidationReport(
            data_type=f"incremental_{data_type}",
            symbol=symbol,
            time_range=(new_data.index.min() if not new_data.empty else datetime.now(),
                       new_data.index.max() if not new_data.empty else datetime.now()),
            validation_level=ValidationLevel.STANDARD,
            total_records=len(combined_data)
        )

        # 增量更新特有的校验规则
        incremental_rules = self._init_incremental_validation_rules()

        for rule in incremental_rules:
            try:
                issue = rule.validator_func(existing_data, new_data, combined_data, symbol)
                if issue:
                    report.issues.append(issue)
            except Exception as e:
                error_issue = ValidationIssue(
                    rule_id=rule.rule_id,
                    level="error",
                    result=ValidationResult.ERROR,
                    message=f"增量校验规则执行失败: {str(e)}",
                    details={"exception": str(e)}
                )
                report.issues.append(error_issue)

        # 生成摘要
        report.summary = self._generate_report_summary(report)

        self.logger.info(f"增量更新校验完成，质量评分: {report.score:.1f}")
        return report

    def generate_validation_report(self, report: ValidationReport, format: str = "json") -> str:
        """
        生成校验报告

        Args:
            report: 校验报告
            format: 报告格式 (json/html/markdown)

        Returns:
            格式化的报告字符串
        """
        if format == "json":
            return self._generate_json_report(report)
        elif format == "html":
            return self._generate_html_report(report)
        elif format == "markdown":
            return self._generate_markdown_report(report)
        else:
            raise ValueError(f"不支持的报告格式: {format}")

    # ===========================================
    # 私有方法：数据标准化
    # ===========================================

    def _normalize_raw_data(self, data: Any, source_type: str) -> pd.DataFrame:
        """标准化 Raw 数据格式"""
        try:
            if isinstance(data, dict):
                # 单个记录
                return pd.DataFrame([data])
            elif isinstance(data, list):
                # 多个记录
                return pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                return data
            else:
                # 尝试转换为 DataFrame
                return pd.DataFrame([data])
        except Exception as e:
            self.logger.warning(f"Raw 数据标准化失败: {e}")
            return pd.DataFrame()

    def _extract_symbol_from_raw(self, data: Any, source_type: str) -> Optional[str]:
        """从 Raw 数据中提取资产符号"""
        try:
            if isinstance(data, dict):
                # 常见的符号字段
                symbol_fields = ['symbol', 'asset', 'instrument', 'market_id']
                for field in symbol_fields:
                    if field in data:
                        return str(data[field])
            elif isinstance(data, list) and len(data) > 0:
                return self._extract_symbol_from_raw(data[0], source_type)
        except Exception:
            pass
        return None

    def _extract_time_range_from_raw(self, data: Any) -> Tuple[datetime, datetime]:
        """从 Raw 数据中提取时间范围"""
        try:
            if isinstance(data, dict):
                timestamp_fields = ['timestamp', 'created_at', 'time', 'date']
                for field in timestamp_fields:
                    if field in data:
                        ts = pd.to_datetime(data[field])
                        return (ts, ts)
            elif isinstance(data, list) and len(data) > 0:
                timestamps = []
                for item in data:
                    if isinstance(item, dict):
                        for field in ['timestamp', 'created_at', 'time', 'date']:
                            if field in item:
                                timestamps.append(pd.to_datetime(item[field]))
                                break
                if timestamps:
                    return (min(timestamps), max(timestamps))
        except Exception:
            pass

        now = datetime.now()
        return (now, now)

    def _extract_time_range_from_clean(self, df: pd.DataFrame) -> Tuple[datetime, datetime]:
        """从 Clean 数据中提取时间范围"""
        if df.empty or 'data_timestamp' not in df.columns:
            now = datetime.now()
            return (now, now)

        timestamps = pd.to_datetime(df['data_timestamp'])
        return (timestamps.min(), timestamps.max())

    def _extract_time_range_from_feature(self, df: pd.DataFrame) -> Tuple[datetime, datetime]:
        """从 Feature 数据中提取时间范围"""
        if df.empty or 'data_timestamp' not in df.columns:
            now = datetime.now()
            return (now, now)

        timestamps = pd.to_datetime(df['data_timestamp'])
        return (timestamps.min(), timestamps.max())

    # ===========================================
    # 私有方法：校验规则初始化
    # ===========================================

    def _init_raw_validation_rules(self) -> List[ValidationRule]:
        """初始化 Raw 数据校验规则"""
        return [
            ValidationRule(
                rule_id="raw_data_existence",
                name="数据存在性检查",
                description="检查数据是否为空或不存在",
                level=ValidationLevel.BASIC,
                validator_func=self._validate_raw_data_existence,
                error_message="数据为空或不存在",
                fix_suggestion="检查数据源连接和API响应",
                critical=True
            ),
            ValidationRule(
                rule_id="raw_data_format",
                name="数据格式校验",
                description="检查数据格式是否符合预期",
                level=ValidationLevel.BASIC,
                validator_func=self._validate_raw_data_format,
                error_message="数据格式不符合预期",
                fix_suggestion="检查数据解析逻辑和API响应格式"
            ),
            ValidationRule(
                rule_id="raw_required_fields",
                name="必需字段检查",
                description="检查必需的字段是否存在",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_raw_required_fields,
                error_message="缺少必需的字段",
                fix_suggestion="更新数据源配置或字段映射"
            ),
            ValidationRule(
                rule_id="raw_data_hash",
                name="数据哈希一致性",
                description="检查数据哈希是否一致（去重）",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_raw_data_hash,
                error_message="发现重复数据",
                fix_suggestion="实施数据去重机制"
            ),
            ValidationRule(
                rule_id="raw_timestamp_validity",
                name="时间戳有效性",
                description="检查时间戳是否有效和合理",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_raw_timestamp_validity,
                error_message="时间戳无效或不合理",
                fix_suggestion="检查时区设置和时间戳格式"
            )
        ]

    def _init_clean_validation_rules(self) -> List[ValidationRule]:
        """初始化 Clean 数据校验规则"""
        return [
            ValidationRule(
                rule_id="clean_data_completeness",
                name="数据完整性检查",
                description="检查数据是否完整，无缺失值",
                level=ValidationLevel.BASIC,
                validator_func=self._validate_clean_data_completeness,
                error_message="数据存在缺失值",
                fix_suggestion="实施数据插补或过滤机制"
            ),
            ValidationRule(
                rule_id="clean_no_duplicates",
                name="重复数据检查",
                description="检查是否存在重复记录",
                level=ValidationLevel.BASIC,
                validator_func=self._validate_clean_no_duplicates,
                error_message="存在重复数据",
                fix_suggestion="实施去重逻辑"
            ),
            ValidationRule(
                rule_id="clean_timestamp_continuity",
                name="时间序列连续性",
                description="检查时间序列是否连续",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_clean_timestamp_continuity,
                error_message="时间序列存在间隙",
                fix_suggestion="检查数据采集频率和缺失数据处理"
            ),
            ValidationRule(
                rule_id="clean_value_reasonableness",
                name="数值合理性检查",
                description="检查数值是否在合理范围内",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_clean_value_reasonableness,
                error_message="数值超出合理范围",
                fix_suggestion="实施异常值检测和处理"
            ),
            ValidationRule(
                rule_id="clean_data_consistency",
                name="数据一致性检查",
                description="检查数据内部逻辑一致性",
                level=ValidationLevel.STRICT,
                validator_func=self._validate_clean_data_consistency,
                error_message="数据存在逻辑不一致",
                fix_suggestion="检查业务规则和数据转换逻辑"
            )
        ]

    def _init_feature_validation_rules(self) -> List[ValidationRule]:
        """初始化 Feature 数据校验规则"""
        return [
            ValidationRule(
                rule_id="feature_indicator_completeness",
                name="指标完整性检查",
                description="检查技术指标是否完整计算",
                level=ValidationLevel.BASIC,
                validator_func=self._validate_feature_indicator_completeness,
                error_message="技术指标计算不完整",
                fix_suggestion="重新计算缺失的指标"
            ),
            ValidationRule(
                rule_id="feature_value_reasonableness",
                name="指标数值合理性",
                description="检查技术指标数值是否合理",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_feature_value_reasonableness,
                error_message="技术指标数值异常",
                fix_suggestion="检查指标计算公式和输入数据"
            ),
            ValidationRule(
                rule_id="feature_calculation_consistency",
                name="计算一致性检查",
                description="检查指标计算的内部一致性",
                level=ValidationLevel.STRICT,
                validator_func=self._validate_feature_calculation_consistency,
                error_message="指标计算存在不一致",
                fix_suggestion="验证计算逻辑和依赖关系"
            ),
            ValidationRule(
                rule_id="feature_temporal_consistency",
                name="时间一致性检查",
                description="检查指标的时间序列一致性",
                level=ValidationLevel.STRICT,
                validator_func=self._validate_feature_temporal_consistency,
                error_message="时间序列存在异常",
                fix_suggestion="检查时间窗口和计算周期"
            )
        ]

    def _init_incremental_validation_rules(self) -> List[ValidationRule]:
        """初始化增量更新校验规则"""
        return [
            ValidationRule(
                rule_id="incremental_no_conflicts",
                name="增量数据冲突检查",
                description="检查新数据与现有数据是否存在冲突",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_incremental_no_conflicts,
                error_message="增量数据与现有数据冲突",
                fix_suggestion="处理数据冲突或实施覆盖策略"
            ),
            ValidationRule(
                rule_id="incremental_temporal_order",
                name="时间顺序检查",
                description="检查增量数据的时序是否正确",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_incremental_temporal_order,
                error_message="增量数据时序异常",
                fix_suggestion="确保数据按时间顺序处理"
            ),
            ValidationRule(
                rule_id="incremental_data_continuity",
                name="数据连续性检查",
                description="检查增量更新后的数据连续性",
                level=ValidationLevel.STANDARD,
                validator_func=self._validate_incremental_data_continuity,
                error_message="增量更新后数据不连续",
                fix_suggestion="实施数据补全或插值策略"
            )
        ]

    # ===========================================
    # 私有方法：具体校验实现
    # ===========================================

    def _validate_raw_data_existence(self, df: pd.DataFrame, source_type: str) -> Optional[ValidationIssue]:
        """校验 Raw 数据存在性"""
        if df.empty:
            return ValidationIssue(
                rule_id="raw_data_existence",
                level="error",
                result=ValidationResult.FAIL,
                message="Raw 数据为空",
                affected_records=0
            )
        return None

    def _validate_raw_data_format(self, df: pd.DataFrame, source_type: str) -> Optional[ValidationIssue]:
        """校验 Raw 数据格式"""
        # 检查是否为有效的 DataFrame
        if not isinstance(df, pd.DataFrame):
            return ValidationIssue(
                rule_id="raw_data_format",
                level="error",
                result=ValidationResult.FAIL,
                message="数据格式不是有效的 DataFrame",
                affected_records=1
            )
        return None

    def _validate_raw_required_fields(self, df: pd.DataFrame, source_type: str) -> Optional[ValidationIssue]:
        """校验 Raw 数据必需字段"""
        required_fields = {
            'predict': ['price', 'timestamp'],
            'polymarket': ['price', 'timestamp'],
            'onchain': ['value', 'timestamp'],
            'dune': ['timestamp']  # Dune 数据字段较多，基础检查 timestamp
        }

        if source_type not in required_fields:
            return None

        missing_fields = []
        for field in required_fields[source_type]:
            if field not in df.columns:
                missing_fields.append(field)

        if missing_fields:
            return ValidationIssue(
                rule_id="raw_required_fields",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"缺少必需字段: {', '.join(missing_fields)}",
                affected_records=len(df),
                details={"missing_fields": missing_fields}
            )
        return None

    def _validate_raw_data_hash(self, df: pd.DataFrame, source_type: str) -> Optional[ValidationIssue]:
        """校验 Raw 数据哈希一致性"""
        if df.empty:
            return None

        # 计算数据哈希
        hashes = []
        for _, row in df.iterrows():
            row_str = json.dumps(row.to_dict(), sort_keys=True, default=str)
            hash_obj = hashlib.md5(row_str.encode())
            hashes.append(hash_obj.hexdigest())

        # 检查重复哈希
        unique_hashes = set(hashes)
        if len(hashes) != len(unique_hashes):
            duplicate_count = len(hashes) - len(unique_hashes)
            return ValidationIssue(
                rule_id="raw_data_hash",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"发现 {duplicate_count} 个重复数据记录",
                affected_records=duplicate_count,
                details={"duplicate_count": duplicate_count}
            )
        return None

    def _validate_raw_timestamp_validity(self, df: pd.DataFrame, source_type: str) -> Optional[ValidationIssue]:
        """校验 Raw 数据时间戳有效性"""
        if 'timestamp' not in df.columns:
            return None

        try:
            timestamps = pd.to_datetime(df['timestamp'], errors='coerce')
            invalid_count = timestamps.isna().sum()

            if invalid_count > 0:
                return ValidationIssue(
                    rule_id="raw_timestamp_validity",
                    level="warning",
                    result=ValidationResult.WARNING,
                    message=f"发现 {invalid_count} 个无效时间戳",
                    affected_records=invalid_count,
                    details={"invalid_timestamps": invalid_count}
                )

            # 检查时间戳是否过于久远或未来
            now = datetime.now()
            too_old = timestamps < (now - timedelta(days=365*2))  # 2年前
            too_future = timestamps > (now + timedelta(days=1))    # 1天后

            suspicious_count = too_old.sum() + too_future.sum()
            if suspicious_count > 0:
                return ValidationIssue(
                    rule_id="raw_timestamp_validity",
                    level="warning",
                    result=ValidationResult.WARNING,
                    message=f"发现 {suspicious_count} 个可疑时间戳（过旧或未来）",
                    affected_records=suspicious_count,
                    details={"too_old": int(too_old.sum()), "too_future": int(too_future.sum())}
                )

        except Exception as e:
            return ValidationIssue(
                rule_id="raw_timestamp_validity",
                level="error",
                result=ValidationResult.ERROR,
                message=f"时间戳校验失败: {str(e)}",
                affected_records=len(df)
            )

        return None

    def _validate_clean_data_completeness(self, df: pd.DataFrame, source_type: str, symbol: str) -> Optional[ValidationIssue]:
        """校验 Clean 数据完整性"""
        if df.empty:
            return ValidationIssue(
                rule_id="clean_data_completeness",
                level="error",
                result=ValidationResult.FAIL,
                message="Clean 数据为空",
                affected_records=0
            )

        # 检查关键字段的缺失值
        key_fields = ['data_timestamp', 'price']
        missing_data = {}

        for field in key_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                if missing_count > 0:
                    missing_data[field] = missing_count

        if missing_data:
            total_missing = sum(missing_data.values())
            return ValidationIssue(
                rule_id="clean_data_completeness",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"发现缺失值: {missing_data}",
                affected_records=total_missing,
                details={"missing_by_field": missing_data}
            )

        return None

    def _validate_clean_no_duplicates(self, df: pd.DataFrame, source_type: str, symbol: str) -> Optional[ValidationIssue]:
        """校验 Clean 数据无重复"""
        if df.empty:
            return None

        # 检查基于时间戳的重复
        if 'data_timestamp' in df.columns:
            duplicate_count = df.duplicated(subset=['data_timestamp']).sum()
            if duplicate_count > 0:
                return ValidationIssue(
                    rule_id="clean_no_duplicates",
                    level="warning",
                    result=ValidationResult.WARNING,
                    message=f"发现 {duplicate_count} 个基于时间戳的重复记录",
                    affected_records=duplicate_count,
                    details={"duplicate_count": duplicate_count}
                )

        return None

    def _validate_clean_timestamp_continuity(self, df: pd.DataFrame, source_type: str, symbol: str) -> Optional[ValidationIssue]:
        """校验 Clean 数据时间连续性"""
        if df.empty or 'data_timestamp' not in df.columns:
            return None

        try:
            # 排序时间戳
            timestamps = pd.to_datetime(df['data_timestamp']).sort_values()

            if len(timestamps) < 2:
                return None

            # 计算时间间隔
            intervals = timestamps.diff().dropna()

            # 计算期望间隔（基于数据频率推测）
            median_interval = intervals.median()

            # 检查异常间隔（超过5倍中位数）
            abnormal_intervals = intervals > (median_interval * 5)
            gap_count = abnormal_intervals.sum()

            if gap_count > 0:
                return ValidationIssue(
                    rule_id="clean_timestamp_continuity",
                    level="warning",
                    result=ValidationResult.WARNING,
                    message=f"发现 {gap_count} 个时间间隙",
                    affected_records=gap_count,
                    details={"gap_count": gap_count, "median_interval": str(median_interval)}
                )

        except Exception as e:
            return ValidationIssue(
                rule_id="clean_timestamp_continuity",
                level="error",
                result=ValidationResult.ERROR,
                message=f"时间连续性校验失败: {str(e)}",
                affected_records=len(df)
            )

        return None

    def _validate_clean_value_reasonableness(self, df: pd.DataFrame, source_type: str, symbol: str) -> Optional[ValidationIssue]:
        """校验 Clean 数据数值合理性"""
        if df.empty or 'price' not in df.columns:
            return None

        prices = df['price'].dropna()

        if len(prices) == 0:
            return None

        # 检查负值
        negative_count = (prices < 0).sum()
        if negative_count > 0:
            return ValidationIssue(
                rule_id="clean_value_reasonableness",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"发现 {negative_count} 个负价格值",
                affected_records=negative_count,
                details={"negative_prices": negative_count}
            )

        # 检查异常值（基于IQR方法）
        Q1 = prices.quantile(0.25)
        Q3 = prices.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 3 * IQR
        upper_bound = Q3 + 3 * IQR

        outlier_count = ((prices < lower_bound) | (prices > upper_bound)).sum()
        if outlier_count > 0:
            return ValidationIssue(
                rule_id="clean_value_reasonableness",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"发现 {outlier_count} 个价格异常值",
                affected_records=outlier_count,
                details={"outlier_count": outlier_count, "iqr_bounds": [lower_bound, upper_bound]}
            )

        return None

    def _validate_clean_data_consistency(self, df: pd.DataFrame, source_type: str, symbol: str) -> Optional[ValidationIssue]:
        """校验 Clean 数据一致性"""
        if df.empty:
            return None

        issues = []

        # 检查 OHLC 逻辑一致性
        if all(col in df.columns for col in ['open_price', 'high_price', 'low_price', 'close_price']):
            ohlc_consistent = (
                (df['high_price'] >= df['open_price']) &
                (df['high_price'] >= df['close_price']) &
                (df['low_price'] <= df['open_price']) &
                (df['low_price'] <= df['close_price'])
            )

            inconsistent_count = (~ohlc_consistent).sum()
            if inconsistent_count > 0:
                issues.append(f"OHLC逻辑不一致: {inconsistent_count} 条记录")

        # 检查成交量合理性
        if 'volume' in df.columns:
            negative_volume = (df['volume'] < 0).sum()
            if negative_volume > 0:
                issues.append(f"负成交量: {negative_volume} 条记录")

        if issues:
            return ValidationIssue(
                rule_id="clean_data_consistency",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"数据一致性问题: {'; '.join(issues)}",
                affected_records=sum(int(s.split(': ')[1].split()[0]) for s in issues),
                details={"consistency_issues": issues}
            )

        return None

    # Feature 数据校验实现（简化版）
    def _validate_feature_indicator_completeness(self, df: pd.DataFrame, symbol: str, interval_type: str) -> Optional[ValidationIssue]:
        """校验特征指标完整性"""
        if df.empty:
            return ValidationIssue(
                rule_id="feature_indicator_completeness",
                level="error",
                result=ValidationResult.FAIL,
                message="Feature 数据为空",
                affected_records=0
            )

        # 检查关键指标字段
        key_indicators = ['sma_20', 'rsi_14']
        missing_data = {}

        for indicator in key_indicators:
            if indicator in df.columns:
                missing_count = df[indicator].isna().sum()
                if missing_count > 0:
                    missing_data[indicator] = missing_count

        if missing_data:
            total_missing = sum(missing_data.values())
            return ValidationIssue(
                rule_id="feature_indicator_completeness",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"指标计算不完整: {missing_data}",
                affected_records=total_missing,
                details={"missing_indicators": missing_data}
            )

        return None

    def _validate_feature_value_reasonableness(self, df: pd.DataFrame, symbol: str, interval_type: str) -> Optional[ValidationIssue]:
        """校验特征指标数值合理性"""
        if df.empty:
            return None

        issues = []

        # 检查 RSI 范围 (0-100)
        if 'rsi_14' in df.columns:
            invalid_rsi = ((df['rsi_14'] < 0) | (df['rsi_14'] > 100)).sum()
            if invalid_rsi > 0:
                issues.append(f"RSI超出范围: {invalid_rsi} 条记录")

        # 检查移动平均线合理性
        if 'sma_5' in df.columns and 'sma_20' in df.columns:
            invalid_ma = (df['sma_5'] < 0).sum() + (df['sma_20'] < 0).sum()
            if invalid_ma > 0:
                issues.append(f"移动平均线为负: {invalid_ma} 条记录")

        if issues:
            return ValidationIssue(
                rule_id="feature_value_reasonableness",
                level="warning",
                result=ValidationResult.WARNING,
                message=f"指标数值异常: {'; '.join(issues)}",
                affected_records=sum(int(s.split(': ')[1].split()[0]) for s in issues),
                details={"value_issues": issues}
            )

        return None

    # 其他校验规则的简化实现
    def _validate_feature_calculation_consistency(self, df: pd.DataFrame, symbol: str, interval_type: str) -> Optional[ValidationIssue]:
        return None

    def _validate_feature_temporal_consistency(self, df: pd.DataFrame, symbol: str, interval_type: str) -> Optional[ValidationIssue]:
        return None

    def _validate_incremental_no_conflicts(self, existing_data: pd.DataFrame, new_data: pd.DataFrame, combined_data: pd.DataFrame, symbol: str) -> Optional[ValidationIssue]:
        return None

    def _validate_incremental_temporal_order(self, existing_data: pd.DataFrame, new_data: pd.DataFrame, combined_data: pd.DataFrame, symbol: str) -> Optional[ValidationIssue]:
        return None

    def _validate_incremental_data_continuity(self, existing_data: pd.DataFrame, new_data: pd.DataFrame, combined_data: pd.DataFrame, symbol: str) -> Optional[ValidationIssue]:
        return None

    # ===========================================
    # 私有方法：报告生成
    # ===========================================

    def _generate_report_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """生成报告摘要"""
        issues_by_level = {}
        for issue in report.issues:
            level = issue.result.value
            if level not in issues_by_level:
                issues_by_level[level] = 0
            issues_by_level[level] += 1

        return {
            "total_issues": len(report.issues),
            "issues_by_level": issues_by_level,
            "quality_score": report.score,
            "is_pass": report.is_pass,
            "validation_duration": (datetime.now() - report.generated_at).total_seconds()
        }

    def _generate_json_report(self, report: ValidationReport) -> str:
        """生成 JSON 格式报告"""
        report_dict = {
            "data_type": report.data_type,
            "symbol": report.symbol,
            "time_range": [report.time_range[0].isoformat(), report.time_range[1].isoformat()],
            "validation_level": report.validation_level.value,
            "total_records": report.total_records,
            "quality_score": report.score,
            "is_pass": report.is_pass,
            "summary": report.summary,
            "issues": [
                {
                    "rule_id": issue.rule_id,
                    "level": issue.level,
                    "result": issue.result.value,
                    "message": issue.message,
                    "affected_records": issue.affected_records,
                    "details": issue.details,
                    "timestamp": issue.timestamp.isoformat()
                }
                for issue in report.issues
            ],
            "generated_at": report.generated_at.isoformat()
        }
        return json.dumps(report_dict, indent=2, ensure_ascii=False)

    def _generate_html_report(self, report: ValidationReport) -> str:
        """生成 HTML 格式报告"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>数据校验报告 - {report.data_type}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .score {{ font-size: 24px; font-weight: bold; color: {'green' if report.is_pass else 'red'}; }}
                .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid {'red' if 'fail' in issue.result.value or 'error' in issue.result.value else 'orange'}; background: #f9f9f9; }}
                .summary {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>数据校验报告</h1>
                <p><strong>数据类型:</strong> {report.data_type}</p>
                <p><strong>资产符号:</strong> {report.symbol or 'N/A'}</p>
                <p><strong>时间范围:</strong> {report.time_range[0]} - {report.time_range[1]}</p>
                <p><strong>校验级别:</strong> {report.validation_level.value}</p>
                <p><strong>总记录数:</strong> {report.total_records}</p>
                <p><strong>质量评分:</strong> <span class="score">{report.score:.1f}</span></p>
                <p><strong>校验结果:</strong> {'✅ 通过' if report.is_pass else '❌ 未通过'}</p>
            </div>

            <div class="summary">
                <h2>校验摘要</h2>
                <p>总问题数: {report.summary.get('total_issues', 0)}</p>
                <p>各等级问题分布: {report.summary.get('issues_by_level', {})}</p>
                <p>校验耗时: {report.summary.get('validation_duration', 0):.2f}秒</p>
            </div>

            <h2>详细问题列表</h2>
        """

        for issue in report.issues:
            color = {
                ValidationResult.PASS: 'green',
                ValidationResult.WARNING: 'orange',
                ValidationResult.FAIL: 'red',
                ValidationResult.ERROR: 'darkred'
            }.get(issue.result, 'gray')

            html += f"""
            <div class="issue" style="border-left-color: {color};">
                <h3>{issue.rule_id}</h3>
                <p><strong>等级:</strong> {issue.level.upper()}</p>
                <p><strong>结果:</strong> {issue.result.value.upper()}</p>
                <p><strong>消息:</strong> {issue.message}</p>
                <p><strong>影响记录数:</strong> {issue.affected_records}</p>
                {f'<p><strong>详情:</strong> {issue.details}</p>' if issue.details else ''}
                <p><strong>时间:</strong> {issue.timestamp}</p>
            </div>
            """

        html += """
        </body>
        </html>
        """
        return html

    def _generate_markdown_report(self, report: ValidationReport) -> str:
        """生成 Markdown 格式报告"""
        md = f"""# 数据校验报告

## 基本信息
- **数据类型**: {report.data_type}
- **资产符号**: {report.symbol or 'N/A'}
- **时间范围**: {report.time_range[0]} - {report.time_range[1]}
- **校验级别**: {report.validation_level.value}
- **总记录数**: {report.total_records}
- **质量评分**: {report.score:.1f}
- **校验结果**: {'✅ 通过' if report.is_pass else '❌ 未通过'}

## 校验摘要
- 总问题数: {report.summary.get('total_issues', 0)}
- 各等级问题分布: {report.summary.get('issues_by_level', {})}
- 校验耗时: {report.summary.get('validation_duration', 0):.2f}秒

## 详细问题列表
"""

        for issue in report.issues:
            md += f"""
### {issue.rule_id}
- **等级**: {issue.level.upper()}
- **结果**: {issue.result.value.upper()}
- **消息**: {issue.message}
- **影响记录数**: {issue.affected_records}
"""

            if issue.details:
                md += f"- **详情**: {issue.details}\n"
            md += f"- **时间**: {issue.timestamp}\n"

        return md


# 全局校验器实例
data_validator = DataValidator()
