#!/usr/bin/env python3
"""
验证PredictLab项目重构结果
检查文件移动、import修正和项目结构
"""

import os
import sys
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

def check_directory_structure() -> Tuple[bool, List[str]]:
    """检查目录结构"""
    print("🔍 检查目录结构...")

    expected_dirs = [
        'db',
        'examples',
        'docs',
        'modules',
        'tests',
        'utils'
    ]

    expected_files = [
        'main.py',
        'config.py',
        'requirements.txt',
        'env.example',
        'README.md',
        'db/__init__.py',
        'examples/__init__.py',
        'docs/__init__.py',
        'modules/__init__.py'
    ]

    missing_dirs = []
    missing_files = []

    # 检查目录
    for dir_name in expected_dirs:
        if not (PROJECT_ROOT / dir_name).exists():
            missing_dirs.append(dir_name)

    # 检查文件
    for file_path in expected_files:
        if not (PROJECT_ROOT / file_path).exists():
            missing_files.append(file_path)

    success = len(missing_dirs) == 0 and len(missing_files) == 0

    issues = []
    if missing_dirs:
        issues.extend([f"缺少目录: {d}" for d in missing_dirs])
    if missing_files:
        issues.extend([f"缺少文件: {f}" for f in missing_files])

    return success, issues

def check_file_moves() -> Tuple[bool, List[str]]:
    """检查文件移动"""
    print("📄 检查文件移动...")

    moved_files = [
        ('db/data_manager.py', 'data_manager.py'),
        ('db/migration_manager.py', 'migration_manager.py'),
        ('db/init_database.py', 'init_database.py'),
        ('db/alembic', 'alembic'),
        ('examples/pipeline_demo.py', 'pipeline_demo.py'),
        ('examples/quality_monitor_demo.py', 'quality_monitor_demo.py'),
        ('docs/scheduler_README.md', 'scheduler_README.md'),
        ('docs/TESTING_README.md', 'TESTING_README.md'),
    ]

    issues = []

    for new_path, original_name in moved_files:
        if not (PROJECT_ROOT / new_path).exists():
            issues.append(f"文件未正确移动: {original_name} -> {new_path}")

    return len(issues) == 0, issues

def check_import_fixes() -> Tuple[bool, List[str]]:
    """检查import修正"""
    print("🔧 检查import修正...")

    files_to_check = [
        'examples/pipeline_demo.py',
        'examples/quality_monitor_demo.py',
        'tests/test_utils.py',
        'tests/conftest.py',
        'tests/unit/test_data_source.py',
        'tests/unit/test_data_storage.py',
    ]

    old_imports = [
        'from data_manager import',
        'from migration_manager import',
        'from migration_templates import',
        'from init_database import',
    ]

    issues = []

    for file_path in files_to_check:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            continue

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for old_import in old_imports:
                if old_import in content:
                    issues.append(f"未修正的import在 {file_path}: {old_import}")

        except Exception as e:
            issues.append(f"检查文件失败 {file_path}: {e}")

    return len(issues) == 0, issues

def check_alembic_config() -> Tuple[bool, List[str]]:
    """检查Alembic配置"""
    print("⚙️ 检查Alembic配置...")

    alembic_ini = PROJECT_ROOT / 'alembic.ini'
    if not alembic_ini.exists():
        return False, ["alembic.ini不存在"]

    try:
        with open(alembic_ini, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'script_location = db/alembic' in content:
            return True, []
        else:
            return False, ["Alembic script_location未修正"]

    except Exception as e:
        return False, [f"读取alembic.ini失败: {e}"]

def check_module_imports() -> Tuple[bool, List[str]]:
    """检查模块导入（不依赖外部包）"""
    print("📦 检查模块导入...")

    # 这些import不依赖外部包，可以直接测试
    safe_imports = [
        ('utils.exceptions', 'PredictLabError'),
        ('utils.error_handler', 'handle_errors'),
    ]

    issues = []

    # 临时添加项目路径
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

    for module_name, attr_name in safe_imports:
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                issues.append(f"模块不存在: {module_name}")
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, attr_name):
                issues.append(f"模块属性不存在: {module_name}.{attr_name}")

        except Exception as e:
            issues.append(f"导入失败 {module_name}.{attr_name}: {e}")

    return len(issues) == 0, issues

def generate_structure_tree() -> str:
    """生成目录结构树"""
    def tree(dir_path: Path, prefix: str = "") -> List[str]:
        lines = []
        try:
            items = sorted(dir_path.iterdir())
            for i, item in enumerate(items):
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue

                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "

                if item.is_dir():
                    lines.append(f"{prefix}{connector}{item.name}/")
                    extension = "    " if is_last else "│   "
                    lines.extend(tree(item, prefix + extension))
                else:
                    lines.append(f"{prefix}{connector}{item.name}")

        except PermissionError:
            pass

        return lines

    tree_lines = ["PredictLab/"]
    tree_lines.extend(tree(PROJECT_ROOT))

    return "\n".join(tree_lines)

def main():
    """主函数"""
    print("🔍 PredictLab 项目重构验证")
    print("=" * 50)

    checks = [
        ("目录结构", check_directory_structure),
        ("文件移动", check_file_moves),
        ("Import修正", check_import_fixes),
        ("Alembic配置", check_alembic_config),
        ("模块导入", check_module_imports),
    ]

    all_success = True
    all_issues = []

    for check_name, check_func in checks:
        success, issues = check_func()
        if success:
            print(f"✅ {check_name}: 通过")
        else:
            print(f"❌ {check_name}: 失败")
            all_success = False
            all_issues.extend(issues)

    print("\n" + "=" * 50)
    print("📋 验证结果")

    if all_success:
        print("🎉 所有检查通过！项目重构成功。")
    else:
        print(f"❌ 发现 {len(all_issues)} 个问题:")
        for issue in all_issues:
            print(f"  • {issue}")

    print("\n" + "=" * 50)
    print("📁 当前项目结构:")
    print(generate_structure_tree())

    print("\n" + "=" * 50)
    print("💡 使用指南:")
    print("1. 运行主程序: python main.py")
    print("2. 查看demo: python examples/pipeline_demo.py")
    print("3. 运行测试: python run_tests.py all")
    print("4. 数据库管理: python db/migration_manager.py")
    print("5. 查看文档: docs/*.md")

    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())
