"""
多环境配置管理
为不同环境提供独立的Alembic配置
"""
import os
from typing import Dict, Any
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


class EnvironmentConfig:
    """环境配置管理器"""

    @staticmethod
    def get_config(env: str) -> Dict[str, Any]:
        """获取指定环境的配置"""
        configs = {
            'development': {
                'database_url': 'postgresql://predictlab:predictlab@localhost:5432/predictlab_dev',
                'log_level': 'INFO',
                'auto_generate': True,
                'backup_before_migration': False,
                'description': '开发环境 - 用于日常开发和测试'
            },
            'testing': {
                'database_url': 'postgresql://test:test@localhost:5432/predictlab_test',
                'log_level': 'DEBUG',
                'auto_generate': True,
                'backup_before_migration': False,
                'description': '测试环境 - 用于自动化测试'
            },
            'staging': {
                'database_url': os.getenv('STAGING_DATABASE_URL', 'postgresql://predictlab:predictlab@staging-db:5432/predictlab_staging'),
                'log_level': 'WARNING',
                'auto_generate': False,  # 暂存环境不自动生成，使用预定义迁移
                'backup_before_migration': True,
                'description': '暂存环境 - 用于集成测试和预发布验证'
            },
            'production': {
                'database_url': os.getenv('DATABASE_URL'),
                'log_level': 'ERROR',
                'auto_generate': False,  # 生产环境绝对不自动生成迁移
                'backup_before_migration': True,
                'maintenance_mode': True,
                'description': '生产环境 - 线上正式环境'
            }
        }

        if env not in configs:
            raise ValueError(f"未知环境: {env}. 支持的环境: {list(configs.keys())}")

        config = configs[env].copy()

        # 生产环境必须设置 DATABASE_URL
        if env == 'production' and not config['database_url']:
            raise ValueError("生产环境必须设置 DATABASE_URL 环境变量")

        return config

    @staticmethod
    def get_current_env() -> str:
        """获取当前环境"""
        return os.getenv('PREDICTLAB_ENV', 'development')

    @staticmethod
    def validate_env_config(env: str) -> bool:
        """验证环境配置"""
        try:
            config = EnvironmentConfig.get_config(env)
            # 这里可以添加更多验证逻辑
            return True
        except Exception:
            return False

    @staticmethod
    def get_backup_config(env: str) -> Dict[str, Any]:
        """获取备份配置"""
        base_config = {
            'backup_dir': PROJECT_ROOT / 'backups',
            'retention_days': 30,
            'compress': True,
            'encrypt': False
        }

        # 生产环境特殊配置
        if env == 'production':
            base_config.update({
                'encrypt': True,
                'retention_days': 90,
                'remote_backup': True,
                'remote_config': {
                    'type': 's3',
                    'bucket': os.getenv('BACKUP_BUCKET'),
                    'region': os.getenv('AWS_REGION', 'us-east-1')
                }
            })

        return base_config

    @staticmethod
    def get_migration_safety_rules(env: str) -> Dict[str, Any]:
        """获取迁移安全规则"""
        rules = {
            'development': {
                'allow_destructive_changes': True,
                'require_backup': False,
                'allow_data_loss': True,
                'auto_approve': True
            },
            'testing': {
                'allow_destructive_changes': True,
                'require_backup': False,
                'allow_data_loss': True,
                'auto_approve': True
            },
            'staging': {
                'allow_destructive_changes': False,
                'require_backup': True,
                'allow_data_loss': False,
                'auto_approve': False,
                'require_review': True
            },
            'production': {
                'allow_destructive_changes': False,
                'require_backup': True,
                'allow_data_loss': False,
                'auto_approve': False,
                'require_review': True,
                'maintenance_window_required': True,
                'rollback_plan_required': True
            }
        }

        return rules.get(env, rules['development'])


def print_env_info(env: str = None):
    """打印环境信息"""
    if env is None:
        env = EnvironmentConfig.get_current_env()

    print(f"当前环境: {env}")
    print("-" * 50)

    try:
        config = EnvironmentConfig.get_config(env)
        print(f"描述: {config['description']}")
        print(f"数据库: {'已配置' if config.get('database_url') else '未配置'}")
        print(f"日志级别: {config['log_level']}")
        print(f"自动生成迁移: {'是' if config['auto_generate'] else '否'}")
        print(f"迁移前备份: {'是' if config['backup_before_migration'] else '否'}")

        safety_rules = EnvironmentConfig.get_migration_safety_rules(env)
        print(f"\n安全规则:")
        print(f"  允许破坏性变更: {'是' if safety_rules['allow_destructive_changes'] else '否'}")
        print(f"  需要备份: {'是' if safety_rules['require_backup'] else '否'}")
        print(f"  允许数据丢失: {'是' if safety_rules['allow_data_loss'] else '否'}")
        print(f"  需要审核: {'是' if safety_rules.get('require_review', False) else '否'}")

    except Exception as e:
        print(f"配置错误: {e}")


def setup_env_vars(env: str) -> Dict[str, str]:
    """设置环境变量"""
    config = EnvironmentConfig.get_config(env)

    env_vars = os.environ.copy()
    env_vars['PREDICTLAB_ENV'] = env

    if config.get('database_url'):
        if env == 'production':
            env_vars['DATABASE_URL'] = config['database_url']
        else:
            env_vars['TEST_DATABASE_URL'] = config['database_url']

    return env_vars


# 导出便捷函数
def dev():
    """开发环境"""
    print_env_info('development')


def test():
    """测试环境"""
    print_env_info('testing')


def staging():
    """暂存环境"""
    print_env_info('staging')


def prod():
    """生产环境"""
    print_env_info('production')


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        env = sys.argv[1]
        print_env_info(env)
    else:
        print_env_info()
