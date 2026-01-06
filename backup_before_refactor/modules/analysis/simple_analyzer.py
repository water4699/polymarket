"""
简化版分析工具模块
合并了策略测试、图表展示和任务调度功能
适合原型阶段快速迭代
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from utils.logger import LoggerMixin


class SimpleStrategy:
    """简化版交易策略"""

    def __init__(self, name: str = "simple_ma"):
        self.name = name

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """生成交易信号 (简化版)"""
        if 'close' not in data.columns:
            return pd.Series(0, index=data.index)

        # 简单的移动平均线策略
        if len(data) < 10:
            return pd.Series(0, index=data.index)

        ma_short = data['close'].rolling(window=5).mean()
        ma_long = data['close'].rolling(window=10).mean()

        signals = pd.Series(0, index=data.index)
        signals[ma_short > ma_long] = 1  # 买入
        signals[ma_short < ma_long] = -1  # 卖出

        return signals


class SimpleBacktester(LoggerMixin):
    """简化版回测器"""

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.logger.info(f"初始化简化回测器，初始资金: {initial_capital}")

    def run_backtest(self, data: pd.DataFrame, strategy: SimpleStrategy = None) -> Dict[str, Any]:
        """运行简化回测"""
        if strategy is None:
            strategy = SimpleStrategy()

        try:
            # 生成信号
            signals = strategy.generate_signals(data)

            # 简化的交易执行
            capital = self.initial_capital
            position = 0.0
            trades = []

            for i in range(len(data)):
                signal = signals.iloc[i] if i < len(signals) else 0
                price = data['close'].iloc[i]

                # 执行交易 (简化版)
                if signal == 1 and position == 0:  # 买入
                    shares = capital / price
                    position = shares
                    capital = 0
                    trades.append({'type': 'buy', 'price': price, 'shares': shares, 'timestamp': data.index[i]})

                elif signal == -1 and position > 0:  # 卖出
                    sale_value = position * price
                    capital = sale_value
                    trades.append({'type': 'sell', 'price': price, 'value': sale_value, 'timestamp': data.index[i]})
                    position = 0

            # 计算结果
            final_value = capital + (position * data['close'].iloc[-1] if position > 0 else 0)
            total_return = (final_value - self.initial_capital) / self.initial_capital

            result = {
                'initial_capital': self.initial_capital,
                'final_value': final_value,
                'total_return': total_return,
                'total_trades': len(trades),
                'trades': trades,
                'strategy_name': strategy.name
            }

            self.logger.info(f"回测完成，收益率: {total_return:.2%}")
            return result

        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            return {}


class SimpleChartGenerator(LoggerMixin):
    """简化版图表生成器"""

    def __init__(self):
        self.logger.info("初始化简化图表生成器")

    def plot_price_chart(self, data: pd.DataFrame, title: str = "价格走势") -> str:
        """生成价格走势图 (简化版，返回文本描述)"""
        try:
            if data.empty or 'close' not in data.columns:
                return "无有效数据生成图表"

            # 计算基本统计
            start_price = data['close'].iloc[0]
            end_price = data['close'].iloc[-1]
            max_price = data['close'].max()
            min_price = data['close'].min()
            change_pct = (end_price - start_price) / start_price * 100

            # 生成简单的文本图表
            chart = f"""
=== {title} ===

价格统计:
- 起始价格: {start_price:.2f}
- 结束价格: {end_price:.2f}
- 最高价格: {max_price:.2f}
- 最低价格: {min_price:.2f}
- 涨跌幅: {change_pct:+.2f}%

数据点数: {len(data)}
时间范围: {data.index[0]} 到 {data.index[-1]}

价格走势简图:
"""
            # 生成简单的ASCII价格图
            price_range = max_price - min_price
            if price_range > 0:
                chart += self._generate_ascii_chart(data['close'], height=10)

            return chart

        except Exception as e:
            self.logger.error(f"生成图表失败: {e}")
            return f"图表生成失败: {e}"

    def plot_backtest_result(self, backtest_result: Dict[str, Any]) -> str:
        """生成回测结果报告"""
        try:
            report = f"""
