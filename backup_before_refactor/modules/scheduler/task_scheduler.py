"""
任务调度器模块
提供数据管道的任务编排、依赖管理和异步执行
支持失败重试、错误隔离和日志记录
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from utils.logger import LoggerMixin


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class TaskError(Exception):
    """任务执行异常"""
    pass


@dataclass
class TaskResult:
    """任务执行结果"""
    task_id: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """任务定义"""
    task_id: str
    name: str
    func: Callable[..., Awaitable[Any]]
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    critical: bool = False  # 关键任务失败是否终止整个流程


class DataPipelineScheduler(LoggerMixin):
    """
    数据管道调度器
    管理数据采集 → 清洗 → 存储 → K线生成 → 回测 → 可视化的完整流程
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_status: Dict[str, TaskStatus] = {}
        self.execution_order: List[str] = []
        self.logger.info("初始化数据管道调度器")

    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.task_id] = task
        self.task_status[task.task_id] = TaskStatus.PENDING
        self.logger.info(f"添加任务: {task.name} ({task.task_id})")

    def create_data_pipeline(self, pipeline_config: Dict[str, Any]):
        """
        创建完整的数据管道

        Args:
            pipeline_config: 管道配置
                {
                    'symbols': ['BTC_PRICE', 'ETH_PRICE'],
                    'source_types': ['predict', 'polymarket'],
                    'intervals': ['1h', '1d'],
                    'days_back': 30
                }
        """
        config = pipeline_config
        symbols = config.get('symbols', ['BTC_PRICE'])
        source_types = config.get('source_types', ['predict'])
        intervals = config.get('intervals', ['1h'])
        days_back = config.get('days_back', 30)

        # 1. 数据采集任务
        for source_type in source_types:
            for symbol in symbols:
                task_id = f"collect_{source_type}_{symbol}"
                self.add_task(Task(
                    task_id=task_id,
                    name=f"采集 {source_type} {symbol} 数据",
                    func=self._task_collect_data,
                    args=[source_type, symbol, days_back]
                ))

        # 2. 数据清洗任务 (依赖对应采集任务)
        for source_type in source_types:
            for symbol in symbols:
                collect_task_id = f"collect_{source_type}_{symbol}"
                task_id = f"clean_{source_type}_{symbol}"

                self.add_task(Task(
                    task_id=task_id,
                    name=f"清洗 {source_type} {symbol} 数据",
                    func=self._task_clean_data,
                    args=[source_type, symbol],
                    dependencies=[collect_task_id],
                    critical=True  # 清洗失败会影响后续所有任务
                ))

        # 3. 数据存储任务 (依赖清洗任务)
        for source_type in source_types:
            for symbol in symbols:
                clean_task_id = f"clean_{source_type}_{symbol}"
                task_id = f"store_{source_type}_{symbol}"

                self.add_task(Task(
                    task_id=task_id,
                    name=f"存储 {source_type} {symbol} 数据",
                    func=self._task_store_data,
                    args=[source_type, symbol],
                    dependencies=[clean_task_id],
                    critical=True
                ))

        # 4. K线生成任务 (依赖存储任务)
        for symbol in symbols:
            store_tasks = [f"store_{source_type}_{symbol}" for source_type in source_types]
            for interval in intervals:
                task_id = f"kline_{symbol}_{interval}"

                self.add_task(Task(
                    task_id=task_id,
                    name=f"生成 {symbol} {interval} K线",
                    func=self._task_generate_klines,
                    args=[symbol, interval, days_back],
                    dependencies=store_tasks
                ))

        # 5. 回测任务 (依赖K线生成)
        for symbol in symbols:
            kline_tasks = [f"kline_{symbol}_{interval}" for interval in intervals]
            task_id = f"backtest_{symbol}"

            self.add_task(Task(
                task_id=task_id,
                name=f"回测 {symbol} 策略",
                func=self._task_run_backtest,
                args=[symbol],
                dependencies=kline_tasks
            ))

        # 6. 可视化任务 (依赖回测)
        for symbol in symbols:
            backtest_task = f"backtest_{symbol}"
            task_id = f"visualize_{symbol}"

            self.add_task(Task(
                task_id=task_id,
                name=f"生成 {symbol} 可视化图表",
                func=self._task_generate_charts,
                args=[symbol],
                dependencies=[backtest_task]
            ))

        self.logger.info(f"创建数据管道完成，共 {len(self.tasks)} 个任务")

    async def execute_pipeline(self, max_concurrent: int = 3) -> Dict[str, TaskResult]:
        """
        执行完整的数据管道

        Args:
            max_concurrent: 最大并发任务数

        Returns:
            所有任务的执行结果
        """
        self.logger.info(f"开始执行数据管道，最大并发数: {max_concurrent}")

        # 拓扑排序确定执行顺序
        self.execution_order = self._topological_sort()

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        # 执行所有任务
        tasks = []
        for task_id in self.execution_order:
            task = asyncio.create_task(self._execute_task_with_semaphore(task_id, semaphore))
            tasks.append(task)

        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        successful = sum(1 for r in self.task_results.values() if r.status == TaskStatus.SUCCESS)
        failed = sum(1 for r in self.task_results.values() if r.status == TaskStatus.FAILED)

        self.logger.info(f"数据管道执行完成: {successful} 成功, {failed} 失败")

        return self.task_results

    async def _execute_task_with_semaphore(self, task_id: str, semaphore: asyncio.Semaphore):
        """使用信号量控制并发执行任务"""
        async with semaphore:
            await self._execute_task(task_id)

    async def _execute_task(self, task_id: str) -> TaskResult:
        """执行单个任务"""
        task = self.tasks[task_id]

        # 检查依赖是否满足
        if not self._check_dependencies(task_id):
            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.SKIPPED,
                start_time=datetime.now(),
                error="依赖任务未完成"
            )
            self.task_results[task_id] = result
            self.task_status[task_id] = TaskStatus.SKIPPED
            return result

        # 执行任务（支持重试）
        result = await self._execute_with_retry(task)
        self.task_results[task_id] = result
        self.task_status[task_id] = result.status

        return result

    async def _execute_with_retry(self, task: Task) -> TaskResult:
        """带重试机制执行任务"""
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            start_time=datetime.now()
        )

        for attempt in range(task.max_retries + 1):
            try:
                result.retry_count = attempt

                # 设置超时
                if task.timeout:
                    coro = asyncio.wait_for(task.func(*task.args, **task.kwargs), timeout=task.timeout)
                else:
                    coro = task.func(*task.args, **task.kwargs)

                # 执行任务
                task_result = await coro

                # 成功
                result.status = TaskStatus.SUCCESS
                result.result = task_result
                result.end_time = datetime.now()
                result.duration = (result.end_time - result.start_time).total_seconds()

                self.logger.info(f"任务 {task.name} 执行成功 ({result.duration:.2f}s)")
                break

            except Exception as e:
                error_msg = f"任务 {task.name} 第 {attempt + 1} 次执行失败: {str(e)}"

                if attempt < task.max_retries:
                    # 还有重试机会
                    result.status = TaskStatus.RETRYING
                    self.logger.warning(f"{error_msg}, {task.retry_delay}s 后重试")
                    await asyncio.sleep(task.retry_delay)
                    task.retry_delay *= 2  # 指数退避
                else:
                    # 重试耗尽
                    result.status = TaskStatus.FAILED
                    result.error = error_msg
                    result.end_time = datetime.now()
                    result.duration = (result.end_time - result.start_time).total_seconds()

                    self.logger.error(f"{error_msg}, 重试 {task.max_retries} 次后失败")

                    # 如果是关键任务失败，记录严重错误
                    if task.critical:
                        self.logger.critical(f"关键任务 {task.name} 失败，可能影响后续任务")

        return result

    def _check_dependencies(self, task_id: str) -> bool:
        """检查任务依赖是否满足"""
        task = self.tasks[task_id]

        for dep_id in task.dependencies:
            if dep_id not in self.task_results:
                return False  # 依赖任务还未执行

            dep_result = self.task_results[dep_id]
            if dep_result.status in [TaskStatus.FAILED, TaskStatus.SKIPPED]:
                return False  # 依赖任务失败或跳过

        return True

    def _topological_sort(self) -> List[str]:
        """拓扑排序确定任务执行顺序"""
        # Kahn算法实现
        in_degree = {task_id: len(task.dependencies) for task_id, task in self.tasks.items()}
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # 找到所有依赖于当前任务的任务
            for task_id, task in self.tasks.items():
                if current in task.dependencies:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)

        # 检查是否有环
        if len(result) != len(self.tasks):
            raise TaskError("任务依赖图存在环，无法确定执行顺序")

        return result

    # ===========================================
    # 具体任务实现
    # ===========================================

    async def _task_collect_data(self, source_type: str, symbol: str, days_back: int) -> Dict[str, Any]:
        """数据采集任务（含Raw数据校验）"""
        from modules.data_source.predict_source import PredictDataSource
        from modules.data_source.polymarket_source import PolymarketDataSource
        from modules.validation.data_validator import data_validator, ValidationLevel

        # 根据源类型选择数据源
        if source_type == 'predict':
            ds = PredictDataSource()
        elif source_type == 'polymarket':
            ds = PolymarketDataSource()
        else:
            raise TaskError(f"不支持的数据源类型: {source_type}")

        # 连接并采集数据
        if not await ds.connect():
            raise TaskError(f"无法连接到 {source_type} 数据源")

        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)

            data = await ds.fetch_data(symbol, start_time, end_time)

            if data.empty:
                raise TaskError(f"未采集到 {source_type} {symbol} 数据")

            # Raw 数据校验
            logging.info(f"校验 {source_type} {symbol} Raw 数据")
            validation_report = data_validator.validate_raw_data(
                data, source_type, ValidationLevel.STANDARD
            )

            # 记录校验结果到日志
            if not validation_report.is_pass:
                logging.warning(f"Raw 数据校验未通过，质量评分: {validation_report.score:.1f}")
                # 生成简要校验报告
                issues_summary = {}
                for issue in validation_report.issues:
                    level = issue.result.value
                    if level not in issues_summary:
                        issues_summary[level] = 0
                    issues_summary[level] += 1
                logging.warning(f"校验问题汇总: {issues_summary}")

            return {
                'source_type': source_type,
                'symbol': symbol,
                'data': data,
                'record_count': len(data),
                'validation_score': validation_report.score,
                'validation_passed': validation_report.is_pass,
                'validation_issues': len(validation_report.issues)
            }
        finally:
            await ds.disconnect()

    async def _task_clean_data(self, source_type: str, symbol: str) -> Dict[str, Any]:
        """数据清洗任务"""
        from modules.data_processing.data_cleaner import DataCleaner
        from modules.data_storage.postgres_storage import PostgresStorage

        # 获取上游任务结果
        collect_result = self.task_results[f"collect_{source_type}_{symbol}"]
        if collect_result.status != TaskStatus.SUCCESS:
            raise TaskError(f"上游采集任务失败: {collect_result.error}")

        raw_data = collect_result.result['data']

        # 数据清洗
        cleaner = DataCleaner()
        if source_type in ['predict', 'polymarket']:
            cleaned_data = cleaner.clean_market_data(raw_data)
        else:
            raise TaskError(f"不支持的数据源类型清洗: {source_type}")

        if cleaned_data.empty:
            raise TaskError("清洗后数据为空")

        # 存储清洗后的数据
        storage = PostgresStorage()
        if not await storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 批量插入清洗数据
            for _, row in cleaned_data.iterrows():
                await storage.insert_clean_market_data(
                    source_type, symbol, row['timestamp'],
                    {
                        'price': row.get('price'),
                        'volume': row.get('volume', 0),
                        'data_quality_score': 0.9
                    }
                )

            return {
                'source_type': source_type,
                'symbol': symbol,
                'original_count': len(raw_data),
                'cleaned_count': len(cleaned_data)
            }
        finally:
            await storage.disconnect()

    async def _task_store_data(self, source_type: str, symbol: str) -> Dict[str, Any]:
        """数据存储任务 (额外验证)"""
        # 这个任务主要是验证存储是否成功
        # 实际存储在_clean_data中已完成

        from modules.data_storage.postgres_storage import PostgresStorage

        storage = PostgresStorage()
        if not await storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 验证数据是否正确存储
            df = await storage.query_data(
                'clean_market_data',
                {'source_type': source_type, 'symbol': symbol},
                limit=1
            )

            if df.empty:
                raise TaskError("数据存储验证失败")

            return {
                'source_type': source_type,
                'symbol': symbol,
                'stored': True
            }
        finally:
            await storage.disconnect()

    async def _task_generate_klines(self, symbol: str, interval: str, days_back: int) -> Dict[str, Any]:
        """K线生成任务"""
        from modules.data_processing.kline_generator import KlineGenerator
        from modules.data_storage.postgres_storage import PostgresStorage

        storage = PostgresStorage()
        if not await storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 获取基础数据
            start_time = datetime.now() - timedelta(days=days_back)
            base_data = await storage.query_data(
                'clean_market_data',
                {'symbol': symbol, 'data_timestamp >=': start_time},
                sort_by='data_timestamp',
                ascending=True
            )

            if base_data.empty:
                raise TaskError(f"没有找到 {symbol} 的基础数据")

            # 生成K线
            generator = KlineGenerator()
            kline_data = generator.generate_klines(
                base_data, interval,
                price_col='price',
                volume_col='volume',
                timestamp_col='data_timestamp'
            )

            if kline_data.empty:
                raise TaskError("K线生成结果为空")

            # 存储K线数据
            for _, row in kline_data.iterrows():
                kline_record = {
                    'open_price': row['open'],
                    'high_price': row['high'],
                    'low_price': row['low'],
                    'close_price': row['close'],
                    'volume': row['volume'],
                    'data_points': len(base_data),
                    'data_quality_score': 0.95
                }

                await storage.insert_kline_data(
                    'predict', symbol, interval,
                    row['timestamp'], row['timestamp'] + pd.Timedelta(interval),
                    kline_record
                )

            return {
                'symbol': symbol,
                'interval': interval,
                'kline_count': len(kline_data)
            }
        finally:
            await storage.disconnect()

    async def _task_run_backtest(self, symbol: str) -> Dict[str, Any]:
        """回测任务"""
        from modules.analysis.simple_analyzer import SimpleBacktester, SimpleStrategy
        from modules.data_storage.postgres_storage import PostgresStorage

        storage = PostgresStorage()
        if not await storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 获取K线数据
            kline_data = await storage.get_klines(symbol, '1h',
                                                datetime.now() - timedelta(days=30),
                                                datetime.now())

            if kline_data.empty:
                raise TaskError(f"没有找到 {symbol} 的K线数据")

            # 运行回测
            backtester = SimpleBacktester()
            strategy = SimpleStrategy()
            result = backtester.run_backtest(kline_data, strategy)

            return {
                'symbol': symbol,
                'backtest_result': result
            }
        finally:
            await storage.disconnect()

    async def _task_generate_charts(self, symbol: str) -> Dict[str, Any]:
        """可视化任务"""
        from modules.analysis.simple_analyzer import SimpleChartGenerator
        from modules.data_storage.postgres_storage import PostgresStorage

        storage = PostgresStorage()
        if not await storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 获取K线数据
            kline_data = await storage.get_klines(symbol, '1h',
                                                datetime.now() - timedelta(days=30),
                                                datetime.now())

            if kline_data.empty:
                raise TaskError(f"没有找到 {symbol} 的K线数据")

            # 生成图表
            chart_generator = SimpleChartGenerator()
            price_chart = chart_generator.plot_price_chart(kline_data, f"{symbol} 价格走势")

            return {
                'symbol': symbol,
                'charts': {
                    'price_chart': price_chart
                }
            }
        finally:
            await storage.disconnect()

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取管道执行状态"""
        total = len(self.tasks)
        completed = sum(1 for status in self.task_status.values()
                       if status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.SKIPPED])

        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for s in self.task_status.values() if s == status)

        return {
            'total_tasks': total,
            'completed_tasks': completed,
            'progress': completed / total if total > 0 else 0,
            'status_breakdown': status_counts,
            'task_results': {tid: {
                'status': result.status.value,
                'duration': result.duration,
                'error': result.error
            } for tid, result in self.task_results.items()}
        }

    # ===========================================
    # 数据校验任务 (可选扩展)
    # ===========================================

    async def _task_validate_raw_data(self, source_type: str, symbol: str) -> Dict[str, Any]:
        """数据校验任务 - 校验已存储的Raw数据"""
        from modules.data_storage.postgres_storage import PostgresStorage
        from modules.validation.data_validator import data_validator, ValidationLevel
        import pandas as pd

        logging.info(f"开始校验存储的 {source_type} {symbol} Raw 数据")

        storage = PostgresStorage()
        if not storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 从数据库获取最近的Raw数据进行校验
            # 这里可以根据需要调整查询条件
            raw_df = storage.query_data(
                'raw_market_data',
                {
                    'source_type': source_type,
                    'symbol': symbol,
                    'is_processed': False  # 只校验未处理的原始数据
                },
                limit=1000  # 限制校验数量以提高性能
            )

            if raw_df.empty:
                logging.info("没有需要校验的Raw数据")
                return {'status': 'no_data', 'source_type': source_type, 'symbol': symbol}

            # 执行校验
            validation_report = data_validator.validate_raw_data(
                raw_df, source_type, ValidationLevel.STANDARD
            )

            # 记录校验结果
            if not validation_report.is_pass:
                logging.warning(f"Raw数据校验发现问题，质量评分: {validation_report.score:.1f}")

            # 可以选择将校验结果存储到数据库
            await storage.update_data(
                'raw_market_data',
                {'source_type': source_type, 'symbol': symbol, 'is_processed': False},
                {'validation_score': validation_report.score, 'validation_checked': True}
            )

            return {
                'source_type': source_type,
                'symbol': symbol,
                'checked_records': len(raw_df),
                'validation_score': validation_report.score,
                'issues_found': len(validation_report.issues)
            }

        finally:
            storage.disconnect()

    async def _task_validate_clean_data(self, source_type: str, symbol: str) -> Dict[str, Any]:
        """数据校验任务 - 校验已存储的Clean数据"""
        from modules.data_storage.postgres_storage import PostgresStorage
        from modules.validation.data_validator import data_validator, ValidationLevel

        logging.info(f"开始校验存储的 {source_type} {symbol} Clean 数据")

        storage = PostgresStorage()
        if not storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 获取Clean数据
            clean_df = storage.query_data(
                'clean_market_data',
                {'source_type': source_type, 'symbol': symbol},
                limit=5000
            )

            if clean_df.empty:
                logging.info("没有需要校验的Clean数据")
                return {'status': 'no_data', 'source_type': source_type, 'symbol': symbol}

            # 执行校验
            validation_report = data_validator.validate_clean_data(
                clean_df, source_type, symbol, ValidationLevel.STANDARD
            )

            if not validation_report.is_pass:
                logging.warning(f"Clean数据校验发现问题，质量评分: {validation_report.score:.1f}")

            return {
                'source_type': source_type,
                'symbol': symbol,
                'checked_records': len(clean_df),
                'validation_score': validation_report.score,
                'issues_found': len(validation_report.issues)
            }

        finally:
            storage.disconnect()

    async def _task_validate_features(self, symbol: str, interval_type: str = '1h') -> Dict[str, Any]:
        """数据校验任务 - 校验Feature数据"""
        from modules.data_storage.postgres_storage import PostgresStorage
        from modules.validation.data_validator import data_validator, ValidationLevel

        logging.info(f"开始校验 {symbol} {interval_type} Feature 数据")

        storage = PostgresStorage()
        if not storage.connect():
            raise TaskError("无法连接数据库")

        try:
            # 获取Feature数据
            feature_df = storage.get_technical_indicators(
                symbol, interval_type,
                datetime.now() - timedelta(days=30),
                datetime.now()
            )

            if feature_df.empty:
                logging.info("没有需要校验的Feature数据")
                return {'status': 'no_data', 'symbol': symbol, 'interval_type': interval_type}

            # 执行校验
            validation_report = data_validator.validate_feature_data(
                feature_df, symbol, interval_type, ValidationLevel.STANDARD
            )

            if not validation_report.is_pass:
                logging.warning(f"Feature数据校验发现问题，质量评分: {validation_report.score:.1f}")

            return {
                'symbol': symbol,
                'interval_type': interval_type,
                'checked_records': len(feature_df),
                'validation_score': validation_report.score,
                'issues_found': len(validation_report.issues)
            }

        finally:
            storage.disconnect()
