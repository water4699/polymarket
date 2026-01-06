"""
Airflow 数据管道 DAG
使用 Apache Airflow 编排 PredictLab 数据处理流程
包含依赖管理、失败重试和监控
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from airflow.utils.trigger_rule import TriggerRule
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.models import Variable
import logging

# 默认参数
default_args = {
    'owner': 'predictlab',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
    'catchup': False,
}

# DAG 配置
dag = DAG(
    'predictlab_data_pipeline',
    default_args=default_args,
    description='PredictLab 完整数据处理管道',
    schedule_interval='0 */4 * * *',  # 每4小时执行一次
    max_active_runs=1,
    catchup=False,
    tags=['predictlab', 'data-pipeline', 'crypto'],
)

# ===========================================
# 任务定义函数
# ===========================================

def get_pipeline_config(**context):
    """获取管道配置"""
    # 从 Airflow Variables 获取配置，或使用默认值
    try:
        config = Variable.get("predictlab_pipeline_config", deserialize_json=True)
    except:
        config = {
            'symbols': ['BTC_PRICE', 'ETH_PRICE'],
            'source_types': ['predict'],
            'intervals': ['1h', '1d'],
            'days_back': 2,  # 每次处理最近2天的数据
            'max_retries': 3,
            'batch_size': 1000
        }

    logging.info(f"管道配置: {config}")
    return config

def collect_data_task(source_type, symbol, days_back, **context):
    """数据采集任务"""
    from modules.data_source.predict_source import PredictDataSource
    from modules.data_source.polymarket_source import PolymarketDataSource
    from modules.data_storage.postgres_storage import PostgresStorage
    import pandas as pd
    from datetime import datetime, timedelta

    logging.info(f"开始采集 {source_type} {symbol} 数据")

    # 选择数据源
    if source_type == 'predict':
        ds = PredictDataSource()
    elif source_type == 'polymarket':
        ds = PolymarketDataSource()
    else:
        raise ValueError(f"不支持的数据源: {source_type}")

    try:
        # 连接数据源
        if not ds.connect():
            raise Exception(f"无法连接到 {source_type} 数据源")

        # 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)

        # 采集数据
        data = ds.fetch_data(symbol, start_time, end_time)

        if data.empty:
            logging.warning(f"未采集到 {source_type} {symbol} 数据")
            return {'status': 'empty', 'symbol': symbol, 'source_type': source_type}

        # 存储原始数据
        storage = PostgresStorage()
        if not storage.connect():
            raise Exception("无法连接数据库")

        try:
            # 插入原始数据
            records_stored = 0
            for _, row in data.iterrows():
                success = storage.insert_raw_market_data(
                    source_type, symbol, row.get('timestamp', datetime.now()),
                    {
                        'price': row.get('price'),
                        'volume': row.get('volume', 0),
                        'source': source_type,
                        'raw_data': row.to_dict()
                    }
                )
                if success:
                    records_stored += 1

            logging.info(f"成功存储 {records_stored} 条原始数据")
            return {
                'status': 'success',
                'symbol': symbol,
                'source_type': source_type,
                'records': records_stored,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }

        finally:
            storage.disconnect()

    except Exception as e:
        logging.error(f"数据采集失败: {e}")
        raise
    finally:
        ds.disconnect()

def clean_data_task(source_type, symbol, **context):
    """数据清洗任务"""
    from modules.data_processing.data_cleaner import DataCleaner
    from modules.data_storage.postgres_storage import PostgresStorage
    import pandas as pd

    logging.info(f"开始清洗 {source_type} {symbol} 数据")

    storage = PostgresStorage()
    if not storage.connect():
        raise Exception("无法连接数据库")

    try:
        # 从原始数据查询需要清洗的数据
        raw_data = storage.query_data(
            'raw_market_data',
            {
                'source_type': source_type,
                'symbol': symbol,
                'is_processed': False
            },
            limit=5000  # 每次处理最多5000条
        )

        if raw_data.empty:
            logging.info(f"没有需要清洗的 {source_type} {symbol} 数据")
            return {'status': 'no_data', 'symbol': symbol}

        # 数据清洗
        cleaner = DataCleaner()
        if source_type in ['predict', 'polymarket']:
            cleaned_data = cleaner.clean_market_data(raw_data)
        else:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        if cleaned_data.empty:
            logging.warning("清洗后数据为空")
            return {'status': 'empty_after_clean', 'symbol': symbol}

        # 存储清洗后的数据
        records_cleaned = 0
        for _, row in cleaned_data.iterrows():
            clean_record = {
                'price': row.get('price'),
                'volume': row.get('volume', 0),
                'open_price': row.get('open_price'),
                'high_price': row.get('high_price'),
                'low_price': row.get('low_price'),
                'close_price': row.get('close_price'),
                'trade_count': row.get('trade_count', 0),
                'data_quality_score': 0.9,
                'raw_data_id': row.get('id')
            }

            success = storage.insert_clean_market_data(
                source_type, symbol, row['timestamp'], clean_record
            )
            if success:
                records_cleaned += 1

        # 标记原始数据为已处理
        processed_ids = raw_data['id'].tolist()
        for record_id in processed_ids[:1000]:  # 限制批量更新大小
            storage.update_data(
                'raw_market_data',
                {'id': record_id},
                {'is_processed': True}
            )

        logging.info(f"成功清洗并存储 {records_cleaned} 条数据")
        return {
            'status': 'success',
            'symbol': symbol,
            'source_type': source_type,
            'raw_records': len(raw_data),
            'clean_records': records_cleaned
        }

    except Exception as e:
        logging.error(f"数据清洗失败: {e}")
        raise
    finally:
        storage.disconnect()

def generate_klines_task(symbol, interval, days_back, **context):
    """K线生成任务"""
    from modules.data_processing.kline_generator import KlineGenerator
    from modules.data_storage.postgres_storage import PostgresStorage
    import pandas as pd
    from datetime import datetime, timedelta

    logging.info(f"开始生成 {symbol} {interval} K线")

    storage = PostgresStorage()
    if not storage.connect():
        raise Exception("无法连接数据库")

    try:
        # 获取基础数据
        start_time = datetime.now() - timedelta(days=days_back)
        base_data = storage.query_data(
            'clean_market_data',
            {
                'symbol': symbol,
                'data_timestamp >=': start_time
            },
            sort_by='data_timestamp',
            ascending=True
        )

        if base_data.empty:
            logging.warning(f"没有找到 {symbol} 的基础数据")
            return {'status': 'no_data', 'symbol': symbol, 'interval': interval}

        # 生成K线
        generator = KlineGenerator()
        kline_data = generator.generate_klines(
            base_data, interval,
            price_col='price',
            volume_col='volume',
            timestamp_col='data_timestamp'
        )

        if kline_data.empty:
            logging.warning("K线数据为空")
            return {'status': 'empty_klines', 'symbol': symbol, 'interval': interval}

        # 存储K线数据
        kline_count = 0
        for _, row in kline_data.iterrows():
            kline_record = {
                'open_price': row['open'],
                'high_price': row['high'],
                'low_price': row['low'],
                'close_price': row['close'],
                'volume': row['volume'],
                'trade_count': 0,  # 聚合后可能没有交易计数
                'vwap': row.get('close', 0),  # 简化计算
                'data_points': len(base_data),
                'data_quality_score': 0.95,
                'is_complete': True
            }

            success = storage.insert_kline_data(
                'predict', symbol, interval,
                row['timestamp'], row['timestamp'] + pd.Timedelta(interval),
                kline_record
            )
            if success:
                kline_count += 1

        logging.info(f"成功生成并存储 {kline_count} 条K线数据")
        return {
            'status': 'success',
            'symbol': symbol,
            'interval': interval,
            'kline_count': kline_count,
            'base_records': len(base_data)
        }

    except Exception as e:
        logging.error(f"K线生成失败: {e}")
        raise
    finally:
        storage.disconnect()

def backtest_task(symbol, **context):
    """策略回测任务"""
    from modules.analysis.simple_analyzer import SimpleBacktester, SimpleStrategy
    from modules.data_storage.postgres_storage import PostgresStorage
    import pandas as pd
    from datetime import datetime, timedelta

    logging.info(f"开始回测 {symbol} 策略")

    storage = PostgresStorage()
    if not storage.connect():
        raise Exception("无法连接数据库")

    try:
        # 获取K线数据
        kline_data = storage.get_klines(
            symbol, '1h',
            datetime.now() - timedelta(days=30),
            datetime.now()
        )

        if kline_data.empty:
            logging.warning(f"没有找到 {symbol} 的K线数据")
            return {'status': 'no_kline_data', 'symbol': symbol}

        # 运行回测
        backtester = SimpleBacktester()
        strategy = SimpleStrategy()
        result = backtester.run_backtest(kline_data, strategy)

        logging.info(f"回测完成: 收益率 {result.get('total_return', 0):.2%}")
        return {
            'status': 'success',
            'symbol': symbol,
            'backtest_result': result
        }

    except Exception as e:
        logging.error(f"回测失败: {e}")
        raise
    finally:
        storage.disconnect()

def visualize_task(symbol, **context):
    """可视化任务"""
    from modules.analysis.simple_analyzer import SimpleChartGenerator
    from modules.data_storage.postgres_storage import PostgresStorage
    import pandas as pd
    from datetime import datetime, timedelta
    import os

    logging.info(f"开始生成 {symbol} 可视化")

    storage = PostgresStorage()
    if not storage.connect():
        raise Exception("无法连接数据库")

    try:
        # 获取数据
        kline_data = storage.get_klines(
            symbol, '1d',
            datetime.now() - timedelta(days=90),
            datetime.now()
        )

        if kline_data.empty:
            logging.warning(f"没有找到 {symbol} 的日线数据")
            return {'status': 'no_data', 'symbol': symbol}

        # 生成图表
        chart_generator = SimpleChartGenerator()
        price_chart = chart_generator.plot_price_chart(kline_data, f"{symbol} 价格走势")

        # 保存到文件 (在Airflow logs目录下)
        charts_dir = os.path.join(os.environ.get('AIRFLOW__CORE__DAGS_FOLDER', '/opt/airflow/dags'), 'charts')
        os.makedirs(charts_dir, exist_ok=True)

        chart_file = os.path.join(charts_dir, f"{symbol}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(chart_file, 'w') as f:
            f.write(price_chart)

        logging.info(f"可视化完成，保存到: {chart_file}")
        return {
            'status': 'success',
            'symbol': symbol,
            'chart_file': chart_file
        }

    except Exception as e:
        logging.error(f"可视化失败: {e}")
        raise
    finally:
        storage.disconnect()

def health_check_task(**context):
    """健康检查任务"""
    from modules.data_storage.postgres_storage import PostgresStorage

    logging.info("执行健康检查")

    storage = PostgresStorage()
    if not storage.connect():
        raise Exception("无法连接数据库")

    try:
        # 检查各表的数据量
        tables = ['raw_market_data', 'clean_market_data', 'clean_kline_data', 'feature_technical_indicators']
        health_stats = {}

        for table in tables:
            try:
                # 获取最近24小时的数据量
                df = storage.query_data(
                    table,
                    {'created_at >=': datetime.now() - timedelta(hours=24)},
                    limit=1
                )
                health_stats[table] = {'status': 'ok', 'has_recent_data': not df.empty}
            except Exception as e:
                health_stats[table] = {'status': 'error', 'error': str(e)}

        logging.info(f"健康检查完成: {health_stats}")
        return health_stats

    except Exception as e:
        logging.error(f"健康检查失败: {e}")
        raise
    finally:
        storage.disconnect()

def cleanup_task(days_to_keep=90, **context):
    """数据清理任务"""
    from db.data_manager import DataManager

    logging.info(f"开始清理 {days_to_keep} 天前的数据")

    manager = DataManager()
    if not manager.connect():
        raise Exception("无法连接数据管理器")

    try:
        result = manager.cleanup_old_data(days_to_keep)
        logging.info(f"数据清理完成: {result}")
        return result

    except Exception as e:
        logging.error(f"数据清理失败: {e}")
        raise
    finally:
        manager.disconnect()

# ===========================================
# DAG 任务定义
# ===========================================

# 开始任务
start_pipeline = DummyOperator(
    task_id='start_pipeline',
    dag=dag,
)

# 获取配置
get_config = PythonOperator(
    task_id='get_pipeline_config',
    python_callable=get_pipeline_config,
    dag=dag,
)

# 数据采集任务 (动态生成)
def create_collect_tasks():
    """动态创建数据采集任务"""
    config = get_pipeline_config()
    tasks = []

    for source_type in config['source_types']:
        for symbol in config['symbols']:
            task = PythonOperator(
                task_id=f'collect_{source_type}_{symbol}',
                python_callable=collect_data_task,
                op_kwargs={
                    'source_type': source_type,
                    'symbol': symbol,
                    'days_back': config['days_back']
                },
                retries=config['max_retries'],
                retry_delay=timedelta(minutes=2),
                execution_timeout=timedelta(minutes=30),
                dag=dag,
            )
            tasks.append(task)
    return tasks

# 数据清洗任务 (动态生成)
def create_clean_tasks():
    """动态创建数据清洗任务"""
    config = get_pipeline_config()
    tasks = []

    for source_type in config['source_types']:
        for symbol in config['symbols']:
            task = PythonOperator(
                task_id=f'clean_{source_type}_{symbol}',
                python_callable=clean_data_task,
                op_kwargs={
                    'source_type': source_type,
                    'symbol': symbol
                },
                retries=2,
                retry_delay=timedelta(minutes=1),
                execution_timeout=timedelta(minutes=15),
                trigger_rule=TriggerRule.ALL_SUCCESS,  # 只有上游成功才执行
                dag=dag,
            )
            tasks.append(task)
    return tasks

# K线生成任务 (动态生成)
def create_kline_tasks():
    """动态创建K线生成任务"""
    config = get_pipeline_config()
    tasks = []

    for symbol in config['symbols']:
        for interval in config['intervals']:
            task = PythonOperator(
                task_id=f'kline_{symbol}_{interval}',
                python_callable=generate_klines_task,
                op_kwargs={
                    'symbol': symbol,
                    'interval': interval,
                    'days_back': config['days_back']
                },
                retries=2,
                retry_delay=timedelta(minutes=2),
                execution_timeout=timedelta(minutes=20),
                dag=dag,
            )
            tasks.append(task)
    return tasks

# 回测任务 (动态生成)
def create_backtest_tasks():
    """动态创建回测任务"""
    config = get_pipeline_config()
    tasks = []

    for symbol in config['symbols']:
        task = PythonOperator(
            task_id=f'backtest_{symbol}',
            python_callable=backtest_task,
            op_kwargs={'symbol': symbol},
            retries=1,
            retry_delay=timedelta(minutes=1),
            execution_timeout=timedelta(minutes=10),
            dag=dag,
        )
        tasks.append(task)
    return tasks

# 可视化任务 (动态生成)
def create_visualize_tasks():
    """动态创建可视化任务"""
    config = get_pipeline_config()
    tasks = []

    for symbol in config['symbols']:
        task = PythonOperator(
            task_id=f'visualize_{symbol}',
            python_callable=visualize_task,
            op_kwargs={'symbol': symbol},
            retries=1,
            retry_delay=timedelta(minutes=1),
            execution_timeout=timedelta(minutes=5),
            dag=dag,
        )
        tasks.append(task)
    return tasks

# 健康检查任务
health_check = PythonOperator(
    task_id='health_check',
    python_callable=health_check_task,
    retries=1,
    retry_delay=timedelta(minutes=1),
    execution_timeout=timedelta(minutes=5),
    trigger_rule=TriggerRule.ALL_DONE,  # 无论上游成功失败都执行
    dag=dag,
)

# 数据清理任务
cleanup = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_task,
    op_kwargs={'days_to_keep': 90},
    retries=1,
    retry_delay=timedelta(minutes=1),
    execution_timeout=timedelta(minutes=10),
    trigger_rule=TriggerRule.ALL_SUCCESS,
    dag=dag,
)

# 结束任务
end_pipeline = DummyOperator(
    task_id='end_pipeline',
    trigger_rule=TriggerRule.ALL_DONE,
    dag=dag,
)

# ===========================================
# 任务依赖关系设置
# ===========================================

# 获取配置后开始数据采集
get_config >> start_pipeline

# 动态创建任务并设置依赖
collect_tasks = create_collect_tasks()
clean_tasks = create_clean_tasks()
kline_tasks = create_kline_tasks()
backtest_tasks = create_backtest_tasks()
visualize_tasks = create_visualize_tasks()

# 数据采集 -> 数据清洗
for i, collect_task in enumerate(collect_tasks):
    source_type = get_pipeline_config()['source_types'][i // len(get_pipeline_config()['symbols'])]
    symbol = get_pipeline_config()['symbols'][i % len(get_pipeline_config()['symbols'])]

    # 找到对应的清洗任务
    for clean_task in clean_tasks:
        if f"{source_type}_{symbol}" in clean_task.task_id:
            collect_task >> clean_task
            break

# 数据清洗 -> K线生成
for symbol in get_pipeline_config()['symbols']:
    # 找到该symbol的所有清洗任务
    symbol_clean_tasks = [t for t in clean_tasks if symbol in t.task_id]

    # 找到该symbol的所有K线任务
    symbol_kline_tasks = [t for t in kline_tasks if symbol in t.task_id]

    # 清洗任务完成后，生成K线
    for clean_task in symbol_clean_tasks:
        for kline_task in symbol_kline_tasks:
            clean_task >> kline_task

# K线生成 -> 回测
for symbol in get_pipeline_config()['symbols']:
    symbol_kline_tasks = [t for t in kline_tasks if symbol in t.task_id]
    symbol_backtest_task = next((t for t in backtest_tasks if symbol in t.task_id), None)

    if symbol_backtest_task:
        for kline_task in symbol_kline_tasks:
            kline_task >> symbol_backtest_task

# 回测 -> 可视化
for symbol in get_pipeline_config()['symbols']:
    symbol_backtest_task = next((t for t in backtest_tasks if symbol in t.task_id), None)
    symbol_visualize_task = next((t for t in visualize_tasks if symbol in t.task_id), None)

    if symbol_backtest_task and symbol_visualize_task:
        symbol_backtest_task >> symbol_visualize_task

# 所有任务完成后执行健康检查和清理
all_tasks = collect_tasks + clean_tasks + kline_tasks + backtest_tasks + visualize_tasks
for task in all_tasks:
    task >> health_check
    task >> cleanup

# 最终结束
health_check >> end_pipeline
cleanup >> end_pipeline
