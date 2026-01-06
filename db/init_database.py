#!/usr/bin/env python3
"""
PredictLab 数据库初始化脚本
自动创建所有必要的表结构和索引
"""
import asyncio
import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent  # 父目录是项目根目录
sys.path.insert(0, str(project_root))

from config import config
from modules.data_storage.postgres_storage import PostgresStorage
from utils.logger import get_logger

logger = get_logger(__name__)


async def init_database():
    """初始化数据库"""
    logger.info("开始初始化 PredictLab 数据库...")

    # 初始化存储
    storage = PostgresStorage()

    try:
        # 连接数据库
        if not await storage.connect():
            logger.error("无法连接到 PostgreSQL 数据库")
            return False

        logger.info("成功连接到数据库，开始创建表结构...")

        # 执行建表SQL
        schema_file = project_root / "database_schema.sql"

        if not schema_file.exists():
            logger.error(f"找不到建表文件: {schema_file}")
            return False

        # 读取并执行SQL文件
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # 分割SQL语句并执行
        statements = []
        current_statement = []
        in_multiline_comment = False

        for line in sql_content.split('\n'):
            line = line.strip()

            # 跳过空行和注释
            if not line or line.startswith('--'):
                continue

            # 处理多行注释
            if '/*' in line:
                in_multiline_comment = True
            if '*/' in line:
                in_multiline_comment = False
                continue
            if in_multiline_comment:
                continue

            # SQL语句结束
            if line.endswith(';'):
                current_statement.append(line[:-1])  # 去掉分号
                statements.append(' '.join(current_statement))
                current_statement = []
            else:
                current_statement.append(line)

        # 执行SQL语句
        executed_count = 0
        for statement in statements:
            if statement.strip():
                try:
                    # 直接执行SQL
                    with storage.engine.connect() as conn:
                        conn.execute(statement)
                    executed_count += 1
                except Exception as e:
                    # 某些语句可能已经存在，跳过错误
                    if "already exists" not in str(e).lower():
                        logger.warning(f"执行SQL失败 (可能已存在): {statement[:100]}... 错误: {e}")

        logger.info(f"成功执行 {executed_count} 条SQL语句")

        # 验证表创建
        await verify_tables(storage)

        # 初始化基础数据
        await init_base_data(storage)

        logger.info("数据库初始化完成！")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False
    finally:
        await storage.disconnect()


async def verify_tables(storage: PostgresStorage):
    """验证表是否创建成功"""
    logger.info("验证表结构...")

    expected_tables = [
        'raw_market_data',
        'raw_onchain_data',
        'clean_market_data',
        'clean_kline_data',
        'clean_onchain_transactions',
        'feature_technical_indicators',
        'feature_market_stats',
        'feature_onchain_metrics',
        'metadata_data_sources',
        'metadata_symbols',
        'metadata_data_quality'
    ]

    try:
        # 查询所有表
        query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        """
        df = pd.read_sql_query(query, storage.engine)
        existing_tables = set(df['table_name'].tolist())

        created_tables = []
        missing_tables = []

        for table in expected_tables:
            if table in existing_tables:
                created_tables.append(table)
            else:
                missing_tables.append(table)

        logger.info(f"成功创建表: {len(created_tables)} 个")
        for table in created_tables:
            logger.info(f"  ✓ {table}")

        if missing_tables:
            logger.warning(f"缺失表: {len(missing_tables)} 个")
            for table in missing_tables:
                logger.warning(f"  ✗ {table}")

    except Exception as e:
        logger.error(f"表验证失败: {e}")


async def init_base_data(storage: PostgresStorage):
    """初始化基础数据"""
    logger.info("初始化基础数据...")

    try:
        # 插入数据源配置
        data_sources = [
            {
                'source_type': 'predict',
                'source_name': 'Predict Protocol',
                'api_endpoint': 'https://api.predict.io',
                'is_active': True
            },
            {
                'source_type': 'polymarket',
                'source_name': 'Polymarket',
                'api_endpoint': 'https://api.polymarket.com',
                'is_active': True
            },
            {
                'source_type': 'dune',
                'source_name': 'Dune Analytics',
                'api_endpoint': 'https://api.dune.com',
                'is_active': True
            },
            {
                'source_type': 'onchain',
                'source_name': 'OnChain Data',
                'api_endpoint': None,
                'is_active': True
            }
        ]

        for source in data_sources:
            try:
                await storage.insert_data('metadata_data_sources', source)
            except Exception as e:
                # 可能已存在，跳过
                pass

        # 插入基础资产配置
        symbols = [
            {
                'symbol': 'BTC_PRICE',
                'symbol_name': 'Bitcoin Price',
                'source_type': 'predict',
                'category': 'crypto',
                'is_active': True
            },
            {
                'symbol': 'ETH_PRICE',
                'symbol_name': 'Ethereum Price',
                'source_type': 'predict',
                'category': 'crypto',
                'is_active': True
            },
            {
                'symbol': 'BTC',
                'symbol_name': 'Bitcoin',
                'source_type': 'onchain',
                'contract_address': None,
                'network': 'ethereum',
                'category': 'crypto',
                'is_active': True
            },
            {
                'symbol': 'ETH',
                'symbol_name': 'Ethereum',
                'source_type': 'onchain',
                'contract_address': None,
                'network': 'ethereum',
                'category': 'crypto',
                'is_active': True
            }
        ]

        for symbol in symbols:
            try:
                await storage.insert_data('metadata_symbols', symbol)
            except Exception as e:
                # 可能已存在，跳过
                pass

        logger.info("基础数据初始化完成")

    except Exception as e:
        logger.error(f"基础数据初始化失败: {e}")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PredictLab 数据库初始化工具')
    parser.add_argument('--force', action='store_true', help='强制重新创建表结构')
    parser.add_argument('--verify-only', action='store_true', help='仅验证表结构，不创建')

    args = parser.parse_args()

    if args.verify_only:
        # 仅验证模式
        storage = PostgresStorage()
        if await storage.connect():
            await verify_tables(storage)
            await storage.disconnect()
        else:
            logger.error("无法连接数据库")
            return 1
    else:
        # 完整初始化
        if not await init_database():
            logger.error("数据库初始化失败")
            return 1

    logger.info("操作完成")
    return 0


if __name__ == "__main__":
    import pandas as pd
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
