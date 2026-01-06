#!/usr/bin/env python3
"""
PredictLab 数据库迁移快速开始脚本
自动初始化数据库和运行基础迁移
"""
import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from config import config
from modules.data_storage.postgres_storage import PostgresStorage

logger = get_logger(__name__)


def check_dependencies():
    """检查依赖"""
    logger.info("检查依赖...")
    try:
        import alembic
        import sqlalchemy
        import psycopg2
        logger.info("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        logger.info("请运行: pip install -r requirements.txt")
        return False


def check_database_connection():
    """检查数据库连接"""
    logger.info("检查数据库连接...")
    storage = PostgresStorage()
    if storage.connect():
        logger.info("✅ 数据库连接成功")
        storage.disconnect()
        return True
    else:
        logger.error("❌ 数据库连接失败")
        logger.info("请检查数据库配置和网络连接")
        return False


def init_database():
    """初始化数据库"""
    logger.info("初始化数据库...")

    # 使用 init_database.py 创建表
    if (project_root / "init_database.py").exists():
        logger.info("使用 init_database.py 创建表...")
        result = subprocess.run([
            sys.executable, "init_database.py"
        ], cwd=project_root, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("✅ 数据库初始化成功")
            return True
        else:
            logger.error(f"❌ 数据库初始化失败: {result.stderr}")
            return False
    else:
        logger.warning("⚠️  init_database.py 不存在，跳过初始化")
        return True


def run_migration_manager(command, env="development", **kwargs):
    """运行迁移管理器"""
    cmd = [sys.executable, "migration_manager.py", command, "--env", env]

    for key, value in kwargs.items():
        if isinstance(value, bool) and value:
            cmd.append(f"--{key}")
        elif value:
            cmd.extend([f"--{key}", str(value)])

    logger.info(f"执行命令: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

    if result.returncode == 0:
        print(result.stdout)
        return True
    else:
        print(result.stderr)
        return False


def quickstart_development():
    """开发环境快速开始"""
    logger.info("🚀 开始开发环境快速设置...")

    steps = [
        ("检查依赖", check_dependencies),
        ("检查数据库连接", check_database_connection),
        ("初始化数据库", init_database),
        ("检查迁移状态", lambda: run_migration_manager("status")),
        ("运行迁移", lambda: run_migration_manager("upgrade")),
        ("验证迁移", lambda: run_migration_manager("status"))
    ]

    for step_name, step_func in steps:
        logger.info(f"执行: {step_name}")
        if not step_func():
            logger.error(f"❌ {step_name} 失败")
            return False
        logger.info(f"✅ {step_name} 完成")

    logger.info("🎉 开发环境设置完成!")
    logger.info("\n下一步:")
    logger.info("1. 运行 python main.py --demo 查看演示")
    logger.info("2. 运行 python main.py --pipeline 运行数据管道")
    logger.info("3. 查看 migration_README.md 了解更多迁移操作")

    return True


def quickstart_production():
    """生产环境快速开始"""
    logger.warning("⚠️  生产环境设置需要谨慎操作")

    if not os.getenv('DATABASE_URL'):
        logger.error("❌ 生产环境需要设置 DATABASE_URL 环境变量")
        return False

    logger.info("🔒 生产环境检查...")

    # 检查是否在维护模式
    maintenance_mode = os.getenv('MAINTENANCE_MODE', 'false').lower() == 'true'
    if not maintenance_mode:
        logger.warning("⚠️  建议在维护模式下运行生产迁移")

    # 运行迁移
    if run_migration_manager("status", "production"):
        logger.info("备份数据库...")
        if not run_migration_manager("backup", "production"):
            logger.error("❌ 备份失败，取消迁移")
            return False

        logger.info("运行迁移...")
        if run_migration_manager("upgrade", "production"):
            logger.info("✅ 生产环境迁移完成")
            return True

    return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PredictLab 数据库迁移快速开始')
    parser.add_argument('--env', choices=['development', 'testing', 'production'],
                       default='development', help='目标环境')
    parser.add_argument('--skip-db-init', action='store_true',
                       help='跳过数据库初始化')
    parser.add_argument('--force', action='store_true',
                       help='强制执行（生产环境）')

    args = parser.parse_args()

    # 设置环境变量
    os.environ['PREDICTLAB_ENV'] = args.env

    logger.info(f"环境: {args.env}")

    if args.env == 'production' and not args.force:
        confirm = input("⚠️  生产环境操作，请确认 (yes/no): ")
        if confirm.lower() != 'yes':
            logger.info("操作已取消")
            return

    try:
        if args.env == 'production':
            success = quickstart_production()
        else:
            success = quickstart_development()

        if success:
            logger.info("🎉 快速开始完成!")
            sys.exit(0)
        else:
            logger.error("❌ 快速开始失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\n操作已取消")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
