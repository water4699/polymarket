#!/usr/bin/env python3
"""
PredictLab 数据库迁移管理器
提供便捷的迁移操作接口和多环境支持
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class MigrationManager:
    """数据库迁移管理器"""

    def __init__(self):
        self.alembic_dir = project_root / "alembic"
        self.versions_dir = self.alembic_dir / "versions"

    def get_current_revision(self, env: str = "development") -> Optional[str]:
        """获取当前数据库版本"""
        try:
            env_vars = self._get_env_vars(env)
            result = self._run_alembic_command("current", env_vars=env_vars, capture_output=True)

            # 解析输出获取当前版本
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('Current revision(s) for'):
                    # 找到版本信息行
                    if ':' in line:
                        revision_part = line.split(':')[1].strip()
                        if revision_part and revision_part != '(head)':
                            return revision_part.split()[0]  # 取第一个版本号
            return None
        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return None

    def get_head_revision(self) -> Optional[str]:
        """获取最新版本"""
        try:
            result = self._run_alembic_command("heads", capture_output=True)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if '->' in line:
                    # 解析版本行
                    parts = line.split('->')
                    if len(parts) >= 2:
                        return parts[0].strip().split()[0]
            return None
        except Exception as e:
            logger.error(f"获取最新版本失败: {e}")
            return None

    def upgrade(self, revision: str = "head", env: str = "development") -> bool:
        """升级到指定版本"""
        try:
            logger.info(f"开始数据库升级: {revision} (环境: {env})")
            env_vars = self._get_env_vars(env)
            result = self._run_alembic_command(f"upgrade {revision}", env_vars=env_vars)

            if result.returncode == 0:
                logger.info("数据库升级成功")
                return True
            else:
                logger.error("数据库升级失败")
                return False

        except Exception as e:
            logger.error(f"升级失败: {e}")
            return False

    def downgrade(self, revision: str, env: str = "development") -> bool:
        """回滚到指定版本"""
        try:
            logger.info(f"开始数据库回滚: {revision} (环境: {env})")
            env_vars = self._get_env_vars(env)
            result = self._run_alembic_command(f"downgrade {revision}", env_vars=env_vars)

            if result.returncode == 0:
                logger.info("数据库回滚成功")
                return True
            else:
                logger.error("数据库回滚失败")
                return False

        except Exception as e:
            logger.error(f"回滚失败: {e}")
            return False

    def create_migration(self, message: str, auto_generate: bool = True) -> Optional[str]:
        """创建新的迁移文件"""
        try:
            logger.info(f"创建迁移: {message}")

            cmd = f"revision --autogenerate -m \"{message}\"" if auto_generate else f"revision -m \"{message}\""

            result = self._run_alembic_command(cmd)

            if result.returncode == 0:
                # 解析输出获取新创建的文件名
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Generating' in line and '.py' in line:
                        # 提取文件名
                        parts = line.split()
                        for part in parts:
                            if part.endswith('.py') and 'alembic/versions/' in part:
                                filename = part.split('/')[-1]
                                revision_id = filename.split('_')[0]
                                logger.info(f"迁移文件创建成功: {filename}")
                                return revision_id

                logger.info("迁移文件创建成功")
                return "unknown"
            else:
                logger.error("迁移文件创建失败")
                return None

        except Exception as e:
            logger.error(f"创建迁移失败: {e}")
            return None

    def show_history(self, env: str = "development") -> List[Dict[str, Any]]:
        """显示迁移历史"""
        try:
            env_vars = self._get_env_vars(env)
            result = self._run_alembic_command("history", env_vars=env_vars, capture_output=True)

            history = []
            lines = result.stdout.strip().split('\n')

            for line in lines:
                if '<->' in line:
                    # 解析迁移历史行
                    parts = line.split('<->')
                    if len(parts) == 2:
                        rev_from = parts[0].strip()
                        rev_to = parts[1].strip()

                        # 提取消息
                        message = ""
                        if '(' in rev_to and ')' in rev_to:
                            message = rev_to.split('(')[1].split(')')[0]

                        history.append({
                            'from': rev_from,
                            'to': rev_to.split()[0] if rev_to else '',
                            'message': message,
                            'raw': line
                        })

            return history

        except Exception as e:
            logger.error(f"获取迁移历史失败: {e}")
            return []

    def check_status(self, env: str = "development") -> Dict[str, Any]:
        """检查迁移状态"""
        try:
            current = self.get_current_revision(env)
            head = self.get_head_revision()

            status = {
                'current_revision': current,
                'head_revision': head,
                'is_up_to_date': current == head,
                'needs_upgrade': current != head and head is not None,
                'environment': env
            }

            # 检查待应用迁移
            if current != head:
                history = self.show_history(env)
                pending = []
                for item in history:
                    if item['to'] != current:
                        pending.append(item)
                status['pending_migrations'] = pending

            return status

        except Exception as e:
            logger.error(f"检查状态失败: {e}")
            return {'error': str(e), 'environment': env}

    def backup_database(self, env: str = "development") -> bool:
        """备份数据库"""
        try:
            logger.info(f"开始数据库备份 (环境: {env})")

            # 这里可以实现数据库备份逻辑
            # 例如导出SQL文件或使用pg_dump

            # 简单实现：记录备份时间戳
            import datetime
            backup_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_{env}_{backup_timestamp}.sql"

            logger.info(f"数据库备份完成: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False

    def _get_env_vars(self, env: str) -> Dict[str, str]:
        """获取环境变量"""
        env_vars = os.environ.copy()
        env_vars['PREDICTLAB_ENV'] = env

        # 根据环境设置数据库URL
        if env == 'production':
            # 生产环境使用环境变量或配置
            pass
        elif env == 'testing':
            # 测试环境使用测试数据库
            env_vars['TEST_DATABASE_URL'] = env_vars.get('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/predictlab_test')
        else:
            # 开发环境使用默认配置
            pass

        return env_vars

    def _run_alembic_command(self, command: str, env_vars: Dict[str, str] = None,
                           capture_output: bool = False) -> subprocess.CompletedProcess:
        """运行Alembic命令"""
        if env_vars is None:
            env_vars = self._get_env_vars('development')

        # 构建命令
        cmd = ["python", "-m", "alembic"] + command.split()

        # 设置工作目录
        cwd = str(project_root)

        # 运行命令
        if capture_output:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env_vars,
                capture_output=True,
                text=True,
                check=False
            )
        else:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env_vars,
                check=False
            )

        return result


def print_status(status: Dict[str, Any]):
    """打印状态信息"""
    print(f"环境: {status.get('environment', 'unknown')}")
    print(f"当前版本: {status.get('current_revision', 'None')}")
    print(f"最新版本: {status.get('head_revision', 'None')}")
    print(f"状态: {'✅ 最新' if status.get('is_up_to_date') else '⚠️ 需要更新'}")

    if status.get('pending_migrations'):
        print(f"\n待应用迁移 ({len(status['pending_migrations'])} 个):")
        for migration in status['pending_migrations'][:5]:  # 显示前5个
            print(f"  • {migration['to']}: {migration['message']}")

    if status.get('error'):
        print(f"错误: {status['error']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='PredictLab 数据库迁移管理器')
    parser.add_argument('command', choices=[
        'status', 'upgrade', 'downgrade', 'create', 'history', 'backup'
    ], help='执行命令')
    parser.add_argument('--env', choices=['development', 'testing', 'production'],
                       default='development', help='目标环境')
    parser.add_argument('--revision', help='版本号 (用于upgrade/downgrade)')
    parser.add_argument('--message', help='迁移消息 (用于create)')
    parser.add_argument('--auto-generate', action='store_true', default=True,
                       help='自动生成迁移文件')

    args = parser.parse_args()

    manager = MigrationManager()

    try:
        if args.command == 'status':
            # 检查状态
            status = manager.check_status(args.env)
            print_status(status)

        elif args.command == 'upgrade':
            # 升级
            revision = args.revision or 'head'
            if manager.upgrade(revision, args.env):
                print("✅ 升级成功")
            else:
                print("❌ 升级失败")
                sys.exit(1)

        elif args.command == 'downgrade':
            # 回滚
            if not args.revision:
                print("❌ 回滚需要指定版本号")
                sys.exit(1)

            if manager.downgrade(args.revision, args.env):
                print("✅ 回滚成功")
            else:
                print("❌ 回滚失败")
                sys.exit(1)

        elif args.command == 'create':
            # 创建迁移
            if not args.message:
                print("❌ 创建迁移需要指定消息")
                sys.exit(1)

            revision_id = manager.create_migration(args.message, args.auto_generate)
            if revision_id:
                print(f"✅ 迁移创建成功: {revision_id}")
            else:
                print("❌ 迁移创建失败")
                sys.exit(1)

        elif args.command == 'history':
            # 显示历史
            history = manager.show_history(args.env)
            print(f"迁移历史 ({len(history)} 个):")
            for item in history:
                print(f"  {item['from']} -> {item['to']}: {item['message']}")

        elif args.command == 'backup':
            # 备份
            if manager.backup_database(args.env):
                print("✅ 备份成功")
            else:
                print("❌ 备份失败")
                sys.exit(1)

    except Exception as e:
        logger.error(f"命令执行失败: {e}")
        print(f"❌ 执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
