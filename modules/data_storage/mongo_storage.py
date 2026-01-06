"""
MongoDB 数据存储
用于存储非结构化数据 (Raw 数据和特征数据)
"""
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import pandas as pd
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from config import config
from .base import BaseStorage, StorageError


class MongoStorage(BaseStorage):
    """MongoDB 存储实现"""

    def __init__(self, database: str = None):
        super().__init__(
            name="MongoDB",
            config={
                "url": config.mongodb_url,
                "database": database or config.database.MONGODB_DB
            }
        )
        self.client = None
        self.db = None

    async def connect(self) -> bool:
        """连接到 MongoDB"""
        try:
            self.client = MongoClient(self.config["url"])
            # 测试连接
            self.client.admin.command('ping')
            self.db = self.client[self.config["database"]]

            self.is_connected = True
            self.logger.info("成功连接到 MongoDB")
            return True
        except ConnectionFailure as e:
            self.logger.error(f"连接 MongoDB 失败: {e}")
            return False

    async def disconnect(self):
        """断开连接"""
        if self.client:
            self.client.close()
            self.is_connected = False
            self.logger.info("已断开 MongoDB 连接")

    async def insert_data(
        self,
        collection_name: str,
        data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> bool:
        """插入数据"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]

            if isinstance(data, pd.DataFrame):
                # DataFrame 转换为字典列表
                records = data.to_dict('records')
                # 添加时间戳
                for record in records:
                    if 'created_at' not in record:
                        record['created_at'] = datetime.utcnow()
                result = collection.insert_many(records)
                inserted_count = len(result.inserted_ids)

            elif isinstance(data, dict):
                # 单个文档
                if 'created_at' not in data:
                    data['created_at'] = datetime.utcnow()
                result = collection.insert_one(data)
                inserted_count = 1 if result.acknowledged else 0

            elif isinstance(data, list):
                # 多个文档
                for record in data:
                    if 'created_at' not in record:
                        record['created_at'] = datetime.utcnow()
                result = collection.insert_many(data)
                inserted_count = len(result.inserted_ids)

            self.logger.info(f"成功插入 {inserted_count} 条文档到集合 {collection_name}")
            return True

        except Exception as e:
            self.logger.error(f"插入数据失败: {e}")
            return False

    async def query_data(
        self,
        collection_name: str,
        filters: Dict[str, Any] = None,
        limit: int = None,
        sort_by: str = None,
        ascending: bool = True
    ) -> pd.DataFrame:
        """查询数据"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]

            # 构建查询
            query = {}
            if filters:
                query.update(filters)

            # 构建排序
            sort_spec = None
            if sort_by:
                sort_order = ASCENDING if ascending else DESCENDING
                sort_spec = [(sort_by, sort_order)]

            # 执行查询
            cursor = collection.find(query, sort=sort_spec)
            if limit:
                cursor = cursor.limit(limit)

            # 转换为 DataFrame
            documents = list(cursor)
            df = pd.DataFrame(documents)

            # 移除 MongoDB 的 _id 列（如果存在）
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)

            self.logger.info(f"成功查询集合 {collection_name}, 返回 {len(df)} 行数据")
            return df

        except Exception as e:
            self.logger.error(f"查询数据失败: {e}")
            return pd.DataFrame()

    async def update_data(
        self,
        collection_name: str,
        filters: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """更新数据"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]

            # 添加更新时间戳
            update_data['updated_at'] = datetime.utcnow()

            result = collection.update_many(
                filters,
                {"$set": update_data}
            )

            updated_count = result.modified_count
            self.logger.info(f"成功更新 {updated_count} 条文档")
            return updated_count

        except Exception as e:
            self.logger.error(f"更新数据失败: {e}")
            return 0

    async def delete_data(
        self,
        collection_name: str,
        filters: Dict[str, Any]
    ) -> int:
        """删除数据"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]

            result = collection.delete_many(filters)

            deleted_count = result.deleted_count
            self.logger.info(f"成功删除 {deleted_count} 条文档")
            return deleted_count

        except Exception as e:
            self.logger.error(f"删除数据失败: {e}")
            return 0

    async def create_index(
        self,
        collection_name: str,
        keys: List[str],
        unique: bool = False
    ):
        """创建索引"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]
            index_spec = [(key, ASCENDING) for key in keys]
            collection.create_index(index_spec, unique=unique)
            self.logger.info(f"成功创建索引: {keys}")
        except Exception as e:
            self.logger.error(f"创建索引失败: {e}")

    async def aggregate_data(
        self,
        collection_name: str,
        pipeline: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """聚合查询"""
        if not self.is_connected or not self.db:
            raise StorageError("未连接到 MongoDB")

        try:
            collection = self.db[collection_name]
            result = list(collection.aggregate(pipeline))
            self.logger.info(f"聚合查询完成，返回 {len(result)} 条结果")
            return result
        except Exception as e:
            self.logger.error(f"聚合查询失败: {e}")
            return []