=== 回测结果报告 ===

策略: {backtest_result.get('strategy_name', '未知')}
初始资金: {backtest_result.get('initial_capital', 0):.2f}
最终价值: {backtest_result.get('final_value', 0):.2f}
总收益率: {backtest_result.get('total_return', 0):.2%}
交易次数: {backtest_result.get('total_trades', 0)}

交易记录:
"""
            trades = backtest_result.get('trades', [])
            for i, trade in enumerate(trades[:10]):  # 只显示前10笔交易
                report += f"{i+1}. {trade['type']} - 价格:{trade['price']:.2f} - 时间:{trade['timestamp']}\n"

            if len(trades) > 10:
                report += f"... 还有 {len(trades)-10} 笔交易\n"

            return report

        except Exception as e:
            self.logger.error(f"生成回测报告失败: {e}")
            return f"报告生成失败: {e}"

    def _generate_ascii_chart(self, prices: pd.Series, height: int = 10) -> str:
        """生成简单的ASCII价格图"""
        min_price = prices.min()
        max_price = prices.max()
        price_range = max_price - min_price

        if price_range == 0:
            return "价格无波动"

        # 将价格归一化到0-height范围
        normalized = ((prices - min_price) / price_range * (height - 1)).astype(int)

        # 生成图表
        chart_lines = []
        for level in range(height):
            line = f"{min_price + (max_price - min_price) * level / (height - 1):.0f}".rjust(8)
            line += " |"

            # 为每个数据点生成字符
            for val in normalized:
                if val >= height - 1 - level:
                    line += "█"
                else:
                    line += " "
            chart_lines.append(line)

        # 添加X轴标签
        x_labels = "         " + "".join([f"{i:>5}" for i in range(0, len(prices), max(1, len(prices)//10))][:10])
        chart_lines.append(x_labels)

        return "\n".join(chart_lines)


class SimpleScheduler(LoggerMixin):
    """简化版任务调度器"""

    def __init__(self):
        self.tasks = []
        self.logger.info("初始化简化任务调度器")

    def add_task(self, name: str, func: Callable, interval_minutes: int = 60):
        """添加定时任务"""
        task = {
            'name': name,
            'func': func,
            'interval': timedelta(minutes=interval_minutes),
            'last_run': None
        }
        self.tasks.append(task)
        self.logger.info(f"添加任务: {name}, 间隔: {interval_minutes}分钟")

    def run_pending_tasks(self):
        """运行待执行的任务"""
        now = datetime.now()

        for task in self.tasks:
            if (task['last_run'] is None or
                now - task['last_run'] >= task['interval']):

                try:
                    self.logger.info(f"执行任务: {task['name']}")
                    task['func']()
                    task['last_run'] = now
                except Exception as e:
                    self.logger.error(f"任务执行失败 {task['name']}: {e}")

    def run_once(self, task_name: str = None):
        """运行一次指定任务或所有任务"""
        if task_name:
            # 运行指定任务
            for task in self.tasks:
                if task['name'] == task_name:
                    try:
                        self.logger.info(f"执行任务: {task_name}")
                        task['func']()
                        task['last_run'] = datetime.now()
                    except Exception as e:
                        self.logger.error(f"任务执行失败 {task_name}: {e}")
                    break
        else:
            # 运行所有任务
            for task in self.tasks:
                try:
                    self.logger.info(f"执行任务: {task['name']}")
                    task['func']()
                    task['last_run'] = datetime.now()
                except Exception as e:
                    self.logger.error(f"任务执行失败 {task['name']}: {e}")


# 全局分析工具实例
simple_strategy = SimpleStrategy()
simple_backtester = SimpleBacktester()
simple_chart_generator = SimpleChartGenerator()
simple_scheduler = SimpleScheduler()
