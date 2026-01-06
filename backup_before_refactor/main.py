#!/usr/bin/env python3
"""
PredictLab 原型版本主程序入口
简化版数据分析平台，适合快速迭代
"""
import asyncio
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any
from config import config
from utils.logger import get_logger

# 核心模块导入
from modules.data_source.predict_source import PredictDataSource
from modules.data_source.polymarket_source import PolymarketDataSource
from modules.data_source.onchain_source import OnChainDataSource
from modules.data_source.dune_source import DuneDataSource

from modules.data_storage.postgres_storage import PostgresStorage
from modules.data_storage.mongo_storage import MongoStorage

from modules.data_processing.data_cleaner import DataCleaner
from modules.data_processing.kline_generator import KlineGenerator

# 简化分析工具
from modules.analysis.simple_analyzer import (
    SimpleStrategy, SimpleBacktester, SimpleChartGenerator, SimpleScheduler,
    simple_backtester, simple_chart_generator, simple_scheduler
)

# 异步任务调度器
from modules.scheduler.async_pipeline_runner import AsyncPipelineRunner

logger = get_logger(__name__)


class PredictLabPrototype:
    """PredictLab 原型版本"""

    def __init__(self):
        # 核心组件
        self.data_sources = {}
        self.storage = {}
        self.data_cleaner = DataCleaner()
        self.kline_generator = KlineGenerator()

        # 分析工具
        self.strategy = SimpleStrategy()
        self.backtester = simple_backtester
        self.chart_generator = simple_chart_generator
        self.scheduler = simple_scheduler

        logger.info("PredictLab 原型版本初始化完成")

    async def init_core_components(self):
        """初始化核心组件"""
        logger.info("初始化核心组件...")

        # 初始化数据源
        await self._init_data_sources()
        # 初始化存储
        await self._init_storage()

        logger.info("核心组件初始化完成")

    async def _init_data_sources(self):
        """初始化数据源"""
        # Predict 数据源
        predict_ds = PredictDataSource()
        if await predict_ds.connect():
            self.data_sources['predict'] = predict_ds

        # Polymarket 数据源
        polymarket_ds = PolymarketDataSource()
        if await polymarket_ds.connect():
            self.data_sources['polymarket'] = polymarket_ds

        # 链上数据源
        onchain_ds = OnChainDataSource()
        if await onchain_ds.connect():
            self.data_sources['onchain'] = onchain_ds

        # Dune 数据源
        dune_ds = DuneDataSource()
        if await dune_ds.connect():
            self.data_sources['dune'] = dune_ds

        logger.info(f"数据源初始化完成: {len(self.data_sources)} 个可用")

    async def _init_storage(self):
        """初始化存储"""
        # PostgreSQL 存储
        postgres_storage = PostgresStorage()
        if await postgres_storage.connect():
            self.storage['postgres'] = postgres_storage

        # MongoDB 存储
        mongo_storage = MongoStorage()
        if await mongo_storage.connect():
            self.storage['mongo'] = mongo_storage

        logger.info(f"存储初始化完成: {len(self.storage)} 个可用")

    async def run_quick_demo(self):
        """运行快速演示"""
        logger.info("开始运行快速演示...")

        try:
            # 1. 快速数据采集
            data = await self._quick_data_fetch()

            # 2. 数据处理
            processed_data = self._quick_data_process(data)

            # 3. 简单分析
            analysis_result = self._quick_analysis(processed_data)

            # 4. 结果展示
            self._display_results(analysis_result)

            logger.info("快速演示完成")

        except Exception as e:
            logger.error(f"快速演示失败: {e}")

    async def _quick_data_fetch(self) -> Dict[str, Any]:
        """快速数据采集"""
        logger.info("执行快速数据采集...")

        # 优先使用 Predict 数据源
        if 'predict' in self.data_sources:
            try:
                ds = self.data_sources['predict']
                end_time = datetime.now()
                start_time = end_time - timedelta(days=7)

                data = await ds.fetch_data(
                    market_id="BTC_PRICE",
                    start_time=start_time,
                    end_time=end_time
                )

                if not data.empty:
                    logger.info(f"采集到真实数据: {len(data)} 条记录")
                    return {'source': 'predict', 'data': data}
            except Exception as e:
                logger.warning(f"Predict 数据采集失败: {e}")

        # 回退到模拟数据
        logger.info("使用模拟数据")
        return {'source': 'mock', 'data': self._generate_mock_data()}

    def _generate_mock_data(self):
        """生成模拟数据"""
        import numpy as np

        timestamps = pd.date_range(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now(),
            freq='1H'
        )

        np.random.seed(42)
        prices = []
        base_price = 50000.0

        for _ in timestamps:
            change = np.random.normal(0, 0.02)
            base_price *= (1 + change)
            prices.append(base_price)

        return pd.DataFrame({
            'timestamp': timestamps,
            'price': prices,
            'volume': np.random.uniform(100000, 1000000, len(timestamps))
        })

    def _quick_data_process(self, fetch_result: Dict[str, Any]):
        """快速数据处理"""
        logger.info("执行数据处理...")

        data = fetch_result['data']

        # 数据清洗
        cleaned_data = self.data_cleaner.clean_market_data(data)
        logger.info(f"数据清洗: {len(data)} -> {len(cleaned_data)} 行")

        # 生成K线
        kline_data = self.kline_generator.generate_klines(
            cleaned_data,
            interval='1d',
            price_col='price',
            volume_col='volume',
            timestamp_col='timestamp'
        )
        logger.info(f"K线生成: {len(kline_data)} 条记录")

        return {
            'original': data,
            'cleaned': cleaned_data,
            'klines': kline_data,
            'source': fetch_result['source']
        }

    def _quick_analysis(self, processed_data: Dict[str, Any]):
        """快速分析"""
        logger.info("执行简单分析...")

        kline_data = processed_data['klines']

        # 简单回测
        backtest_result = self.backtester.run_backtest(kline_data, self.strategy)

        # 生成图表
        price_chart = self.chart_generator.plot_price_chart(kline_data, "价格走势")
        backtest_report = self.chart_generator.plot_backtest_result(backtest_result)

        return {
            'processed_data': processed_data,
            'backtest': backtest_result,
            'charts': {
                'price_chart': price_chart,
                'backtest_report': backtest_report
            }
        }

    def _display_results(self, analysis_result: Dict[str, Any]):
        """显示结果"""
        print("\n" + "="*60)
        print("PredictLab 原型演示结果")
        print("="*60)

        # 数据信息
        processed = analysis_result['processed_data']
        print(f"\n📊 数据概览:")
        print(f"   数据源: {processed['source']}")
        print(f"   原始数据: {len(processed['original'])} 行")
        print(f"   清洗后: {len(processed['cleaned'])} 行")
        print(f"   K线数据: {len(processed['klines'])} 条")

        # 回测结果
        backtest = analysis_result['backtest']
        print(f"\n📈 回测结果:")
        print(f"   策略: {backtest.get('strategy_name', 'N/A')}")
        print(".2f")
        print(".2f")
        print(".2%")
        print(f"   交易次数: {backtest.get('total_trades', 0)}")

        # 图表展示
        print(f"\n📋 分析图表:")
        print(analysis_result['charts']['price_chart'])
        print("\n" + "-"*40)
        print(analysis_result['charts']['backtest_report'])

        print("\n" + "="*60)
        print("演示完成！可以开始自定义扩展")
        print("="*60)

    async def run_custom_analysis(self, data_source: str = "mock", days: int = 30):
        """运行自定义分析"""
        logger.info(f"运行自定义分析: {data_source}, {days}天数据")

        # 生成或获取数据
        if data_source == "mock":
            data = self._generate_mock_data()
        else:
            # 这里可以扩展其他数据源
            data = self._generate_mock_data()

        # 处理和分析
        processed = self._quick_data_process({'source': data_source, 'data': data})
        analysis = self._quick_analysis(processed)
        self._display_results(analysis)

    async def health_check(self):
        """健康检查"""
        health = {
            'data_sources': len(self.data_sources),
            'storage': len(self.storage),
            'status': 'ready' if (self.data_sources or self.storage) else 'limited'
        }

        print("=== 健康检查 ===")
        print(f"数据源: {health['data_sources']} 个可用")
        print(f"存储: {health['storage']} 个可用")
        print(f"状态: {health['status']}")

        return health

    def show_available_components(self):
        """显示可用组件"""
        print("\n=== 可用组件 ===")

        print("数据源:")
        for name in self.data_sources.keys():
            print(f"  ✓ {name}")

        print("存储:")
        for name in self.storage.keys():
            print(f"  ✓ {name}")

        print("分析工具:")
        print("  ✓ 简单策略")
        print("  ✓ 简化回测器")
        print("  ✓ 文本图表生成器")
        print("  ✓ 任务调度器")
        print("  ✓ 异步管道调度器")

    async def run_async_pipeline(self, max_concurrent: int = 2):
        """运行异步数据管道"""
        logger.info(f"启动异步数据管道 (并发数: {max_concurrent})")

        try:
            runner = AsyncPipelineRunner()
            result = await runner.run_pipeline(max_concurrent=min(max_concurrent, 5))

            if result['status'] == 'completed':
                print("🎉 异步数据管道执行成功！")
                print(f"总任务数: {result['stats']['total_tasks']}")
                print(".1%")
                print(".1f")
            else:
                print(f"💥 异步数据管道执行失败: {result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"异步管道执行异常: {e}")
            print(f"💥 异步管道执行异常: {e}")

    async def run_partial_pipeline(self, target_stage: str, symbols: list):
        """运行部分异步管道"""
        logger.info(f"启动部分异步管道: {target_stage}, 资产: {symbols}")

        try:
            runner = AsyncPipelineRunner()
            result = await runner.run_partial_pipeline(target_stage, symbols)

            if result['status'] == 'completed':
                print(f"🎉 部分管道 ({target_stage}) 执行成功！")
                stats = result['stats']
                print(f"总任务数: {stats['total_tasks']}")
                print(".1%")
            else:
                print(f"💥 部分管道执行失败: {result.get('error', '未知错误')}")

        except Exception as e:
            logger.error(f"部分管道执行异常: {e}")
            print(f"💥 部分管道执行异常: {e}")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PredictLab 原型版本 - 快速迭代数据分析平台')
    parser.add_argument('--demo', action='store_true', help='运行快速演示')
    parser.add_argument('--pipeline', action='store_true', help='运行异步数据管道')
    parser.add_argument('--pipeline-stage', choices=['collect', 'clean', 'kline', 'backtest', 'visualize'],
                       help='运行到指定管道阶段')
    parser.add_argument('--analyze', choices=['mock', 'predict'], default='mock', help='运行自定义分析')
    parser.add_argument('--days', type=int, default=30, help='分析数据天数')
    parser.add_argument('--symbols', nargs='+', help='指定处理的资产符号')
    parser.add_argument('--concurrent', type=int, default=2, help='管道最大并发数')
    parser.add_argument('--health', action='store_true', help='健康检查')
    parser.add_argument('--components', action='store_true', help='显示可用组件')

    args = parser.parse_args()

    app = PredictLabPrototype()

    try:
        # 初始化核心组件
        await app.init_core_components()

        if args.health:
            await app.health_check()

        elif args.components:
            app.show_available_components()

        elif args.pipeline:
            # 运行异步数据管道
            await app.run_async_pipeline(max_concurrent=args.concurrent)

        elif args.pipeline_stage:
            # 运行部分管道
            symbols = args.symbols or ['BTC_PRICE']
            await app.run_partial_pipeline(args.pipeline_stage, symbols)

        elif args.demo:
            await app.run_quick_demo()

        elif args.analyze:
            await app.run_custom_analysis(args.analyze, args.days)

        else:
            parser.print_help()
            print("\n" + "="*60)
            print("PredictLab 原型使用示例:")
            print("  python main.py --demo                      # 快速演示")
            print("  python main.py --pipeline                  # 异步数据管道")
            print("  python main.py --pipeline-stage collect    # 运行到采集阶段")
            print("  python main.py --symbols BTC_PRICE ETH_PRICE # 指定资产")
            print("  python main.py --concurrent 3              # 设置并发数")
            print("  python main.py --analyze mock              # 模拟数据分析")
            print("  python main.py --health                   # 健康检查")
            print("  python main.py --components               # 查看组件")
            print("="*60)

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import pandas as pd
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
