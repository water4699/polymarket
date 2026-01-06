#!/usr/bin/env python3
"""
PredictLab 管道调度演示
展示完整的数据处理流程和错误处理机制
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.scheduler.task_scheduler import DataPipelineScheduler, Task, TaskStatus
from utils.logger import get_logger

logger = get_logger(__name__)


async def demo_successful_pipeline():
    """演示成功的管道执行"""
    print("\n" + "="*60)
    print("🚀 演示1: 成功的数据管道执行")
    print("="*60)

    # 创建调度器
    scheduler = DataPipelineScheduler()

    # 创建模拟管道配置
    pipeline_config = {
        'symbols': ['BTC_PRICE'],  # 只处理一个资产以加快演示
        'source_types': ['predict'],
        'intervals': ['1h'],
        'days_back': 1,  # 只处理1天数据
    }

    # 创建管道
    scheduler.create_data_pipeline(pipeline_config)

    print(f"创建了 {len(scheduler.tasks)} 个任务")
    print("任务列表:")
    for task_id, task in scheduler.tasks.items():
        deps = ", ".join(task.dependencies) if task.dependencies else "无"
        print(f"  • {task.name} (依赖: {deps})")

    # 执行管道
    print("\n开始执行管道...")
    start_time = datetime.now()

    results = await scheduler.execute_pipeline(max_concurrent=2)

    execution_time = (datetime.now() - start_time).total_seconds()

    # 显示结果
    print(".2f")
    print("执行结果:")

    for task_id, result in results.items():
        status_emoji = {
            TaskStatus.SUCCESS: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.RETRYING: "🔄"
        }.get(result.status, "❓")

        print("6.2f")
        if result.error:
            print(f"      错误: {result.error}")


async def demo_error_handling():
    """演示错误处理和重试机制"""
    print("\n" + "="*60)
    print("🛡️ 演示2: 错误处理和重试机制")
    print("="*60)

    scheduler = DataPipelineScheduler()

    # 添加一个必定失败的任务
    async def failing_task():
        raise Exception("这是一个故意制造的错误，用于演示重试机制")

    scheduler.add_task(Task(
        task_id="failing_task",
        name="必定失败的任务",
        func=failing_task,
        max_retries=3,
        retry_delay=0.5,  # 快速重试以加快演示
        critical=False
    ))

    # 添加依赖于失败任务的任务
    async def dependent_task():
        return "依赖任务成功执行"

    scheduler.add_task(Task(
        task_id="dependent_task",
        name="依赖任务",
        func=dependent_task,
        dependencies=["failing_task"]
    ))

    # 执行
    results = await scheduler.execute_pipeline(max_concurrent=1)

    # 分析结果
    failing_result = results.get("failing_task")
    dependent_result = results.get("dependent_task")

    print("失败任务结果:")
    print(f"  状态: {failing_result.status.value}")
    print(f"  重试次数: {failing_result.retry_count}")
    print(f"  执行时间: {failing_result.duration:.2f}秒")
    print(f"  错误信息: {failing_result.error}")

    print("\n依赖任务结果:")
    print(f"  状态: {dependent_result.status.value}")
    print("  (依赖任务被跳过，因为上游任务失败)")

    print("\n💡 错误处理特性:")
    print("  • 自动重试机制 (最多3次)")
    print("  • 依赖检查防止级联错误")
    print("  • 详细的错误日志记录")


async def demo_concurrent_execution():
    """演示并发执行"""
    print("\n" + "="*60)
    print("⚡ 演示3: 并发执行优化")
    print("="*60)

    scheduler = DataPipelineScheduler()

    # 添加多个独立任务来演示并发
    async def quick_task(task_id: str, duration: float):
        await asyncio.sleep(duration)  # 模拟处理时间
        return f"任务 {task_id} 完成，耗时 {duration}秒"

    # 创建10个快速任务
    for i in range(10):
        scheduler.add_task(Task(
            task_id=f"quick_task_{i}",
            name=f"快速任务 {i}",
            func=quick_task,
            args=[f"task_{i}", 0.1 * (i % 3 + 1)]  # 不同的处理时间
        ))

    # 串行执行 (并发数=1)
    print("串行执行 (max_concurrent=1):")
    start_time = datetime.now()
    results_serial = await scheduler.execute_pipeline(max_concurrent=1)
    serial_time = (datetime.now() - start_time).total_seconds()

    # 重新创建任务
    scheduler.tasks.clear()
    scheduler.task_results.clear()
    scheduler.task_status.clear()
    for i in range(10):
        scheduler.add_task(Task(
            task_id=f"quick_task_{i}",
            name=f"快速任务 {i}",
            func=quick_task,
            args=[f"task_{i}", 0.1 * (i % 3 + 1)]
        ))

    # 并发执行 (并发数=3)
    print("并发执行 (max_concurrent=3):")
    start_time = datetime.now()
    results_concurrent = await scheduler.execute_pipeline(max_concurrent=3)
    concurrent_time = (datetime.now() - start_time).total_seconds()

    # 比较结果
    speedup = serial_time / concurrent_time if concurrent_time > 0 else 1

    print(".2f")
    print(".2f")
    print(".1f")

    print("
💡 并发执行优势:"    print("  • 独立任务可并行处理")
    print("  • 显著提升整体 throughput")
    print("  • 自动资源池管理")


async def demo_pipeline_monitoring():
    """演示管道监控"""
    print("\n" + "="*60)
    print("📊 演示4: 管道监控和状态跟踪")
    print("="*60)

    scheduler = DataPipelineScheduler()

    # 创建一个小型管道
    pipeline_config = {
        'symbols': ['BTC_PRICE', 'ETH_PRICE'],
        'source_types': ['predict'],
        'intervals': ['1h'],
        'days_back': 1,
    }

    scheduler.create_data_pipeline(pipeline_config)

    # 模拟执行过程，定期检查状态
    print("启动管道执行...")
    execution_task = asyncio.create_task(scheduler.execute_pipeline(max_concurrent=2))

    # 监控状态
    while not execution_task.done():
        status = scheduler.get_pipeline_status()
        progress = status['progress']
        completed = status['completed_tasks']
        total = status['total_tasks']

        print("5")

        await asyncio.sleep(0.5)  # 每0.5秒检查一次

    # 等待执行完成
    results = await execution_task

    # 最终状态报告
    final_status = scheduler.get_pipeline_status()

    print("
最终执行报告:"    print(f"  总任务数: {final_status['total_tasks']}")
    print(f"  完成任务: {final_status['completed_tasks']}")
    print(".1%")

    print("
任务状态分布:"    for status_name, count in final_status['status_breakdown'].items():
        if count > 0:
            print(f"  {status_name}: {count}")

    print("
📈 监控特性:"    print("  • 实时进度跟踪")
    print("  • 任务状态统计")
    print("  • 性能指标监控")


async def demo_custom_pipeline():
    """演示自定义管道配置"""
    print("\n" + "="*60)
    print("🔧 演示5: 自定义管道配置")
    print("="*60)

    scheduler = DataPipelineScheduler()

    # 自定义任务配置
    custom_config = {
        'symbols': ['BTC_PRICE'],
        'source_types': ['predict', 'polymarket'],  # 多数据源
        'intervals': ['1h', '4h', '1d'],  # 多时间周期
        'days_back': 3,
    }

    # 创建自定义管道
    scheduler.create_data_pipeline(custom_config)

    print(f"自定义管道包含 {len(scheduler.tasks)} 个任务:")

    # 按阶段分组显示
    stages = {}
    for task_id, task in scheduler.tasks.items():
        stage = task_id.split('_')[0]
        if stage not in stages:
            stages[stage] = []
        stages[stage].append(task.name)

    for stage, tasks in stages.items():
        print(f"  {stage.upper()}: {len(tasks)} 个任务")
        for task in tasks[:3]:  # 只显示前3个
            print(f"    • {task}")
        if len(tasks) > 3:
            print(f"    ... 还有 {len(tasks) - 3} 个任务")

    # 显示依赖关系
    print("
依赖关系示例:"    for task_id, task in list(scheduler.tasks.items())[:5]:  # 只显示前5个
        deps = ", ".join(task.dependencies) if task.dependencies else "无依赖"
        print(f"  {task.name} → 依赖: {deps}")

    print("
🎛️ 自定义配置特性:"    print("  • 多数据源并行处理")
    print("  • 多时间周期K线生成")
    print("  • 灵活的任务依赖配置")
    print("  • 可扩展的管道架构")


async def main():
    """主演示函数"""
    print("🎯 PredictLab 任务调度系统演示")
    print("展示数据管道的执行顺序、依赖管理和错误处理")

    try:
        # 演示1: 成功管道
        await demo_successful_pipeline()

        # 演示2: 错误处理
        await demo_error_handling()

        # 演示3: 并发执行
        await demo_concurrent_execution()

        # 演示4: 管道监控
        await demo_pipeline_monitoring()

        # 演示5: 自定义管道
        await demo_custom_pipeline()

        print("\n" + "="*60)
        print("🎉 所有演示完成！")
        print("="*60)
        print("核心特性总结:")
        print("✅ 任务依赖管理和拓扑排序")
        print("✅ 异步并发执行和资源控制")
        print("✅ 自动重试和错误处理机制")
        print("✅ 实时监控和状态跟踪")
        print("✅ 灵活的管道配置系统")
        print("✅ 数据一致性保障")

    except Exception as e:
        logger.error(f"演示执行失败: {e}")
        print(f"💥 演示失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
