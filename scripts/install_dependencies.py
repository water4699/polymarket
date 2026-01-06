#!/usr/bin/env python3
"""
PredictLab 依赖安装和验证脚本
检查并安装项目所需的依赖包
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 依赖包列表
DEPENDENCIES = {
    # 核心依赖
    'pandas': 'pandas>=1.5.0',
    'numpy': 'numpy>=1.21.0',
    'requests': 'requests>=2.28.0',
    'sqlalchemy': 'sqlalchemy>=1.4.0',
    'psycopg2': 'psycopg2-binary>=2.9.0',

    # 异步支持
    'aiohttp': 'aiohttp>=3.8.0',

    # 数据处理
    'ccxt': 'ccxt>=4.0.0',

    # 数据库迁移
    'alembic': 'alembic>=1.8.0',

    # 工具
    'loguru': 'loguru>=0.6.0',
    'pydantic': 'pydantic>=1.9.0',

    # 开发工具
    'pytest': 'pytest>=7.0.0',
    'pytest_asyncio': 'pytest-asyncio>=0.21.0',
    'pytest_cov': 'pytest-cov>=4.0.0',
    'faker': 'faker>=15.0.0',
}

# 可选依赖
OPTIONAL_DEPENDENCIES = {
    'pymongo': 'pymongo>=4.0.0',
    'web3': 'web3>=6.0.0',
    'dotenv': 'python-dotenv>=0.19.0',
    'freezegun': 'freezegun>=1.2.0',
    'pytest_mock': 'pytest-mock>=3.10.0',
    'xdist': 'pytest-xdist>=3.0.0',
}

def check_dependency(module_name: str, package_name: str = None) -> tuple[bool, str]:
    """
    检查依赖包是否已安装

    Args:
        module_name: 模块名
        package_name: 包名 (如果与模块名不同)

    Returns:
        (是否安装成功, 版本信息或错误信息)
    """
    if package_name is None:
        package_name = module_name

    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False, f"模块 {module_name} 未找到"

        # 尝试导入并获取版本
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        version = getattr(module, '__version__', '未知版本')
        return True, f"v{version}"

    except Exception as e:
        return False, str(e)

def install_package(package_spec: str) -> tuple[bool, str]:
    """
    安装Python包

    Args:
        package_spec: 包规格 (如 'pandas>=1.5.0')

    Returns:
        (是否安装成功, 输出信息)
    """
    try:
        # 尝试使用不同的pip命令
        commands = [
            [sys.executable, '-m', 'pip', 'install', package_spec],
            ['pip3', 'install', package_spec],
            ['pip', 'install', package_spec],
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )

                if result.returncode == 0:
                    return True, "安装成功"
                else:
                    continue  # 尝试下一个命令

            except FileNotFoundError:
                continue  # 命令不存在，尝试下一个
            except subprocess.TimeoutExpired:
                return False, "安装超时"

        return False, "所有安装命令都失败"

    except Exception as e:
        return False, f"安装异常: {e}"

def check_all_dependencies() -> dict:
    """
    检查所有依赖包状态

    Returns:
        包含所有依赖状态的字典
    """
    results = {
        'required': {},
        'optional': {},
        'missing_required': [],
        'missing_optional': []
    }

    print("🔍 检查必需依赖...")

    for module_name, package_spec in DEPENDENCIES.items():
        installed, info = check_dependency(module_name)
        results['required'][module_name] = {
            'installed': installed,
            'info': info,
            'package_spec': package_spec
        }

        if not installed:
            results['missing_required'].append((module_name, package_spec))
        else:
            print(f"  ✅ {module_name}: {info}")

    print("\n🔍 检查可选依赖...")

    for module_name, package_spec in OPTIONAL_DEPENDENCIES.items():
        installed, info = check_dependency(module_name)
        results['optional'][module_name] = {
            'installed': installed,
            'info': info,
            'package_spec': package_spec
        }

        if not installed:
            results['missing_optional'].append((module_name, package_spec))
        else:
            print(f"  ✅ {module_name}: {info}")

    return results

def install_missing_dependencies(results: dict, auto_install: bool = False) -> dict:
    """
    安装缺失的依赖

    Args:
        results: 依赖检查结果
        auto_install: 是否自动安装

    Returns:
        安装结果
    """
    install_results = {
        'installed': [],
        'failed': []
    }

    # 处理必需依赖
    if results['missing_required']:
        print(f"\n📦 发现 {len(results['missing_required'])} 个缺失的必需依赖:")
        for module_name, package_spec in results['missing_required']:
            print(f"  • {package_spec}")

        if auto_install or input("\n是否安装必需依赖? (y/N): ").lower() == 'y':
            print("\n🔧 开始安装必需依赖...")
            for module_name, package_spec in results['missing_required']:
                print(f"  安装 {package_spec}...")
                success, message = install_package(package_spec)
                if success:
                    install_results['installed'].append(package_spec)
                    print(f"    ✅ {message}")
                else:
                    install_results['failed'].append((package_spec, message))
                    print(f"    ❌ {message}")

    # 处理可选依赖
    if results['missing_optional']:
        print(f"\n📦 发现 {len(results['missing_optional'])} 个缺失的可选依赖:")
        for module_name, package_spec in results['missing_optional']:
            print(f"  • {package_spec}")

        if auto_install or input("\n是否安装可选依赖? (y/N): ").lower() == 'y':
            print("\n🔧 开始安装可选依赖...")
            for module_name, package_spec in results['missing_optional']:
                print(f"  安装 {package_spec}...")
                success, message = install_package(package_spec)
                if success:
                    install_results['installed'].append(package_spec)
                    print(f"    ✅ {message}")
                else:
                    install_results['failed'].append((package_spec, message))
                    print(f"    ❌ {message}")

    return install_results

def generate_install_commands(results: dict) -> str:
    """
    生成安装命令

    Args:
        results: 依赖检查结果

    Returns:
        安装命令字符串
    """
    commands = []

    if results['missing_required']:
        required_packages = [spec for _, spec in results['missing_required']]
        commands.append("# 安装必需依赖")
        commands.append(f"pip install {' '.join(required_packages)}")

    if results['missing_optional']:
        optional_packages = [spec for _, spec in results['missing_optional']]
        commands.append("\n# 安装可选依赖")
        commands.append(f"pip install {' '.join(optional_packages)}")

    # 完整安装命令
    commands.append("\n# 或使用requirements.txt一次性安装所有依赖")
    commands.append("pip install -r requirements.txt")

    return "\n".join(commands)

def main():
    """主函数"""
    print("🚀 PredictLab 依赖检查和安装工具")
    print("=" * 50)

    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print(f"项目路径: {PROJECT_ROOT}")
    print()

    # 检查依赖
    results = check_all_dependencies()

    # 生成报告
    print("\n" + "=" * 50)
    print("📋 依赖检查报告")

    missing_required = len(results['missing_required'])
    missing_optional = len(results['missing_optional'])

    if missing_required == 0 and missing_optional == 0:
        print("🎉 所有依赖都已安装！")
        print("\n💡 您可以运行以下命令验证项目:")
        print("  python main.py --help")
        print("  python run_tests.py check")
        return 0
    else:
        print(f"❌ 发现 {missing_required} 个缺失的必需依赖")
        print(f"⚠️  发现 {missing_optional} 个缺失的可选依赖")

        # 生成安装命令
        install_commands = generate_install_commands(results)
        print("\n🔧 建议安装命令:")
        print(install_commands)

        # 尝试自动安装
        if '--auto-install' in sys.argv:
            print("\n🔧 自动安装模式已启用...")
            install_results = install_missing_dependencies(results, auto_install=True)

            if install_results['installed']:
                print(f"\n✅ 成功安装 {len(install_results['installed'])} 个包")

            if install_results['failed']:
                print(f"\n❌ {len(install_results['failed'])} 个包安装失败:")
                for package, error in install_results['failed']:
                    print(f"  • {package}: {error}")

            # 重新检查
            print("\n🔄 重新检查依赖...")
            new_results = check_all_dependencies()

            remaining_required = len(new_results['missing_required'])
            if remaining_required == 0:
                print("\n🎉 所有必需依赖安装完成！")
                return 0
            else:
                print(f"\n❌ 仍有 {remaining_required} 个必需依赖未安装")
                return 1
        else:
            print("\n💡 运行以下命令自动安装:")
            print("  python install_dependencies.py --auto-install")
            return 1

if __name__ == "__main__":
    sys.exit(main())
