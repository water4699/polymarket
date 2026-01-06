"""
Alembic环境配置文件
用于PredictLab数据库迁移管理
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入配置和模型
from config import config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config_alembic = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config_alembic.config_file_name is not None:
    fileConfig(config_alembic.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """获取数据库URL，支持多环境"""
    # 从环境变量获取环境类型
    env = os.getenv('PREDICTLAB_ENV', 'development')

    if env == 'production':
        # 生产环境
        url = os.getenv('DATABASE_URL')
        if not url:
            raise ValueError("生产环境必须设置 DATABASE_URL 环境变量")
        return url
    elif env == 'testing':
        # 测试环境
        return os.getenv('TEST_DATABASE_URL', 'postgresql://test:test@localhost:5432/predictlab_test')
    else:
        # 开发环境
        return config.postgres_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config_alembic.get_section(config_alembic.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
