#!/usr/bin/env python3
"""
异步数据管道运行器
使用 PredictLab 任务调度器执行完整的异步数据处理流程
包含错误处理、并发控制和状态监控
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modules.scheduler.task_scheduler import DataPipelineScheduler
from utils.logger import get_logger

logger = get_logger(__name__)


class AsyncPipelineRunner:
    """异步管道运行器"""

    def __init__(self):
        self.scheduler = DataPipelineScheduler()
        self.pipeline_config = {
            'symbols': ['BTC_PRICE', 'ETH_PRICE'],
            'source_types': ['predict'],
            'intervals': ['1h', '1d'],
            'days_back': 7,  # 处理最近7天的数据
        }

    async def run_pipeline(self, max_concurrent: int = 2) -> Dict[str, Any]:
        """
        运行完整的数据管道

        Args:
            max_concurrent: 最大并发任务数

        Returns:
            执行结果统计
        """
        logger.info("开始运行异步数据管道")
        start_time = datetime.now()

        try:
            # 创建管道
            self.scheduler.create_data_pipeline(self.pipeline_config)

            # 执行管道
            results = await self.scheduler.execute_pipeline(max_concurrent)

            # 计算统计信息
            execution_time = (datetime.now() - start_time).total_seconds()
            stats = self._calculate_stats(results, execution_time)

            # 打印结果报告
            self._print_execution_report(results, stats)

            return {
                'status': 'completed',
                'stats': stats,
                'results': results,
                'execution_time': execution_time
            }

        except Exception as e:
            logger.error(f"管道执行失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }

    async def run_partial_pipeline(self, target_stage: str, symbols: list = None) -> Dict[str, Any]:
        """
        运行部分管道 (用于调试或特定阶段执行)

        Args:
            target_stage: 目标阶段 (collect, clean, kline, backtest, visualize)
            symbols: 指定处理的资产

        Returns:
            执行结果
        """
        logger.info(f"开始运行部分管道: {target_stage}")

        config = self.pipeline_config.copy()
        if symbols:
            config['symbols'] = symbols

        # 根据目标阶段调整配置
        if target_stage == 'collect':
            config['intervals'] = []  # 不生成K线
        elif target_stage == 'clean':
            config['intervals'] = []
        elif target_stage == 'kline':
            pass  # 正常执行
        elif target_stage == 'backtest':
            pass
        elif target_stage == 'visualize':
            pass

        try:
            self.scheduler.create_data_pipeline(config)
            results = await self.scheduler.execute_pipeline(max_concurrent=3)

            execution_time = sum(r.duration for r in results.values() if r.end_time)
            stats = self._calculate_stats(results, execution_time)

            return {
                'status': 'completed',
                'target_stage': target_stage,
                'stats': stats,
                'results': results
            }

        except Exception as e:
            logger.error(f"部分管道执行失败: {e}")
            return {
                'status': 'failed',
                'target_stage': target_stage,
                'error': str(e)
            }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取管道状态"""
        return self.scheduler.get_pipeline_status()

    def _calculate_stats(self, results: Dict[str, Any], execution_time: float) -> Dict[str, Any]:
        """计算执行统计"""
        total_tasks = len(results)
        successful_tasks = sum(1 for r in results.values() if r.status.name == 'SUCCESS')
        failed_tasks = sum(1 for r in results.values() if r.status.name == 'FAILED')
        skipped_tasks = sum(1 for r in results.values() if r.status.name == 'SKIPPED')

        success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0

        # 按阶段统计
        stage_stats = {}
        for task_id, result in results.items():
            stage = task_id.split('_')[0]  # collect, clean, kline, backtest, visualize
            if stage not in stage_stats:
                stage_stats[stage] = {'total': 0, 'success': 0, 'failed': 0}

            stage_stats[stage]['total'] += 1
            if result.status.name == 'SUCCESS':
                stage_stats[stage]['success'] += 1
            elif result.status.name == 'FAILED':
                stage_stats[stage]['failed'] += 1

        return {
            'total_tasks': total_tasks,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'skipped_tasks': skipped_tasks,
            'success_rate': success_rate,
            'execution_time': execution_time,
            'tasks_per_second': total_tasks / execution_time if execution_time > 0 else 0,
            'stage_stats': stage_stats
        }

    def _print_execution_report(self, results: Dict[str, Any], stats: Dict[str, Any]):
        """打印执行报告"""
        print("\n" + "="*80)
        print("📊 PredictLab 数据管道执行报告")
        print("="*80)

        print(f"\n⏱️  执行时间: {stats['execution_time']:.2f} 秒")
        print(f"📋 总任务数: {stats['total_tasks']}")
        print(f"✅ 成功任务: {stats['successful_tasks']}")
        print(f"❌ 失败任务: {stats['failed_tasks']}")
        print(f"⏭️  跳过任务: {stats['skipped_tasks']}")
        print(".1%")
        print(".1f")

        print(f"\n📈 阶段统计:")
        for stage, stage_stat in stats['stage_stats'].items():
            success_rate = stage_stat['success'] / stage_stat['total'] if stage_stat['total'] > 0 else 0
            print("5")

        # 失败任务详情
        failed_results = {tid: r for tid, r in results.items() if r.status.name == 'FAILED'}
        if failed_results:
            print(f"\n❌ 失败任务详情 ({len(failed_results)} 个):")
            for task_id, result in failed_results.items():
                print(f"   • {task_id}: {result.error} ({result.duration:.2f}s)")

        # 性能最慢的任务
        if results:
            slowest_tasks = sorted(
                [(tid, r.duration) for tid, r in results.items() if r.end_time],
                key=lambda x: x[1],
                reverse=True
            )[:5]

            print(f"\n🐌 执行最慢的任务:")
            for task_id, duration in slowest_tasks:
                print("5.2f")

        print("\n" + "="*80)


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PredictLab 异步数据管道运行器')
    parser.add_argument('--full', action='store_true', help='运行完整管道')
    parser.add_argument('--stage', choices=['collect', 'clean', 'kline', 'backtest', 'visualize'],
                       help='运行到指定阶段')
    parser.add_argument('--symbols', nargs='+', help='指定处理的资产符号')
    parser.add_argument('--concurrent', type=int, default=2, help='最大并发任务数 (1-5)')
    parser.add_argument('--status', action='store_true', help='查看管道状态')

    args = parser.parse_args()

    runner = AsyncPipelineRunner()

    try:
        if args.status:
            # 查看状态
            status = runner.get_pipeline_status()
            print("=== 管道状态 ===")
            print(f"总任务数: {status['total_tasks']}")
            print(f"已完成: {status['completed_tasks']}")
            print(".1%")
            print(f"状态分布: {status['status_breakdown']}")

        elif args.full:
            # 运行完整管道
            result = await runner.run_pipeline(max_concurrent=min(args.concurrent, 5))

            if result['status'] == 'completed':
                print("🎉 完整管道执行成功！"            else:
                print(f"💥 管道执行失败: {result.get('error', '未知错误')}")

        elif args.stage:
            # 运行部分管道
            symbols = args.symbols or ['BTC_PRICE']
            result = await runner.run_partial_pipeline(args.stage, symbols)

            if result['status'] == 'completed':
                print(f"🎉 部分管道 ({args.stage}) 执行成功！"            else:
                print(f"💥 部分管道执行失败: {result.get('error', '未知错误')}")

        else:
            parser.print_help()
            print("\n" + "="*60)
            print("PredictLab 异步管道使用示例:")
            print("  python async_pipeline_runner.py --full              # 完整管道")
            print("  python async_pipeline_runner.py --stage collect     # 只采集数据")
            print("  python async_pipeline_runner.py --stage kline       # 生成K线")
            print("  python async_pipeline_runner.py --symbols BTC_PRICE # 指定资产")
            print("  python async_pipeline_runner.py --concurrent 3      # 3并发")
            print("  python async_pipeline_runner.py --status           # 查看状态")
            print("="*60)

    except KeyboardInterrupt:
        print("\n👋 收到中断信号，正在退出...")
    except Exception as e:
        logger.error(f"执行出错: {e}")
        print(f"💥 执行失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
