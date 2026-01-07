#!/usr/bin/env python3
"""
PredictLab 数据质量监控演示
展示完整的数据质量监控、校验和告警功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.validation.quality_monitor import quality_monitor, QualityReport
from modules.validation.data_validator import data_validator, ValidationLevel
from utils.logger import get_logger

logger = get_logger(__name__)


async def demo_quality_check():
    """演示质量检查功能"""
    print("\n" + "="*60)
    print("📊 演示1: 数据质量检查")
    print("="*60)

    try:
        # 执行全面质量检查
        report = await quality_monitor.run_quality_check(['raw', 'clean', 'feature', 'system'])

        print("✅ 质量检查完成"        print(f"📈 总体评分: {report.overall_score:.1f}/100")
        print(f"📊 趋势: {report.trend}")
        print(f"⚠️  告警数量: {len(report.alerts)}")

        print(f"\n📋 各指标评分:")
        for metric_id, score in report.metrics.items():
            status = "🟢" if score >= 95 else "🟡" if score >= 90 else "🔴"
            print("8.1f")

        if report.alerts:
            print(f"\n🚨 活跃告警:")
            for alert in report.alerts[:5]:  # 显示前5个
                level_icon = {"warning": "⚠️", "error": "❌", "critical": "🚨"}.get(alert.level, "ℹ️")
                print(f"   {level_icon} {alert.metric_id}: {alert.message}")

        return report

    except Exception as e:
        logger.error(f"质量检查演示失败: {e}")
        print(f"❌ 质量检查失败: {e}")
        return None


async def demo_data_validation():
    """演示数据校验功能"""
    print("\n" + "="*60)
    print("🔍 演示2: 数据校验功能")
    print("="*60)

    # 创建模拟数据进行校验
    import pandas as pd
    import numpy as np

    # 模拟Raw数据
    raw_data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
        'price': 50000 + np.random.normal(0, 1000, 100),
        'volume': np.random.uniform(1000, 10000, 100),
        'source': ['predict'] * 100
    })

    # 模拟Clean数据
    clean_data = pd.DataFrame({
        'data_timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
        'price': 50000 + np.random.normal(0, 1000, 100),
        'volume': np.random.uniform(1000, 10000, 100),
        'source_type': ['predict'] * 100,
        'symbol': ['BTC_PRICE'] * 100
    })

    # 模拟Feature数据
    feature_data = pd.DataFrame({
        'data_timestamp': pd.date_range('2024-01-01', periods=100, freq='1H'),
        'sma_20': 50000 + np.random.normal(0, 500, 100),
        'rsi_14': np.random.uniform(30, 70, 100),
        'symbol': ['BTC_PRICE'] * 100
    })

    validations = []

    try:
        # Raw数据校验
        print("🔍 校验 Raw 数据...")
        raw_report = data_validator.validate_raw_data(raw_data, 'predict', ValidationLevel.STANDARD)
        validations.append(('Raw', raw_report))

        # Clean数据校验
        print("🔍 校验 Clean 数据...")
        clean_report = data_validator.validate_clean_data(clean_data, 'predict', 'BTC_PRICE', ValidationLevel.STANDARD)
        validations.append(('Clean', clean_report))

        # Feature数据校验
        print("🔍 校验 Feature 数据...")
        feature_report = data_validator.validate_feature_data(feature_data, 'BTC_PRICE', '1h', ValidationLevel.STANDARD)
        validations.append(('Feature', feature_report))

        # 显示结果
        print(f"\n📊 校验结果汇总:")
        for data_type, report in validations:
            status = "✅" if report.is_pass else "❌"
            print("8.1f")

            if report.issues:
                print(f"   ⚠️  发现 {len(report.issues)} 个问题")
                for issue in report.issues[:3]:  # 显示前3个问题
                    print(f"      • {issue.message}")

        return validations

    except Exception as e:
        logger.error(f"数据校验演示失败: {e}")
        print(f"❌ 数据校验失败: {e}")
        return []


async def demo_incremental_validation():
    """演示增量校验功能"""
    print("\n" + "="*60)
    print("🔄 演示3: 增量更新校验")
    print("="*60)

    import pandas as pd
    import numpy as np

    try:
        # 创建现有数据
        existing_data = pd.DataFrame({
            'data_timestamp': pd.date_range('2024-01-01', periods=50, freq='1H'),
            'price': 50000 + np.random.normal(0, 500, 50),
            'volume': np.random.uniform(1000, 5000, 50)
        })

        # 创建新增数据（部分重叠）
        new_data = pd.DataFrame({
            'data_timestamp': pd.date_range('2024-01-01 12:00:00', periods=30, freq='1H'),
            'price': 51000 + np.random.normal(0, 800, 30),
            'volume': np.random.uniform(2000, 8000, 30)
        })

        print("📊 数据重叠分析:")
        existing_times = set(existing_data['data_timestamp'])
        new_times = set(new_data['data_timestamp'])
        overlap = existing_times & new_times
        only_existing = existing_times - new_times
        only_new = new_times - existing_times

        print(f"   📈 现有数据: {len(existing_times)} 条")
        print(f"   🆕 新增数据: {len(new_times)} 条")
        print(f"   🔄 重叠数据: {len(overlap)} 条")
        print(f"   ➕ 仅新增: {len(only_new)} 条")
        print(f"   📉 仅现有: {len(only_existing)} 条")

        # 执行增量校验
        print("
🔍 执行增量校验..."        validation_report = data_validator.validate_incremental_update(
            existing_data, new_data, 'BTC_PRICE', 'clean'
        )

        print("📋 增量校验结果:"        print(f"   🎯 质量评分: {validation_report.score:.1f}/100")
        print(f"   ✅ 校验通过: {'是' if validation_report.is_pass else '否'}")

        if validation_report.issues:
            print(f"   ⚠️  发现问题: {len(validation_report.issues)} 个")
            for issue in validation_report.issues[:3]:
                print(f"      • {issue.message}")

        return validation_report

    except Exception as e:
        logger.error(f"增量校验演示失败: {e}")
        print(f"❌ 增量校验失败: {e}")
        return None


async def demo_monitoring_dashboard():
    """演示监控仪表板"""
    print("\n" + "="*60)
    print("📈 演示4: 质量监控仪表板")
    print("="*60)

    try:
        # 生成质量仪表板HTML
        dashboard_html = quality_monitor.generate_quality_dashboard(days=7)

        # 保存到文件
        dashboard_file = project_root / "quality_dashboard.html"
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)

        print("✅ 质量仪表板已生成"        print(f"📁 保存位置: {dashboard_file}")

        # 显示关键指标
        active_alerts = quality_monitor.get_active_alerts()
        print(f"\n🚨 当前活跃告警: {len(active_alerts)} 个")

        if active_alerts:
            print("📋 最新告警:")
            for alert in active_alerts[:3]:
                print(f"   • {alert.level.upper()}: {alert.message}")

        # 显示质量历史（模拟数据）
        history_df = await quality_monitor.get_quality_history(days=7)
        if not history_df.empty:
            print(f"\n📊 质量历史趋势 (最近7天):")
            recent_scores = history_df.tail(3)
            for _, row in recent_scores.iterrows():
                date_str = row['date'].strftime('%m-%d')
                score = row['overall_score']
                alerts = row['alerts_count']
                trend = "📈" if score >= 90 else "📉" if score >= 80 else "🔴"
                print("6.1f")

        return dashboard_html

    except Exception as e:
        logger.error(f"监控仪表板演示失败: {e}")
        print(f"❌ 仪表板生成失败: {e}")
        return None


async def demo_validation_reports():
    """演示校验报告生成功能"""
    print("\n" + "="*60)
    print("📄 演示5: 校验报告生成")
    print("="*60)

    try:
        # 创建一个示例报告
        sample_report = QualityReport(
            report_date=datetime.now(),
            data_type="sample",
            symbol="BTC_PRICE",
            overall_score=87.5,
            trend="improving"
        )

        # 添加一些示例告警
        from modules.validation.quality_monitor import QualityAlert
        sample_report.alerts = [
            QualityAlert(
                alert_id="sample_1",
                metric_id="raw_completeness",
                level="warning",
                message="Raw数据完整性略低于标准",
                details={"current_score": 94.2, "threshold": 95.0}
            ),
            QualityAlert(
                alert_id="sample_2",
                metric_id="clean_uniqueness",
                level="error",
                message="发现重复数据记录",
                details={"duplicate_count": 15}
            )
        ]

        # 生成不同格式的报告
        formats = ['json', 'markdown', 'html']

        for fmt in formats:
            report_content = data_validator.generate_validation_report(sample_report, fmt)

            # 保存报告
            report_file = project_root / f"sample_validation_report.{fmt}"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"✅ {fmt.upper()} 报告已生成: {report_file}")

        print(f"\n📋 报告包含:")
        print(f"   • 总体评分: {sample_report.overall_score:.1f}/100")
        print(f"   • 告警数量: {len(sample_report.alerts)} 个")
        print(f"   • 趋势: {sample_report.trend}")

        return True

    except Exception as e:
        logger.error(f"校验报告演示失败: {e}")
        print(f"❌ 报告生成失败: {e}")
        return False


async def main():
    """主演示函数"""
    print("🎯 PredictLab 数据质量监控系统演示")
    print("展示完整的数据校验、监控和报告功能")

    try:
        # 演示1: 质量检查
        await demo_quality_check()

        # 演示2: 数据校验
        await demo_data_validation()

        # 演示3: 增量校验
        await demo_incremental_validation()

        # 演示4: 监控仪表板
        await demo_monitoring_dashboard()

        # 演示5: 校验报告
        await demo_validation_reports()

        print("\n" + "="*80)
        print("🎉 所有演示完成！")
        print("="*80)
        print("核心特性总结:")
        print("✅ 多层数据质量校验 (Raw/Clean/Feature)")
        print("✅ 增量更新一致性保证")
        print("✅ 实时质量监控和告警")
        print("✅ 多样化报告生成 (JSON/HTML/Markdown)")
        print("✅ 自动问题检测和修复建议")
        print("✅ 完整的历史趋势分析")

        print("
📁 生成的文件:"        print(f"   • quality_dashboard.html - 质量监控仪表板")
        print(f"   • sample_validation_report.* - 示例校验报告")

    except Exception as e:
        logger.error(f"演示执行失败: {e}")
        print(f"💥 演示失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
