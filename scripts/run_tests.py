#!/usr/bin/env python3
"""
PredictLab 测试运行器
提供便捷的测试执行和报告功能
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "tests"
        self.pytest_args = [
            "python", "-m", "pytest",
            "--tb=short",
            "--strict-markers",
            "--disable-warnings"
        ]

    def run_unit_tests(self, markers: List[str] = None, coverage: bool = True) -> Dict[str, Any]:
        """运行单元测试"""
        logger.info("开始运行单元测试...")

        cmd = self.pytest_args.copy()
        cmd.extend([
            str(self.test_dir / "unit"),
            "-v"
        ])

        if coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-fail-under=80"
            ])

        if markers:
            cmd.extend(["-m", " and ".join(markers)])

        return self._run_command(cmd, "单元测试")

    def run_integration_tests(self, markers: List[str] = None) -> Dict[str, Any]:
        """运行集成测试"""
        logger.info("开始运行集成测试...")

        cmd = self.pytest_args.copy()
        cmd.extend([
            str(self.test_dir / "integration"),
            "-v",
            "--durations=10"
        ])

        if markers:
            cmd.extend(["-m", " and ".join(markers)])

        return self._run_command(cmd, "集成测试")

    def run_all_tests(self, coverage: bool = True, parallel: bool = False) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("开始运行所有测试...")

        cmd = self.pytest_args.copy()
        cmd.extend([
            str(self.test_dir),
            "-v",
            "--durations=10"
        ])

        if coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=xml",
                "--cov-fail-under=80"
            ])

        if parallel:
            # 需要安装 pytest-xdist
            try:
                import pytest_xdist
                cmd.extend(["-n", "auto"])
            except ImportError:
                logger.warning("pytest-xdist 未安装，使用单线程模式")

        return self._run_command(cmd, "所有测试")

    def run_specific_test(self, test_path: str, coverage: bool = False) -> Dict[str, Any]:
        """运行特定测试"""
        logger.info(f"运行特定测试: {test_path}")

        cmd = self.pytest_args.copy()
        cmd.extend([
            test_path,
            "-v",
            "--tb=long"
        ])

        if coverage:
            cmd.extend([
                "--cov=.",
                "--cov-report=term-missing"
            ])

        return self._run_command(cmd, f"测试 {test_path}")

    def run_with_coverage_report(self) -> Dict[str, Any]:
        """生成详细的覆盖率报告"""
        logger.info("生成覆盖率报告...")

        cmd = [
            "python", "-m", "pytest",
            str(self.test_dir),
            "--cov=.",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--cov-report=term-missing:skip-covered",
            "-v"
        ]

        result = self._run_command(cmd, "覆盖率测试")

        if result['returncode'] == 0:
            htmlcov_path = self.project_root / "htmlcov" / "index.html"
            if htmlcov_path.exists():
                logger.info(f"详细覆盖率报告已生成: file://{htmlcov_path}")

        return result

    def run_performance_tests(self) -> Dict[str, Any]:
        """运行性能测试"""
        logger.info("运行性能测试...")

        cmd = self.pytest_args.copy()
        cmd.extend([
            str(self.test_dir),
            "-m", "slow",
            "-v",
            "--durations=0",
            "--tb=short"
        ])

        return self._run_command(cmd, "性能测试")

    def check_test_structure(self) -> Dict[str, Any]:
        """检查测试结构"""
        logger.info("检查测试结构...")

        issues = []

        # 检查测试文件存在
        unit_dir = self.test_dir / "unit"
        integration_dir = self.test_dir / "integration"

        if not unit_dir.exists():
            issues.append("单元测试目录不存在")

        if not integration_dir.exists():
            issues.append("集成测试目录不存在")

        # 检查 conftest.py
        conftest_path = self.test_dir / "conftest.py"
        if not conftest_path.exists():
            issues.append("conftest.py 不存在")

        # 检查测试文件
        test_files = list(self.test_dir.rglob("test_*.py"))
        if len(test_files) == 0:
            issues.append("没有找到测试文件")

        # 检查测试覆盖
        modules_dir = self.project_root / "modules"
        if modules_dir.exists():
            module_files = list(modules_dir.rglob("*.py"))
            test_files_count = len(test_files)

            if test_files_count < len(module_files) * 0.5:  # 至少50%的覆盖
                issues.append(f"测试文件数量不足: {test_files_count} 个测试文件, {len(module_files)} 个模块文件")

        return {
            'success': len(issues) == 0,
            'issues': issues,
            'test_files': len(test_files),
            'module_files': len(list(modules_dir.rglob("*.py"))) if modules_dir.exists() else 0
        }

    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = []
        report.append("PredictLab 测试报告")
        report.append("=" * 50)
        report.append(f"执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        if 'returncode' in results:
            status = "✅ 通过" if results['returncode'] == 0 else "❌ 失败"
            report.append(f"状态: {status}")
            report.append(f"返回码: {results['returncode']}")
            report.append(f"执行时间: {results.get('duration', 'N/A'):.2f}秒")
            report.append("")

        if 'stdout' in results and results['stdout']:
            report.append("标准输出:")
            report.append("-" * 30)
            report.append(results['stdout'][-1000:])  # 最后1000个字符
            report.append("")

        if 'stderr' in results and results['stderr']:
            report.append("标准错误:")
            report.append("-" * 30)
            report.append(results['stderr'][-1000:])
            report.append("")

        return "\n".join(report)

    def _run_command(self, cmd: List[str], test_type: str) -> Dict[str, Any]:
        """运行命令"""
        logger.info(f"执行命令: {' '.join(cmd)}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
        except subprocess.TimeoutExpired:
            logger.error(f"{test_type}超时")
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': f'{test_type}执行超时',
                'duration': time.time() - start_time
            }

        duration = time.time() - start_time

        logger.info(f"{test_type}完成，耗时: {duration:.2f}秒")

        return {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'duration': duration
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PredictLab 测试运行器')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 单元测试
    subparsers.add_parser('unit', help='运行单元测试')

    # 集成测试
    subparsers.add_parser('integration', help='运行集成测试')

    # 所有测试
    all_parser = subparsers.add_parser('all', help='运行所有测试')
    all_parser.add_argument('--no-coverage', action='store_true', help='不生成覆盖率报告')
    all_parser.add_argument('--parallel', action='store_true', help='并行执行')

    # 特定测试
    specific_parser = subparsers.add_parser('specific', help='运行特定测试')
    specific_parser.add_argument('test_path', help='测试文件路径')

    # 覆盖率测试
    subparsers.add_parser('coverage', help='生成详细覆盖率报告')

    # 性能测试
    subparsers.add_parser('performance', help='运行性能测试')

    # 检查测试结构
    subparsers.add_parser('check', help='检查测试结构')

    # 配置参数
    parser.add_argument('--markers', nargs='+', help='测试标记')
    parser.add_argument('--output', '-o', help='输出报告文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    runner = TestRunner()

    try:
        if args.command == 'unit':
            results = runner.run_unit_tests(args.markers)

        elif args.command == 'integration':
            results = runner.run_integration_tests(args.markers)

        elif args.command == 'all':
            results = runner.run_all_tests(
                coverage=not args.no_coverage,
                parallel=args.parallel
            )

        elif args.command == 'specific':
            results = runner.run_specific_test(args.test_path)

        elif args.command == 'coverage':
            results = runner.run_with_coverage_report()

        elif args.command == 'performance':
            results = runner.run_performance_tests()

        elif args.command == 'check':
            check_result = runner.check_test_structure()
            if check_result['success']:
                logger.info("✅ 测试结构检查通过")
                logger.info(f"测试文件: {check_result['test_files']}")
                logger.info(f"模块文件: {check_result['module_files']}")
            else:
                logger.error("❌ 测试结构检查失败:")
                for issue in check_result['issues']:
                    logger.error(f"  - {issue}")
            return

        else:
            parser.print_help()
            return

        # 生成报告
        report = runner.generate_test_report(results)

        # 输出到控制台
        print(report)

        # 保存到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"报告已保存到: {args.output}")

        # 返回适当的退出码
        sys.exit(results.get('returncode', 0))

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
