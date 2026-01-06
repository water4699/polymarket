#!/usr/bin/env python3
"""
PredictLab 数据管理工具
提供数据迁移、清理、重算等功能
"""
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from modules.data_storage.postgres_storage import PostgresStorage
from modules.data_processing.data_cleaner import DataCleaner
from modules.data_processing.kline_generator import KlineGenerator
from modules.validation.data_validator import data_validator, ValidationLevel
from utils.logger import get_logger

logger = get_logger(__name__)


class DataManager:
    """数据管理器"""

    def __init__(self):
        self.storage = PostgresStorage()
        self.data_cleaner = DataCleaner()
        self.kline_generator = KlineGenerator()

    async def connect(self) -> bool:
        """连接数据库"""
        return await self.storage.connect()

    async def disconnect(self):
        """断开连接"""
        await self.storage.disconnect()

    async def migrate_raw_to_clean(self, source_type: str = None, symbol: str = None,
                                 days_back: int = 30, batch_size: int = 1000) -> Dict[str, int]:
        """
        将原始数据迁移到清洗层

        Args:
            source_type: 数据源类型过滤
            symbol: 资产符号过滤
            days_back: 处理最近N天的数��
            batch_size: 批处理大小

        Returns:
            处理统计信息
        """
        logger.info(f"开始数据迁移: source_type={source_type}, symbol={symbol}, days_back={days_back}")

        stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'migrated': 0
        }

        try:
            # 构建查询条件
            conditions = ["is_processed = FALSE"]
            if source_type:
                conditions.append(f"source_type = '{source_type}'")
            if symbol:
                conditions.append(f"symbol = '{symbol}'")

            start_time = datetime.now() - timedelta(days=days_back)
            conditions.append(f"fetch_timestamp >= '{start_time}'")

            where_clause = " AND ".join(conditions)

            # 分批处理
            offset = 0
            while True:
                # 获取一批原始数据
                query = f"""
                SELECT id, source_type, symbol, data_timestamp, raw_data
                FROM raw_market_data
                WHERE {where_clause}
                ORDER BY fetch_timestamp
                LIMIT {batch_size} OFFSET {offset}
                """

                df = pd.read_sql_query(query, self.storage.engine)
                if df.empty:
                    break

                for _, row in df.iterrows():
                    try:
                        # 解析和清洗数据
                        clean_data = self._clean_raw_market_data(row['raw_data'], row['source_type'])

                        if clean_data:
                            # 插入清洗数据
                            success = await self.storage.insert_clean_market_data(
                                row['source_type'], row['symbol'], row['data_timestamp'], clean_data
                            )

                            if success:
                                stats['migrated'] += 1
                            else:
                                stats['errors'] += 1
                        else:
                            stats['skipped'] += 1

                        # 标记为已处理
                        await self._mark_processed(row['id'])

                        stats['processed'] += 1

                    except Exception as e:
                        logger.error(f"处理数据失败 ID={row['id']}: {e}")
                        stats['errors'] += 1

                offset += batch_size
                logger.info(f"已处理 {stats['processed']} 条数据...")

            logger.info(f"数据迁移完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            return stats

    async def generate_klines_batch(self, symbol: str, intervals: List[str] = None,
                                  days_back: int = 30) -> Dict[str, int]:
        """
        批量生成K线数据

        Args:
            symbol: 资产符号
            intervals: K线间隔列表
            days_back: 处理天数

        Returns:
            生成统计
        """
        if intervals is None:
            intervals = ['1m', '5m', '15m', '1h', '1d']

        logger.info(f"开始生成K线: symbol={symbol}, intervals={intervals}")

        stats = {interval: 0 for interval in intervals}
        stats['errors'] = 0

        try:
            # 获取基础数据
            start_time = datetime.now() - timedelta(days=days_back)
            base_data = await self.storage.query_data(
                'clean_market_data',
                {'symbol': symbol, 'data_timestamp >=': start_time},
                sort_by='data_timestamp',
                ascending=True
            )

            if base_data.empty:
                logger.warning(f"没有找到 {symbol} 的基础数据")
                return stats

            # 为每个间隔生成K线
            for interval in intervals:
                try:
                    kline_data = self.kline_generator.generate_klines(
                        base_data, interval,
                        price_col='price',
                        volume_col='volume',
                        timestamp_col='data_timestamp'
                    )

                    if not kline_data.empty:
                        # 批量插入K线数据
                        for _, row in kline_data.iterrows():
                            kline_record = {
                                'open_price': row['open'],
                                'high_price': row['high'],
                                'low_price': row['low'],
                                'close_price': row['close'],
                                'volume': row['volume'],
                                'data_points': len(base_data),  # 简化计算
                                'data_quality_score': 0.95
                            }

                            success = await self.storage.insert_kline_data(
                                'predict', symbol, interval,
                                row['timestamp'], row['timestamp'] + pd.Timedelta(interval),
                                kline_record
                            )

                            if success:
                                stats[interval] += 1

                except Exception as e:
                    logger.error(f"生成 {interval} K线失败: {e}")
                    stats['errors'] += 1

            logger.info(f"K线生成完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"K线生成失败: {e}")
            return stats

    async def recalculate_indicators(self, symbol: str, interval: str = '1h',
                                   days_back: int = 30) -> Dict[str, int]:
        """
        重新计算技术指标

        Args:
            symbol: 资产符号
            interval: 时间间隔
            days_back: 重新计算天数

        Returns:
            计算统计
        """
        logger.info(f"开始重新计算技术指标: {symbol} {interval}")

        stats = {'processed': 0, 'errors': 0}

        try:
            # 获取K线数据
            start_time = datetime.now() - timedelta(days=days_back)
            kline_data = await self.storage.get_klines(symbol, interval, start_time, datetime.now())

            if kline_data.empty:
                logger.warning(f"没有找到 {symbol} {interval} 的K线数据")
                return stats

            # 添加技术指标
            kline_with_indicators = self.kline_generator.add_technical_indicators(kline_data)

            # 更新技术指标表
            for _, row in kline_with_indicators.iterrows():
                try:
                    indicators = {
                        'sma_5': row.get('sma_5'),
                        'sma_10': row.get('sma_10'),
                        'sma_20': row.get('sma_20'),
                        'rsi_14': row.get('rsi'),
                        'macd_line': row.get('macd'),
                        'macd_signal': row.get('macd_signal'),
                        'macd_histogram': row.get('macd_histogram'),
                        'bb_upper': row.get('bb_upper'),
                        'bb_middle': row.get('bb_middle'),
                        'bb_lower': row.get('bb_lower'),
                        'price_change_1d': row.get('price_change_1d', 0),
                        'volatility_7d': row.get('volatility_7d', 0)
                    }

                    # 移除NaN值
                    indicators = {k: v for k, v in indicators.items() if pd.notna(v)}

                    success = await self.storage.insert_technical_indicators(
                        symbol, interval, row['timestamp'], indicators
                    )

                    if success:
                        stats['processed'] += 1
                    else:
                        stats['errors'] += 1

                except Exception as e:
                    logger.error(f"更新技术指标失败: {e}")
                    stats['errors'] += 1

            logger.info(f"技术指标重算完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"技术指标重算失败: {e}")
            return stats

    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        清理过期数据

        Args:
            days_to_keep: 保留天数

        Returns:
            清理统计
        """
        logger.info(f"开始清理过期数据，保留 {days_to_keep} 天")

        stats = {'raw_deleted': 0, 'clean_deleted': 0, 'feature_deleted': 0}

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # 清理原始数据 (只删除已处理的)
            raw_deleted = await self.storage.delete_data(
                'raw_market_data',
                {'is_processed': True, 'data_timestamp <': cutoff_date}
            )
            stats['raw_deleted'] = raw_deleted

            # 清理清洗数据
            clean_deleted = await self.storage.delete_data(
                'clean_market_data',
                {'data_timestamp <': cutoff_date}
            )
            stats['clean_deleted'] = clean_deleted

            # 清理特征数据
            feature_deleted = await self.storage.delete_data(
                'feature_technical_indicators',
                {'data_timestamp <': cutoff_date}
            )
            stats['feature_deleted'] = feature_deleted

            logger.info(f"数据清理完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"数据清理失败: {e}")
            return stats

    def _clean_raw_market_data(self, raw_data: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        """清洗原始市场数据"""
        try:
            if source_type == 'predict':
                return {
                    'price': raw_data.get('price'),
                    'volume': raw_data.get('volume', 0),
                    'open_price': raw_data.get('open_price'),
                    'high_price': raw_data.get('high_price'),
                    'low_price': raw_data.get('low_price'),
                    'close_price': raw_data.get('close_price'),
                    'trade_count': raw_data.get('trade_count', 0),
                    'data_quality_score': 0.9
                }
            elif source_type == 'polymarket':
                return {
                    'price': raw_data.get('yes_probability', 0.5),
                    'volume': raw_data.get('volume', 0),
                    'data_quality_score': 0.85
                }
            else:
                # 默认清洗逻辑
                return {
                    'price': raw_data.get('price'),
                    'volume': raw_data.get('volume', 0),
                    'data_quality_score': 0.8
                }
        except Exception as e:
            logger.warning(f"清洗数据失败: {e}")
            return None

    async def _mark_processed(self, record_id: int):
        """标记记录为已处理"""
        try:
            await self.storage.update_data(
                'raw_market_data',
                {'id': record_id},
                {'is_processed': True, 'updated_at': datetime.now()}
            )
    except Exception as e:
        logger.error(f"标记处理状态失败: {e}")

    async def validate_data_consistency(self, symbol: str, data_type: str = "all") -> Dict[str, Any]:
        """
        校验数据一致性

        Args:
            symbol: 资产符号
            data_type: 数据类型 (raw/clean/feature/all)

        Returns:
            校验结果
        """
        logger.info(f"开始校验 {symbol} 数据一致性: {data_type}")

        results = {}

        try:
            if data_type in ["raw", "all"]:
                # 校验Raw数据
                raw_df = self.storage.query_data(
                    'raw_market_data',
                    {'symbol': symbol},
                    limit=1000
                )
                if not raw_df.empty:
                    raw_report = data_validator.validate_raw_data(
                        raw_df, raw_df.iloc[0].get('source_type', 'unknown'), ValidationLevel.STANDARD
                    )
                    results['raw'] = {
                        'score': raw_report.score,
                        'issues': len(raw_report.issues),
                        'passed': raw_report.is_pass
                    }

            if data_type in ["clean", "all"]:
                # 校验Clean数据
                clean_df = self.storage.query_data(
                    'clean_market_data',
                    {'symbol': symbol},
                    limit=1000
                )
                if not clean_df.empty:
                    source_type = clean_df.iloc[0].get('source_type', 'unknown')
                    clean_report = data_validator.validate_clean_data(
                        clean_df, source_type, symbol, ValidationLevel.STANDARD
                    )
                    results['clean'] = {
                        'score': clean_report.score,
                        'issues': len(clean_report.issues),
                        'passed': clean_report.is_pass
                    }

            if data_type in ["feature", "all"]:
                # 校验Feature数据
                feature_df = self.storage.get_technical_indicators(
                    symbol, '1h',
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                )
                if not feature_df.empty:
                    feature_report = data_validator.validate_feature_data(
                        feature_df, symbol, '1h', ValidationLevel.STANDARD
                    )
                    results['feature'] = {
                        'score': feature_report.score,
                        'issues': len(feature_report.issues),
                        'passed': feature_report.is_pass
                    }

            logger.info(f"数据一致性校验完成: {results}")
            return results

        except Exception as e:
            logger.error(f"数据一致性校验失败: {e}")
            return {'error': str(e)}

    async def incremental_update_safety_check(self, symbol: str, new_data: pd.DataFrame,
                                             data_type: str = "clean") -> Dict[str, Any]:
        """
        增量更新安全性检查

        Args:
            symbol: 资产符号
            new_data: 新增数据
            data_type: 数据类型

        Returns:
            安全检查结果
        """
        logger.info(f"开始增量更新安全检查: {symbol} {data_type}")

        safety_result = {
            'safe_to_update': False,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }

        try:
            # 获取现有数据
            if data_type == "clean":
                existing_df = self.storage.query_data(
                    'clean_market_data',
                    {'symbol': symbol},
                    limit=5000
                )
            elif data_type == "feature":
                existing_df = self.storage.get_technical_indicators(
                    symbol, '1h',
                    datetime.now() - timedelta(days=30),
                    datetime.now()
                )
            else:
                safety_result['errors'].append(f"不支持的数据类型: {data_type}")
                return safety_result

            if existing_df.empty:
                # 没有现有数据，直接允许更新
                safety_result['safe_to_update'] = True
                safety_result['recommendations'].append("首次数据导入，无冲突风险")
                return safety_result

            # 执行增量校验
            validation_report = data_validator.validate_incremental_update(
                existing_df, new_data, symbol, data_type
            )

            # 分析校验结果
            critical_issues = [issue for issue in validation_report.issues
                             if issue.result.value in ['fail', 'error']]

            if critical_issues:
                safety_result['safe_to_update'] = False
                safety_result['errors'].extend([issue.message for issue in critical_issues])
                safety_result['recommendations'].append("建议先解决关键问题再进行更新")
            else:
                safety_result['safe_to_update'] = True
                if validation_report.score < 95:
                    safety_result['warnings'].append(f"数据质量评分较低: {validation_report.score:.1f}")
                    safety_result['recommendations'].append("建议检查数据质量后继续")

            # 检查时间范围重叠
            if not new_data.empty and 'data_timestamp' in new_data.columns:
                new_timestamps = pd.to_datetime(new_data['data_timestamp'])
                existing_timestamps = pd.to_datetime(existing_df['data_timestamp'])

                overlap = set(new_timestamps) & set(existing_timestamps)
                if overlap:
                    safety_result['warnings'].append(f"发现 {len(overlap)} 个时间戳冲突")
                    safety_result['recommendations'].append("考虑使用UPSERT模式或跳过冲突数据")

            logger.info(f"增量更新安全检查完成: {'安全' if safety_result['safe_to_update'] else '不安全'}")
            return safety_result

        except Exception as e:
            logger.error(f"增量更新安全检查失败: {e}")
            safety_result['errors'].append(f"检查过程出错: {str(e)}")
            return safety_result


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PredictLab 数据管理工具')
    parser.add_argument('action', choices=['migrate', 'klines', 'indicators', 'cleanup', 'validate', 'safety_check'],
                       help='执行操作')
    parser.add_argument('--symbol', help='资产符号')
    parser.add_argument('--source-type', help='数据源类型')
    parser.add_argument('--interval', default='1h', help='K线间隔')
    parser.add_argument('--days', type=int, default=30, help='处理天数')
    parser.add_argument('--batch-size', type=int, default=1000, help='批处理大小')
    parser.add_argument('--data-type', choices=['raw', 'clean', 'feature', 'all'], default='all',
                       help='数据类型 (用于校验)')

    args = parser.parse_args()

    manager = DataManager()

    try:
        if not await manager.connect():
            logger.error("无法连接数据库")
            return 1

        if args.action == 'migrate':
            # 数据迁移
            result = await manager.migrate_raw_to_clean(
                source_type=args.source_type,
                symbol=args.symbol,
                days_back=args.days,
                batch_size=args.batch_size
            )
            print(f"数据迁移结果: {result}")

        elif args.action == 'klines':
            # 生成K线
            if not args.symbol:
                print("生成K线需要指定 --symbol")
                return 1

            result = await manager.generate_klines_batch(
                args.symbol,
                ['1m', '5m', '1h', '1d'],
                args.days
            )
            print(f"K线生成结果: {result}")

        elif args.action == 'indicators':
            # 重算指标
            if not args.symbol:
                print("重算指标需要指定 --symbol")
                return 1

            result = await manager.recalculate_indicators(
                args.symbol,
                args.interval,
                args.days
            )
            print(f"指标重算结果: {result}")

        elif args.action == 'cleanup':
            # 清理数据
            result = await manager.cleanup_old_data(args.days)
            print(f"数据清理结果: {result}")

        elif args.action == 'validate':
            # 数据一致性校验
            if not args.symbol:
                print("数据校验需要指定 --symbol")
                return 1

            data_type = getattr(args, 'data_type', 'all')
            result = await manager.validate_data_consistency(args.symbol, data_type)
            print(f"数据一致性校验结果: {result}")

        elif args.action == 'safety_check':
            # 增量更新安全检查
            if not args.symbol:
                print("安全检查需要指定 --symbol")
                return 1

            # 这里需要模拟新数据，实际使用时应该从参数或文件读取
            mock_new_data = pd.DataFrame({
                'data_timestamp': [datetime.now()],
                'price': [50000.0],
                'volume': [1000.0]
            })

            data_type = getattr(args, 'data_type', 'clean')
            result = await manager.incremental_update_safety_check(args.symbol, mock_new_data, data_type)
            print(f"增量更新安全检查结果: {result}")

    except Exception as e:
        logger.error(f"操作失败: {e}")
        return 1
    finally:
        await manager.disconnect()

    return 0


if __name__ == "__main__":
    import pandas as pd
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
