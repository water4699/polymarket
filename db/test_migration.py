#!/usr/bin/env python3
"""
数据库迁移系统测试脚本
验证迁移功能是否正常工作
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from migration_manager import MigrationManager
from alembic.environments import EnvironmentConfig

logger = get_logger(__name__)


def test_migration_system():
    """测试迁移系统"""
    logger.info("开始测试迁移系统...")

    # 1. 测试环境配置
    logger.info("1. 测试环境配置...")
    try:
        dev_config = EnvironmentConfig.get_config('development')
        assert 'database_url' in dev_config
        logger.info("✅ 环境配置正常")
    except Exception as e:
        logger.error(f"❌ 环境配置失败: {e}")
        return False

    # 2. 测试迁移管理器初始化
    logger.info("2. 测试迁移管理器...")
    try:
        manager = MigrationManager()
        logger.info("✅ 迁移管理器初始化成功")
    except Exception as e:
        logger.error(f"❌ 迁移管理器初始化失败: {e}")
        return False

    # 3. 测试迁移文件存在
    logger.info("3. 测试迁移文件...")
    migration_files = list(manager.versions_dir.glob("*.py"))
    if migration_files:
        logger.info(f"✅ 找到 {len(migration_files)} 个迁移文件")
        for mf in migration_files:
            logger.info(f"   - {mf.name}")
    else:
        logger.warning("⚠️  没有找到迁移文件")

    # 4. 测试迁移模板
    logger.info("4. 测试迁移模板...")
    try:
        from migration_templates import MigrationTemplate
        template = MigrationTemplate.create_add_column_template(
            'test_table', 'test_column', 'sa.String(length=100)'
        )
        assert 'test_column' in template
        assert 'upgrade()' in template
        assert 'downgrade()' in template
        logger.info("✅ 迁移模板生成正常")
    except Exception as e:
        logger.error(f"❌ 迁移模板测试失败: {e}")
        return False

    # 5. 测试迁移验证器
    logger.info("5. 测试迁移验证器...")
    try:
        from migration_templates import MigrationValidator
        # 创建临时迁移文件进行测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('''"""
Test migration
"""
revision = 'test'
down_revision = None

def upgrade():
    pass

def downgrade():
    pass
''')
            temp_file = f.name

        try:
            result = MigrationValidator.validate_migration_file(temp_file)
            assert result['valid'] == True
            logger.info("✅ 迁移验证器正常")
        finally:
            os.unlink(temp_file)
    except Exception as e:
        logger.error(f"❌ 迁移验证器测试失败: {e}")
        return False

    logger.info("🎉 迁移系统测试完成!")
    return True


def test_database_connection():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    try:
        from modules.data_storage.postgres_storage import PostgresStorage
        storage = PostgresStorage()

        if storage.connect():
            logger.info("✅ 数据库连接成功")
            storage.disconnect()
            return True
        else:
            logger.warning("⚠️  数据库连接失败 (可能是配置问题)")
            return False
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='测试数据库迁移系统')
    parser.add_argument('--skip-db', action='store_true',
                       help='跳过数据库连接测试')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 开始测试 PredictLab 数据库迁移系统")

    tests = [
        ("迁移系统功能", test_migration_system)
    ]

    if not args.skip_db:
        tests.append(("数据库连接", test_database_connection))

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"执行测试: {test_name}")
        logger.info('='*50)

        try:
            success = test_func()
            results.append((test_name, success))

            if success:
                logger.info(f"✅ {test_name} 通过")
            else:
                logger.error(f"❌ {test_name} 失败")

        except Exception as e:
            logger.error(f"❌ {test_name} 异常: {e}")
            results.append((test_name, False))

    # 总结
    logger.info(f"\n{'='*50}")
    logger.info("测试总结")
    logger.info('='*50)

    passed = 0
    total = len(results)

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{status} {test_name}")
        if success:
            passed += 1

    logger.info(f"\n总体结果: {passed}/{total} 项测试通过")

    if passed == total:
        logger.info("🎉 所有测试通过!")
        return 0
    else:
        logger.error("❌ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
