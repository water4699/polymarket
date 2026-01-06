"""
PostgreSQL 数据存储
支持三层数据架构：Raw Layer、Clean Layer、Feature Layer
"""
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import select, insert, update, delete
from sqlalchemy.orm import sessionmaker
from config import config
from .base import BaseStorage, StorageError


class PostgresStorage(BaseStorage):
    """PostgreSQL 存储实现"""

    def __init__(self, schema: str = "public"):
        super().__init__(
            name="PostgreSQL",
            config={
                "url": config.postgres_url,
                "schema": schema
            }
        )
        self.engine = None
        self.metadata = MetaData(schema=schema)
        self.SessionLocal = None

    async def connect(self) -> bool:
        """连接到 PostgreSQL"""
        try:
            self.engine = create_engine(self.config["url"], echo=False)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(select(1))

            self.is_connected = True
            self.logger.info("成功连接到 PostgreSQL")
            return True
        except Exception as e:
            self.logger.error(f"连接 PostgreSQL 失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.engine:
            self.engine.dispose()
            self.is_connected = False
            self.logger.info("已断开 PostgreSQL 连接")

    async def insert_data(
        self,
        table_name: str,
        data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """插入数据"""
        if not self.is_connected or not self.engine:
            raise StorageError("未连接到 PostgreSQL")

        try:
            with self.SessionLocal() as session:
                if isinstance(data, pd.DataFrame):
                    # DataFrame 批量插入
                    data.to_sql(
                        table_name,
                        self.engine,
                        schema=self.config["schema"],
                        if_exists="append",
                        index=False
                    )
                elif isinstance(data, dict):
                    # 单个记录插入
                    table = self._get_or_create_table(table_name, data)
                    stmt = insert(table).values(**data)
                    session.execute(stmt)
                    session.commit()
                elif isinstance(data, list):
                    # 多个记录插入
                    if data:
                        table = self._get_or_create_table(table_name, data[0])
                        stmt = insert(table).values(data)
                        session.execute(stmt)
                        session.commit()

            self.logger.info(f"成功插入数据到表 {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"插入数据失败: {e}")
            return False

    async def query_data(
        self,
        table_name: str,
        filters: Dict[str, Any] = None,
        limit: int = None,
        sort_by: str = None,
        ascending: bool = True
    ) -> pd.DataFrame:
        """查询数据"""
        if not self.is_connected or not self.engine:
            raise StorageError("未连接到 PostgreSQL")

        try:
            query = f"SELECT * FROM {self.config['schema']}.{table_name}"

            # 添加过滤条件
            where_clauses = []
            params = {}
            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"{key} = :{key}")
                    params[key] = value

                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

            # 添加排序
            if sort_by:
                order = "ASC" if ascending else "DESC"
                query += f" ORDER BY {sort_by} {order}"

            # 添加限制
            if limit:
                query += f" LIMIT {limit}"

            # 执行查询
            df = pd.read_sql_query(query, self.engine, params=params)
            self.logger.info(f"成功查询表 {table_name}, 返回 {len(df)} 行数据")
            return df

        except Exception as e:
            self.logger.error(f"查询数据失败: {e}")
            return pd.DataFrame()

    async def update_data(
        self,
        table_name: str,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """更新数据"""
        if not self.is_connected or not self.engine:
            raise StorageError("未连接到 PostgreSQL")

        try:
            with self.SessionLocal() as session:
                table = Table(table_name, self.metadata, autoload_with=self.engine)

                # 构建更新语句
                stmt = update(table).where(
                    *[getattr(table.c, k) == v for k, v in filters.items()]
                ).values(**update_data)

                result = session.execute(stmt)
                session.commit()

                updated_count = result.rowcount
                self.logger.info(f"成功更新 {updated_count} 行数据")
                return updated_count

        except Exception as e:
            self.logger.error(f"更新数据失败: {e}")
            return 0

    async def delete_data(
        self,
        table_name: str,
        filters: Dict[str, Any]
    ) -> int:
        """删除数据"""
        if not self.is_connected or not self.engine:
            raise StorageError("未连接到 PostgreSQL")

        try:
            with self.SessionLocal() as session:
                table = Table(table_name, self.metadata, autoload_with=self.engine)

                # 构建删除语句
                stmt = delete(table).where(
                    *[getattr(table.c, k) == v for k, v in filters.items()]
                )

                result = session.execute(stmt)
                session.commit()

                deleted_count = result.rowcount
                self.logger.info(f"成功删除 {deleted_count} 行数据")
                return deleted_count

        except Exception as e:
            self.logger.error(f"删除数据失败: {e}")
            return 0

    # ===========================================
    # 三层数据架构专用方法
    # ===========================================

    async def insert_raw_market_data(self, source_type: str, symbol: str, data_timestamp, raw_data: dict, data_hash: str = None) -> bool:
        """插入原始市场数据 (Raw Layer)"""
        if data_hash is None:
            import hashlib
            data_hash = hashlib.md5(str(raw_data).encode()).hexdigest()

        data = {
            'source_type': source_type,
            'symbol': symbol,
            'data_timestamp': data_timestamp,
            'raw_data': raw_data,
            'data_hash': data_hash
        }
        return await self.insert_data('raw_market_data', data)

    async def insert_clean_market_data(self, source_type: str, symbol: str, data_timestamp, market_data: dict) -> bool:
        """插入清洗后的市场数据 (Clean Layer)"""
        data = {
            'source_type': source_type,
            'symbol': symbol,
            'data_timestamp': data_timestamp,
            **market_data
        }
        return await self.insert_data('clean_market_data', data)

    async def insert_kline_data(self, source_type: str, symbol: str, interval_type: str,
                              interval_start, interval_end, kline_data: dict) -> bool:
        """插入K线数据 (Clean Layer)"""
        data = {
            'source_type': source_type,
            'symbol': symbol,
            'interval_type': interval_type,
            'interval_start': interval_start,
            'interval_end': interval_end,
            **kline_data
        }
        return await self.insert_data('clean_kline_data', data)

    async def insert_technical_indicators(self, symbol: str, interval_type: str,
                                        data_timestamp, indicators: dict) -> bool:
        """插入技术指标数据 (Feature Layer)"""
        data = {
            'symbol': symbol,
            'interval_type': interval_type,
            'data_timestamp': data_timestamp,
            **indicators
        }
        return await self.insert_data('feature_technical_indicators', data)

    async def insert_onchain_transaction(self, network: str, contract_address: str,
                                       transaction_hash: str, block_number: int,
                                       transaction_data: dict) -> bool:
        """插入链上交易数据 (Clean Layer)"""
        data = {
            'network': network,
            'contract_address': contract_address,
            'transaction_hash': transaction_hash,
            'block_number': block_number,
            **transaction_data
        }
        return await self.insert_data('clean_onchain_transactions', data)

    async def get_klines(self, symbol: str, interval_type: str, start_time, end_time,
                        limit: int = None) -> pd.DataFrame:
        """获取K线数据"""
        filters = {
            'symbol': symbol,
            'interval_type': interval_type,
            'interval_start >=': start_time,
            'interval_start <': end_time
        }
        return await self.query_data('clean_kline_data', filters, limit=limit,
                                   sort_by='interval_start', ascending=True)

    async def get_technical_indicators(self, symbol: str, interval_type: str,
                                     start_time, end_time, indicator_list: list = None) -> pd.DataFrame:
        """获取技术指标数据"""
        filters = {
            'symbol': symbol,
            'interval_type': interval_type,
            'data_timestamp >=': start_time,
            'data_timestamp <': end_time
        }

        columns = ['data_timestamp'] + (indicator_list if indicator_list else ['*'])
        df = await self.query_data('feature_technical_indicators', filters,
                                 sort_by='data_timestamp', ascending=True)

        if indicator_list:
            available_cols = [col for col in indicator_list if col in df.columns]
            return df[['data_timestamp'] + available_cols]

        return df

    async def get_market_stats(self, symbol: str, stat_period: str, start_date, end_date) -> pd.DataFrame:
        """获取市场统计数据"""
        filters = {
            'symbol': symbol,
            'stat_period': stat_period,
            'stat_date >=': start_date,
            'stat_date <=': end_date
        }
        return await self.query_data('feature_market_stats', filters,
                                   sort_by='stat_date', ascending=True)

    async def get_latest_price(self, symbol: str) -> dict:
        """获取最新价格"""
        df = await self.query_data('clean_market_data',
                                 {'symbol': symbol},
                                 limit=1,
                                 sort_by='data_timestamp',
                                 ascending=False)
        if not df.empty:
            row = df.iloc[0]
            return {
                'symbol': symbol,
                'price': row.get('price'),
                'timestamp': row.get('data_timestamp'),
                'volume': row.get('volume')
            }
        return {}

    async def update_data_quality(self, table_name: str, record_ids: list, quality_score: float):
        """批量更新数据质量评分"""
        if not self.is_connected or not self.engine:
            raise StorageError("未连接到 PostgreSQL")

        try:
            with self.SessionLocal() as session:
                table = Table(table_name, self.metadata, autoload_with=self.engine)
                stmt = update(table).where(
                    table.c.id.in_(record_ids)
                ).values(data_quality_score=quality_score, updated_at=datetime.now())

                result = session.execute(stmt)
                session.commit()
                return result.rowcount

        except Exception as e:
            self.logger.error(f"更新数据质量失败: {e}")
            return 0

    async def get_data_quality_stats(self, table_name: str, days: int = 7) -> dict:
        """获取数据质量统计"""
        query = f"""
        SELECT
            COUNT(*) as total_records,
            AVG(data_quality_score) as avg_quality,
            MIN(data_quality_score) as min_quality,
            MAX(data_quality_score) as max_quality,
            COUNT(CASE WHEN data_quality_score < 0.8 THEN 1 END) as low_quality_count
        FROM {table_name}
        WHERE created_at >= NOW() - INTERVAL '{days} days'
        """

        try:
            df = pd.read_sql_query(query, self.engine)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception as e:
            self.logger.error(f"获取数据质量统计失败: {e}")

        return {}

    def _get_or_create_table(self, table_name: str, sample_data: Dict[str, Any]) -> Table:
        """获取或创建表"""
        try:
            # 尝试获取现有表
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            return table
        except Exception:
            # 表不存在，创建新表
            columns = []
            for key, value in sample_data.items():
                if isinstance(value, int):
                    columns.append(Column(key, Integer))
                elif isinstance(value, float):
                    columns.append(Column(key, Float))
                elif isinstance(value, bool):
                    columns.append(Column(key, Boolean))
                elif isinstance(value, datetime):
                    columns.append(Column(key, DateTime))
                else:
                    # 检查是否是长文本
                    if len(str(value)) > 255:
                        columns.append(Column(key, Text))
                    else:
                        columns.append(Column(key, String(255)))

            # 添加时间戳列
            if 'created_at' not in sample_data:
                columns.append(Column('created_at', DateTime, default=datetime.utcnow))

            table = Table(table_name, self.metadata, *columns)
            self.metadata.create_all(self.engine)
            return table
