#!/usr/bin/env python3
"""
PredictLab 项目重构脚本
将项目目录重新组织为更清晰的结构
"""

import os
import shutil
import sys
import re
from pathlib import Path
from typing import Dict, List, Set

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 文件移动映射
FILE_MOVES = {
    # 数据库相关文件 -> db/
    'data_manager.py': 'db/data_manager.py',
    'database_examples.sql': 'db/database_examples.sql',
    'database_quickstart.md': 'db/database_quickstart.md',
    'database_README.md': 'db/database_README.md',
    'database_schema.sql': 'db/database_schema.sql',
    'init_database.py': 'db/init_database.py',
    'migration_manager.py': 'db/migration_manager.py',
    'migration_quickstart.py': 'db/migration_quickstart.py',
    'migration_README.md': 'db/migration_README.md',
    'migration_templates.py': 'db/migration_templates.py',
    'MIGRATION_SETUP.md': 'db/MIGRATION_SETUP.md',
    'test_migration.py': 'db/test_migration.py',

    # demo脚本 -> examples/
    'pipeline_demo.py': 'examples/pipeline_demo.py',
    'quality_monitor_demo.py': 'examples/quality_monitor_demo.py',

    # 文档 -> docs/
    'scheduler_README.md': 'docs/scheduler_README.md',
    'TESTING_README.md': 'docs/TESTING_README.md',
    'TESTING_SETUP.md': 'docs/TESTING_SETUP.md',
}

# 目录移动映射
DIR_MOVES = {
    'alembic': 'db/alembic'
}

# import路径修正映射
IMPORT_FIXES = {
    # data_manager 相关
    r'from data_manager import': 'from db.data_manager import',
    r'import data_manager': 'import db.data_manager',

    # migration_manager 相关
    r'from migration_manager import': 'from db.migration_manager import',
    r'import migration_manager': 'import db.migration_manager',

    # migration_templates 相关
    r'from migration_templates import': 'from db.migration_templates import',
    r'import migration_templates': 'import db.migration_templates',

    # migration_quickstart 相关
    r'from migration_quickstart import': 'from db.migration_quickstart import',
    r'import migration_quickstart': 'import db.migration_quickstart',

    # init_database 相关
    r'from init_database import': 'from db.init_database import',
    r'import init_database': 'import db.init_database',
}

