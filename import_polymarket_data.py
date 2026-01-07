#!/usr/bin/env python3
"""
Polymarket数据导入脚本
将JSON数据导入到PostgreSQL数据库中
"""

import json
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import os
from pathlib import Path

class PolymarketDataImporter:
    def __init__(self, db_config=None):
        """初始化数据库连接"""
        if db_config:
            self.db_config = db_config
        else:
            # 尝试自动检测配置
            self.db_config = self.detect_db_config()

    def detect_db_config(self):
        """自动检测数据库配置"""
        import os

        # 首先尝试从环境变量读取
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'polymarket'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD')
        }

        # 如果环境变量没有设置，尝试自动检测
        if not config['user']:
            current_user = os.getenv('USER') or os.getenv('USERNAME')

            # 优先使用postgres用户（PostgreSQL标准超级用户）
            # 其次尝试系统用户
            possible_users = ['postgres', current_user]

            for user in possible_users:
                test_config = config.copy()
                test_config['user'] = user
                test_config['password'] = ''  # PostgreSQL通常默认不需要密码

                if self.test_connection(test_config):
                    config['user'] = user
                    config['password'] = ''
                    print(f"✅ 自动检测到数据库用户: {user}")
                    break
            else:
                # 如果自动检测都失败了，使用postgres作为默认值
                # 这是最常见的PostgreSQL配置
                config['user'] = 'postgres'
                config['password'] = ''
                print("ℹ️  使用默认数据库用户: postgres")

        return config

    def test_connection(self, config):
        """测试数据库连接"""
        try:
            # 使用默认数据库测试连接
            test_config = config.copy()
            test_config['database'] = 'postgres'

            conn = psycopg2.connect(**test_config)
            conn.close()
            return True
        except:
            return False
        self.conn = None

    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = False
            print("✅ 数据库连接成功")
            print(f"   用户: {self.db_config['user']}")
            print(f"   数据库: {self.db_config['database']}")
        except psycopg2.OperationalError as e:
            print(f"❌ 数据库连接失败: {e}")
            print("\\n💡 解决方案:")
            if "role" in str(e).lower() and "does not exist" in str(e).lower():
                print("   1. 检查用户名是否正确 (默认应为 'postgres' 或你的系统用户名)")
                print("   2. 运行: python3 check_postgres_connection.py")
            elif "authentication failed" in str(e).lower():
                print("   1. 检查密码是否正确")
                print("   2. 可能需要设置密码: ALTER USER your_username PASSWORD 'your_password';")
            elif "connection refused" in str(e).lower():
                print("   1. 确保PostgreSQL服务正在运行")
                print("   2. macOS: brew services start postgresql")
                print("   3. Linux: sudo systemctl start postgresql")
            elif "database" in str(e).lower() and "does not exist" in str(e).lower():
                print("   1. 创建数据库: createdb polymarket")
                print("   2. 或者连接到默认数据库 'postgres' 进行测试")
            else:
                print("   1. 运行诊断脚本: python3 check_postgres_connection.py")

            print(f"\\n🔧 当前配置: {self.db_config}")
            raise
        except Exception as e:
            print(f"❌ 未知数据库错误: {e}")
            raise

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            print("🔌 数据库连接已关闭")

    def create_tables(self):
        """创建数据表"""
        schema_file = Path(__file__).parent / 'polymarket_db_schema.sql'
        if not schema_file.exists():
            print(f"❌ 找不到表结构文件: {schema_file}")
            return False

        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            with self.conn.cursor() as cursor:
                cursor.execute(schema_sql)
                self.conn.commit()
                print("✅ 数据表创建成功")
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 表创建失败: {e}")
            return False

    def load_json_file(self, file_path):
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📄 成功加载文件: {file_path}")
                return data
        except Exception as e:
            print(f"❌ 加载文件失败 {file_path}: {e}")
            return None

    def parse_timestamp(self, timestamp_str):
        """解析时间戳"""
        if not timestamp_str:
            return None

        # 处理不同的时间格式
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S%z',
            '%Y-%m-%d'
        ]

        for fmt in formats:
            try:
                if fmt.endswith('%z'):
                    # 处理时区信息
                    dt = datetime.strptime(timestamp_str, fmt)
                else:
                    dt = datetime.strptime(timestamp_str.replace('Z', ''), fmt)
                return dt
            except ValueError:
                continue
        return None

    def insert_market(self, market_data, category):
        """插入市场数据"""
        try:
            with self.conn.cursor() as cursor:
                # 准备市场数据
                market_sql = """
                INSERT INTO markets (
                    id, question, condition_id, slug, description, resolution_source,
                    created_at, updated_at, start_date, end_date, closed_time,
                    active, closed, archived, restricted, featured, new,
                    volume, volume_24hr, volume_1wk, volume_1mo, volume_1yr, liquidity,
                    enable_order_book, accepting_orders, neg_risk, neg_risk_market_id,
                    uma_bond, uma_reward, uma_end_date, uma_resolution_status,
                    image, icon, submitted_by, category, data_source, sport_type
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (id) DO UPDATE SET
                    question = EXCLUDED.question,
                    updated_at = EXCLUDED.updated_at,
                    volume = EXCLUDED.volume,
                    liquidity = EXCLUDED.liquidity,
                    updated_at_db = NOW()
                """

                market_values = (
                    market_data.get('id'),
                    market_data.get('question'),
                    market_data.get('condition_id') or market_data.get('conditionId'),
                    market_data.get('slug'),
                    market_data.get('description'),
                    market_data.get('resolutionSource'),
                    self.parse_timestamp(market_data.get('createdAt')),
                    self.parse_timestamp(market_data.get('updatedAt')),
                    self.parse_timestamp(market_data.get('startDate') or market_data.get('start_date')),
                    self.parse_timestamp(market_data.get('endDate') or market_data.get('end_date')),
                    self.parse_timestamp(market_data.get('closedTime') or market_data.get('closed_time')),
                    market_data.get('active', True),
                    market_data.get('closed', False),
                    market_data.get('archived', False),
                    market_data.get('restricted', False),
                    market_data.get('featured', False),
                    market_data.get('new', True),
                    market_data.get('volumeNum') or market_data.get('volume'),
                    market_data.get('volume24hr') or market_data.get('volume_24hr'),
                    market_data.get('volume1wk') or market_data.get('volume_1wk'),
                    market_data.get('volume1mo') or market_data.get('volume_1mo'),
                    market_data.get('volume1yr') or market_data.get('volume_1yr'),
                    market_data.get('liquidityNum') or market_data.get('liquidity'),
                    market_data.get('enableOrderBook') or market_data.get('enable_order_book'),
                    market_data.get('acceptingOrders') or market_data.get('accepting_orders'),
                    market_data.get('negRisk') or market_data.get('neg_risk'),
                    market_data.get('negRiskMarketID') or market_data.get('neg_risk_market_id'),
                    market_data.get('umaBond') or market_data.get('uma_bond'),
                    market_data.get('umaReward') or market_data.get('uma_reward'),
                    self.parse_timestamp(market_data.get('umaEndDate') or market_data.get('uma_end_date')),
                    market_data.get('umaResolutionStatus') or market_data.get('uma_resolution_status'),
                    market_data.get('image'),
                    market_data.get('icon'),
                    market_data.get('submitted_by'),
                    category,
                    market_data.get('data_source'),
                    market_data.get('sport_type')
                )

                cursor.execute(market_sql, market_values)

                market_id = market_data.get('id')

                # 插入结果选项
                self.insert_market_outcomes(cursor, market_id, market_data)

                # 插入事件
                self.insert_market_events(cursor, market_id, market_data)

                # 插入合约地址
                self.insert_contract_addresses(cursor, market_id, market_data)

                # 插入代币ID
                self.insert_clob_token_ids(cursor, market_id, market_data)

                # 插入奖励
                self.insert_market_rewards(cursor, market_id, market_data)

                self.conn.commit()
                print(f"✅ 市场 {market_id} 数据插入成功")

        except Exception as e:
            self.conn.rollback()
            print(f"❌ 插入市场数据失败: {e}")
            raise

    def insert_market_outcomes(self, cursor, market_id, market_data):
        """插入市场结果选项"""
        outcomes = market_data.get('outcomes', '[]')
        outcome_prices = market_data.get('outcomePrices', '[]')

        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        if isinstance(outcome_prices, str):
            outcome_prices = json.loads(outcome_prices)

        if outcomes:
            outcome_data = []
            for i, outcome in enumerate(outcomes):
                price = outcome_prices[i] if i < len(outcome_prices) else None
                outcome_data.append((market_id, outcome, price, i))

            execute_values(cursor,
                "INSERT INTO market_outcomes (market_id, outcome_text, outcome_price, outcome_index) VALUES %s",
                outcome_data)

    def insert_market_events(self, cursor, market_id, market_data):
        """插入市场事件"""
        events = market_data.get('events', [])
        if events:
            event_data = []
            for event in events:
                event_data.append((
                    market_id,
                    event.get('id'),
                    event.get('ticker'),
                    event.get('slug'),
                    event.get('title'),
                    event.get('description'),
                    self.parse_timestamp(event.get('startDate')),
                    self.parse_timestamp(event.get('endDate')),
                    self.parse_timestamp(event.get('createdAt')),
                    event.get('active', True),
                    event.get('closed', False),
                    event.get('archived', False),
                    event.get('volume'),
                    event.get('liquidity'),
                    event.get('commentCount') or event.get('comment_count')
                ))

            execute_values(cursor,
                """INSERT INTO market_events
                   (market_id, event_id, ticker, event_slug, title, event_description,
                    event_start_date, event_end_date, event_created_at, active, closed, archived,
                    volume, liquidity, comment_count) VALUES %s""",
                event_data)

    def insert_contract_addresses(self, cursor, market_id, market_data):
        """插入合约地址"""
        addresses = market_data.get('contract_addresses', {})
        if addresses:
            cursor.execute(
                """INSERT INTO contract_addresses
                   (market_id, conditional_tokens, clob_exchange, fee_module)
                   VALUES (%s, %s, %s, %s)""",
                (market_id,
                 addresses.get('conditional_tokens'),
                 addresses.get('clob_exchange'),
                 addresses.get('fee_module'))
            )

    def insert_clob_token_ids(self, cursor, market_id, market_data):
        """插入CLOB代币ID"""
        token_ids = market_data.get('clob_token_ids', [])
        outcomes = market_data.get('outcomes', '[]')

        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)

        if token_ids:
            token_data = []
            for i, token_id in enumerate(token_ids):
                outcome_text = outcomes[i] if i < len(outcomes) else f"Option {i+1}"
                token_data.append((market_id, token_id, i, outcome_text))

            execute_values(cursor,
                "INSERT INTO clob_token_ids (market_id, token_id, token_index, outcome_text) VALUES %s",
                token_data)

    def insert_market_rewards(self, cursor, market_id, market_data):
        """插入市场奖励"""
        rewards = market_data.get('clobRewards') or market_data.get('clob_rewards', [])
        if rewards:
            reward_data = []
            for reward in rewards:
                reward_data.append((
                    market_id,
                    reward.get('id'),
                    reward.get('assetAddress') or reward.get('asset_address'),
                    reward.get('rewardsAmount') or reward.get('rewards_amount'),
                    reward.get('rewardsDailyRate') or reward.get('rewards_daily_rate'),
                    reward.get('startDate') or reward.get('start_date'),
                    reward.get('endDate') or reward.get('end_date')
                ))

            execute_values(cursor,
                """INSERT INTO market_rewards
                   (market_id, reward_id, asset_address, rewards_amount,
                    rewards_daily_rate, start_date, end_date) VALUES %s""",
                reward_data)

    def insert_data_file_record(self, filename, file_path, category, total_markets):
        """插入数据文件记录"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO data_files
                       (filename, file_path, category, total_markets, status)
                       VALUES (%s, %s, %s, %s, 'completed')
                       ON CONFLICT (filename) DO UPDATE SET
                           processed_at = NOW(),
                           status = 'completed'""",
                    (filename, file_path, category, total_markets)
                )
                self.conn.commit()
        except Exception as e:
            print(f"❌ 插入文件记录失败: {e}")

    def store_raw_json_data(self, file_path, data, category):
        """存储原始JSON数据"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 从文件名提取时间戳
            file_timestamp = None
            if '_2026' in filename:
                # 提取时间戳部分
                parts = filename.split('_2026')
                if len(parts) > 1:
                    timestamp_str = '2026' + parts[1].split('.')[0]
                    try:
                        file_timestamp = datetime.strptime(timestamp_str, '%Y%m%d%H%M%S')
                    except:
                        pass

            # 准备数据
            metadata_json = json.dumps(data.get('metadata', {}), ensure_ascii=False)
            markets_json = json.dumps(data.get('markets', []), ensure_ascii=False)

            total_markets = data.get('metadata', {}).get('total_markets', 0)

            with self.conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO raw_json_data
                       (filename, category, file_timestamp, total_markets,
                        metadata_json, markets_json, file_size_bytes)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (filename, category) DO UPDATE SET
                           file_timestamp = EXCLUDED.file_timestamp,
                           total_markets = EXCLUDED.total_markets,
                           metadata_json = EXCLUDED.metadata_json,
                           markets_json = EXCLUDED.markets_json,
                           file_size_bytes = EXCLUDED.file_size_bytes,
                           last_updated = NOW()""",
                    (filename, category, file_timestamp, total_markets,
                     metadata_json, markets_json, file_size)
                )
                self.conn.commit()
                print(f"✅ 原始JSON数据存储成功: {filename} ({file_size} bytes)")

        except Exception as e:
            self.conn.rollback()
            print(f"❌ 存储原始JSON数据失败: {e}")

    def import_file(self, file_path, category):
        """导入单个文件"""
        print(f"\\n🔄 开始导入文件: {file_path}")

        # 加载数据
        data = self.load_json_file(file_path)
        if not data:
            return False

        filename = os.path.basename(file_path)
        total_markets = data.get('metadata', {}).get('total_markets', 0)

        try:
            # 1. 存储原始JSON数据
            self.store_raw_json_data(file_path, data, category)

            # 2. 导入结构化数据
            markets_imported = 0
            for market_data in data.get('markets', []):
                self.insert_market(market_data, category)
                markets_imported += 1

            # 3. 记录文件信息
            self.insert_data_file_record(filename, file_path, category, total_markets)

            print(f"✅ 文件 {filename} 导入完成:")
            print(f"   📄 原始JSON数据: 已存储")
            print(f"   🏛️ 结构化数据: {markets_imported} 个市场")
            print(f"   📊 总市场数: {total_markets}")
            return True

        except Exception as e:
            print(f"❌ 文件导入失败: {e}")
            return False

    def import_all_files(self):
        """导入所有数据文件"""
        data_dir = Path('data')
        if not data_dir.exists():
            print(f"❌ 数据目录不存在: {data_dir}")
            return

        # 文件映射
        file_mapping = {
            'polymarket_markets_Sports_*.json': 'Sports',
            'polymarket_markets_Crypto_*.json': 'Crypto',
            'polymarket_markets_Politics_*.json': 'Politics'
        }

        imported_files = 0

        for pattern, category in file_mapping.items():
            # 查找匹配的文件
            for file_path in data_dir.glob(pattern):
                if self.import_file(str(file_path), category):
                    imported_files += 1

        print(f"\\n🎉 导入完成，共处理 {imported_files} 个文件")

def main():
    """主函数"""
    importer = PolymarketDataImporter()

    try:
        # 连接数据库
        importer.connect()

        # 创建表结构
        if not importer.create_tables():
            return

        # 导入数据
        importer.import_all_files()

    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
    finally:
        importer.disconnect()

if __name__ == "__main__":
    main()