class ProjectRefactor:
    """项目重构器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / 'backup_before_refactor'
        self.errors = []
        self.warnings = []

    def create_backup(self):
        """创建备份"""
        print("📦 创建备份...")
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)

        shutil.copytree(self.project_root, self.backup_dir,
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))

        # 移除备份中的备份目录本身
        backup_backup = self.backup_dir / 'backup_before_refactor'
        if backup_backup.exists():
            shutil.rmtree(backup_backup)

        print(f"✅ 备份创建完成: {self.backup_dir}")

    def move_directories(self):
        """移动目录"""
        print("📁 移动目录...")

        for src_dir, dst_dir in DIR_MOVES.items():
            src_path = self.project_root / src_dir
            dst_path = self.project_root / dst_dir

            if src_path.exists():
                print(f"  移动目录: {src_dir} -> {dst_dir}")
                if dst_path.exists():
                    shutil.rmtree(dst_path)
                shutil.move(str(src_path), str(dst_path))
            else:
                self.warnings.append(f"目录不存在: {src_dir}")

    def move_files(self):
        """移动文件"""
        print("📄 移动文件...")

        for src_file, dst_file in FILE_MOVES.items():
            src_path = self.project_root / src_file
            dst_path = self.project_root / dst_file

            if src_path.exists():
                print(f"  移动文件: {src_file} -> {dst_file}")

                # 确保目标目录存在
                dst_path.parent.mkdir(parents=True, exist_ok=True)

                # 如果目标文件已存在，先删除
                if dst_path.exists():
                    dst_path.unlink()

                shutil.move(str(src_path), str(dst_path))
            else:
                self.warnings.append(f"文件不存在: {src_file}")

    def create_init_files(self):
        """创建__init__.py文件"""
        print("📝 创建包初始化文件...")

        # db/__init__.py
        db_init = self.project_root / 'db' / '__init__.py'
        db_init.write_text('"""PredictLab 数据库模块"""\n')

        # examples/__init__.py
        examples_init = self.project_root / 'examples' / '__init__.py'
        examples_init.write_text('"""PredictLab 示例脚本"""\n')

        # docs/__init__.py (可选)
        docs_init = self.project_root / 'docs' / '__init__.py'
        docs_init.write_text('"""PredictLab 文档"""\n')

        print("✅ 包初始化文件创建完成")

    def fix_import_paths(self):
        """修正import路径"""
        print("🔧 修正import路径...")

        # 需要检查的文件类型
        file_patterns = ['*.py']

        for pattern in file_patterns:
            for file_path in self.project_root.rglob(pattern):
                # 跳过新创建的目录和备份目录
                if any(part in file_path.parts for part in ['db', 'examples', 'docs', 'backup_before_refactor']):
                    continue

                try:
                    self._fix_file_imports(file_path)
                except Exception as e:
                    self.errors.append(f"修正文件失败 {file_path}: {e}")

    def _fix_file_imports(self, file_path: Path):
        """修正单个文件的import"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            modified = False

            # 应用import修正
            for old_pattern, new_import in IMPORT_FIXES.items():
                if re.search(old_pattern, content):
                    content = re.sub(old_pattern, new_import, content)
                    modified = True

            # 如果内容有变化，写回文件
            if modified and content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  修正文件: {file_path.relative_to(self.project_root)}")

        except Exception as e:
            self.errors.append(f"处理文件失败 {file_path}: {e}")

    def fix_demo_imports(self):
        """修正demo脚本的import路径"""
        print("🔧 修正demo脚本imports...")

        examples_dir = self.project_root / 'examples'
        if not examples_dir.exists():
            return

        for demo_file in examples_dir.glob('*.py'):
            try:
                with open(demo_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 修正相对导入
                content = re.sub(r'from \.\.modules', 'from modules', content)
                content = re.sub(r'from \.\.config', 'from config', content)
                content = re.sub(r'from \.\.db', 'from db', content)

                with open(demo_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"  修正demo文件: {demo_file.relative_to(self.project_root)}")

            except Exception as e:
                self.errors.append(f"修正demo文件失败 {demo_file}: {e}")

    def fix_alembic_config(self):
        """修正alembic配置"""
        print("🔧 修正Alembic配置...")

        alembic_ini = self.project_root / 'alembic.ini'
        if alembic_ini.exists():
            try:
                with open(alembic_ini, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 修正script_location路径
                content = content.replace('script_location = alembic',
                                        'script_location = db/alembic')

                with open(alembic_ini, 'w', encoding='utf-8') as f:
                    f.write(content)

                print("  ✅ Alembic配置已修正")

            except Exception as e:
                self.errors.append(f"修正alembic.ini失败: {e}")

    def fix_test_imports(self):
        """修正测试文件的import路径"""
        print("🔧 修正测试文件imports...")

        tests_dir = self.project_root / 'tests'
        if not tests_dir.exists():
            return

        for test_file in tests_dir.rglob('*.py'):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 修正import路径
                content = re.sub(r'from data_manager import', 'from db.data_manager import', content)
                content = re.sub(r'from migration_manager import', 'from db.migration_manager import', content)
                content = re.sub(r'from migration_templates import', 'from db.migration_templates import', content)

                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                print(f"  修正测试文件: {test_file.relative_to(self.project_root)}")

            except Exception as e:
                self.errors.append(f"修正测试文件失败 {test_file}: {e}")

    def validate_structure(self):
        """验证目录结构"""
        print("🔍 验证目录结构...")

        expected_structure = {
            'db': ['__init__.py', 'data_manager.py', 'migration_manager.py', 'init_database.py', 'alembic'],
            'examples': ['__init__.py', 'pipeline_demo.py', 'quality_monitor_demo.py'],
            'docs': ['__init__.py', 'scheduler_README.md', 'TESTING_README.md', 'TESTING_SETUP.md'],
            'tests': ['conftest.py', 'test_utils.py'],  # 至少这些文件
            'modules': ['__init__.py'],  # 至少有__init__.py
            'utils': ['__init__.py']  # 至少有__init__.py
        }

        missing_files = []

        for dir_name, expected_files in expected_structure.items():
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                missing_files.append(f"目录不存在: {dir_name}/")
                continue

            for expected_file in expected_files:
                file_path = dir_path / expected_file
                if not file_path.exists():
                    missing_files.append(f"文件不存在: {dir_name}/{expected_file}")

        if missing_files:
            self.warnings.extend(missing_files)
            print("⚠️  结构验证发现问题:")
            for issue in missing_files:
                print(f"    {issue}")
        else:
            print("✅ 目录结构验证通过")

    def test_imports(self):
        """测试import是否正常"""
        print("🧪 测试imports...")

        test_imports = [
            ('config', 'config'),
            ('modules.data_source.base', 'BaseDataSource'),
            ('modules.data_processing.data_cleaner', 'DataCleaner'),
            ('modules.data_storage.postgres_storage', 'PostgresStorage'),
            ('db.data_manager', 'DataManager'),
            ('db.migration_manager', 'MigrationManager'),
            ('utils.exceptions', 'PredictLabError'),
            ('utils.error_handler', 'handle_errors'),
        ]

        failed_imports = []

        for module_name, attr_name in test_imports:
            try:
                module = __import__(module_name, fromlist=[attr_name])
                getattr(module, attr_name)
                print(f"  ✅ {module_name}.{attr_name}")
            except Exception as e:
                failed_imports.append(f"{module_name}.{attr_name}: {e}")
                print(f"  ❌ {module_name}.{attr_name}: {e}")

        if failed_imports:
            self.errors.extend(failed_imports)

    def generate_report(self):
        """生成重构报告"""
        print("\n" + "="*60)
        print("📋 PredictLab 项目重构报告")
        print("="*60)

        print("\n📁 文件移动:")
        for src, dst in FILE_MOVES.items():
            status = "✅" if (self.project_root / dst).exists() else "❌"
            print(f"  {status} {src} -> {dst}")

        print("\n📁 目录移动:")
        for src, dst in DIR_MOVES.items():
            status = "✅" if (self.project_root / dst).exists() else "❌"
            print(f"  {status} {src}/ -> {dst}/")

        if self.errors:
            print(f"\n❌ 错误 ({len(self.errors)} 个):")
            for error in self.errors:
                print(f"  • {error}")

        if self.warnings:
            print(f"\n⚠️  警告 ({len(self.warnings)} 个):")
            for warning in self.warnings:
                print(f"  • {warning}")

        success = len(self.errors) == 0
        if success:
            print("\n🎉 重构成功完成！")
            print("\n💡 接下来:")
            print("1. 运行 python main.py --help 查看主程序")
            print("2. 运行 python examples/pipeline_demo.py 测试demo")
            print("3. 运行 python run_tests.py check 验证测试")
        else:
            print(f"\n❌ 重构完成但有 {len(self.errors)} 个错误")
            print("请检查错误信息并手动修复")

        return success

def main():
    """主函数"""
    print("🚀 开始 PredictLab 项目重构...")

    refactor = ProjectRefactor(PROJECT_ROOT)

    try:
        # 执行重构步骤
        refactor.create_backup()
        refactor.move_directories()
        refactor.move_files()
        refactor.create_init_files()
        refactor.fix_import_paths()
        refactor.fix_demo_imports()
        refactor.fix_alembic_config()
        refactor.fix_test_imports()
        refactor.validate_structure()
        refactor.test_imports()

        # 生成报告
        success = refactor.generate_report()

        return 0 if success else 1

    except Exception as e:
        print(f"❌ 重构过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
