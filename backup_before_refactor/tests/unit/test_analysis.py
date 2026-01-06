"""
分析模块单元测试
测试回测、策略和技术指标计算
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from modules.analysis.simple_analyzer import SimpleStrategy, SimpleBacktester, SimpleChartGenerator
from utils.exceptions import BacktestError, StrategyError, VisualizationError
from tests.conftest import test_helper


class TestSimpleStrategy:
    """SimpleStrategy 单元测试"""

    @pytest.fixture
    def strategy(self):
        """简单策略实例"""
        return SimpleStrategy()

    @pytest.fixture
    def sample_price_data(self):
        """示例价格数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(hours=i) for i in range(100)]

        # 生成价格数据，有趋势和波动
        trend = np.linspace(40000, 45000, 100)
        noise = np.random.normal(0, 500, 100)
        prices = trend + noise

        data = {
            'timestamp': timestamps,
            'close_price': prices,
            'high_price': np.maximum(prices + np.random.uniform(0, 200, 100), prices),
            'low_price': np.minimum(prices - np.random.uniform(0, 200, 100), prices),
            'volume': np.random.uniform(1000, 10000, 100)
        }

        return pd.DataFrame(data)

    def test_init(self, strategy):
        """测试初始化"""
        assert strategy is not None
        assert hasattr(strategy, 'logger')

    def test_moving_average_strategy(self, strategy, sample_price_data):
        """测试移动平均线策略"""
        signals = strategy.moving_average_strategy(sample_price_data, short_window=5, long_window=20)

        assert isinstance(signals, pd.DataFrame)
        assert not signals.empty
        assert 'signal' in signals.columns

        # 检查信号值
        valid_signals = signals['signal'].dropna()
        assert all(sig in [-1, 0, 1] for sig in valid_signals)

    def test_rsi_strategy(self, strategy, sample_price_data):
        """测试RSI策略"""
        signals = strategy.rsi_strategy(sample_price_data, rsi_period=14, overbought=70, oversold=30)

        assert isinstance(signals, pd.DataFrame)
        assert not signals.empty
        assert 'signal' in signals.columns

    def test_mean_reversion_strategy(self, strategy, sample_price_data):
        """测试均值回归策略"""
        signals = strategy.mean_reversion_strategy(sample_price_data, lookback=20, threshold=2.0)

        assert isinstance(signals, pd.DataFrame)
        assert not signals.empty
        assert 'signal' in signals.columns

    def test_generate_signals_invalid_data(self, strategy):
        """测试无效数据"""
        invalid_data = pd.DataFrame({
            'invalid_column': [1, 2, 3]
        })

        with pytest.raises(StrategyError):
            strategy.moving_average_strategy(invalid_data)

    def test_strategy_with_insufficient_data(self, strategy):
        """测试数据不足的情况"""
        small_data = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now() + timedelta(hours=1)],
            'close_price': [40000, 40100]
        })

        # 对于需要较长历史的数据，应该返回空信号或抛出错误
        signals = strategy.moving_average_strategy(small_data, short_window=50, long_window=200)

        # 应该返回数据框，但信号列可能大部分为空
        assert isinstance(signals, pd.DataFrame)


class TestSimpleBacktester:
    """SimpleBacktester 单元测试"""

    @pytest.fixture
    def backtester(self):
        """回测器实例"""
        return SimpleBacktester()

    @pytest.fixture
    def sample_signals(self, sample_price_data):
        """示例信号数据"""
        signals = pd.DataFrame({
            'timestamp': sample_price_data['timestamp'],
            'close_price': sample_price_data['close_price'],
            'signal': [0] * 10 + [1] * 20 + [-1] * 20 + [0] * 50  # 买入、卖出、持有
        })
        return signals

    def test_init(self, backtester):
        """测试初始化"""
        assert backtester is not None
        assert hasattr(backtester, 'logger')

    def test_run_backtest(self, backtester, sample_signals):
        """测试运行回测"""
        initial_capital = 10000
        position_size = 0.1

        results = backtester.run_backtest(
            sample_signals,
            initial_capital=initial_capital,
            position_size=position_size
        )

        assert isinstance(results, dict)
        assert 'total_return' in results
        assert 'sharpe_ratio' in results
        assert 'max_drawdown' in results
        assert 'win_rate' in results
        assert 'total_trades' in results

        # 检查基本约束
        assert results['total_return'] >= -1.0  # 不应损失超过100%
        assert 0 <= results['win_rate'] <= 1.0

    def test_calculate_returns(self, backtester, sample_signals):
        """测试收益计算"""
        returns = backtester.calculate_returns(sample_signals)

        assert isinstance(returns, pd.Series)
        assert len(returns) == len(sample_signals)

    def test_calculate_sharpe_ratio(self, backtester):
        """测试夏普比率计算"""
        # 生成示例收益数据
        returns = pd.Series(np.random.normal(0.01, 0.05, 100))

        sharpe = backtester.calculate_sharpe_ratio(returns)

        assert isinstance(sharpe, float)
        # 夏普比率通常在合理范围内
        assert -10 <= sharpe <= 10

    def test_calculate_max_drawdown(self, backtester):
        """测试最大回撤计算"""
        # 生成下跌的价格序列
        prices = pd.Series([100, 95, 90, 85, 80, 85, 90, 95])

        max_dd = backtester.calculate_max_drawdown(prices)

        assert isinstance(max_dd, float)
        assert 0 <= max_dd <= 1.0  # 回撤是百分比

        # 对于这个序列，最大回撤应该是0.2 (从100到80)
        assert abs(max_dd - 0.2) < 0.01

    def test_calculate_win_rate(self, backtester):
        """测试胜率计算"""
        trades = [
            {'pnl': 100, 'entry_price': 100, 'exit_price': 110},  # 盈利
            {'pnl': -50, 'entry_price': 100, 'exit_price': 95},   # 亏损
            {'pnl': 200, 'entry_price': 100, 'exit_price': 120},  # 盈利
        ]

        win_rate = backtester.calculate_win_rate(trades)

        assert isinstance(win_rate, float)
        assert 0 <= win_rate <= 1.0
        assert win_rate == 2/3  # 2笔盈利，3笔总交易

    def test_run_backtest_invalid_signals(self, backtester):
        """测试无效信号数据"""
        invalid_signals = pd.DataFrame({
            'invalid_column': [1, 2, 3]
        })

        with pytest.raises(BacktestError):
            backtester.run_backtest(invalid_signals)

    def test_run_backtest_empty_data(self, backtester):
        """测试空数据"""
        empty_signals = pd.DataFrame()

        with pytest.raises(BacktestError):
            backtester.run_backtest(empty_signals)

    def test_backtest_with_different_position_sizes(self, backtester, sample_signals):
        """测试不同仓位大小"""
        results_small = backtester.run_backtest(sample_signals, position_size=0.1)
        results_large = backtester.run_backtest(sample_signals, position_size=0.5)

        # 不同仓位应该产生不同的结果
        assert results_small != results_large


class TestSimpleChartGenerator:
    """SimpleChartGenerator 单元测试"""

    @pytest.fixture
    def chart_generator(self):
        """图表生成器实例"""
        return SimpleChartGenerator()

    @pytest.fixture
    def sample_chart_data(self):
        """示例图表数据"""
        base_time = datetime(2024, 1, 1, 0, 0, 0)
        timestamps = [base_time + timedelta(hours=i) for i in range(50)]

        data = {
            'timestamp': timestamps,
            'price': np.random.uniform(40000, 45000, 50),
            'volume': np.random.uniform(1000, 10000, 50),
            'sma_20': np.random.uniform(40000, 45000, 50),
            'rsi': np.random.uniform(20, 80, 50)
        }

        return pd.DataFrame(data)

    def test_init(self, chart_generator):
        """测试初始化"""
        assert chart_generator is not None
        assert hasattr(chart_generator, 'logger')

    def test_generate_price_chart(self, chart_generator, sample_chart_data):
        """测试价格图表生成"""
        chart = chart_generator.generate_price_chart(sample_chart_data)

        assert isinstance(chart, str)
        assert len(chart) > 0
        # 应该包含ASCII字符
        assert any(char in chart for char in ['│', '─', '┼', '*'])

    def test_generate_volume_chart(self, chart_generator, sample_chart_data):
        """测试成交量图表生成"""
        chart = chart_generator.generate_volume_chart(sample_chart_data)

        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_generate_combined_chart(self, chart_generator, sample_chart_data):
        """测试组合图表生成"""
        chart = chart_generator.generate_combined_chart(sample_chart_data)

        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_generate_chart_invalid_data(self, chart_generator):
        """测试无效数据"""
        invalid_data = pd.DataFrame({
            'invalid_column': [1, 2, 3]
        })

        with pytest.raises(VisualizationError):
            chart_generator.generate_price_chart(invalid_data)

    def test_generate_chart_empty_data(self, chart_generator):
        """测试空数据"""
        empty_data = pd.DataFrame()

        with pytest.raises(VisualizationError):
            chart_generator.generate_price_chart(empty_data)

    def test_chart_with_signals(self, chart_generator, sample_chart_data):
        """测试带信号的图表"""
        # 添加信号列
        data_with_signals = sample_chart_data.copy()
        data_with_signals['signal'] = [0] * 40 + [1] * 5 + [-1] * 5  # 买入卖出信号

        chart = chart_generator.generate_price_chart(data_with_signals, show_signals=True)

        assert isinstance(chart, str)
        assert len(chart) > 0
        # 可能包含信号标记
        assert any(char in chart for char in ['▲', '▼', '●'])

    def test_chart_custom_size(self, chart_generator, sample_chart_data):
        """测试自定义图表尺寸"""
        custom_chart = chart_generator.generate_price_chart(
            sample_chart_data,
            width=100,
            height=20
        )

        assert isinstance(custom_chart, str)
        assert len(custom_chart) > 0

    def test_normalize_data(self, chart_generator):
        """测试数据归一化"""
        data = pd.Series([100, 200, 300, 400, 500])

        normalized = chart_generator._normalize_data(data, height=10)

        assert isinstance(normalized, pd.Series)
        assert len(normalized) == len(data)
        assert normalized.min() >= 0
        assert normalized.max() < 10

    def test_create_ascii_bar(self, chart_generator):
        """测试ASCII条形图创建"""
        bar = chart_generator._create_ascii_bar(5, max_height=10)

        assert isinstance(bar, str)
        assert len(bar) > 0
        assert '█' in bar or '▌' in bar  # 应该包含块字符


class TestAnalysisIntegration:
    """分析模块集成测试"""

    @pytest.fixture
    def analysis_pipeline(self):
        """分析管道"""
        return {
            'strategy': SimpleStrategy(),
            'backtester': SimpleBacktester(),
            'chart_generator': SimpleChartGenerator()
        }

    def test_full_analysis_workflow(self, analysis_pipeline, sample_price_data):
        """测试完整分析工作流"""
        strategy = analysis_pipeline['strategy']
        backtester = analysis_pipeline['backtester']
        chart_gen = analysis_pipeline['chart_generator']

        # 1. 生成交易信号
        signals = strategy.moving_average_strategy(sample_price_data, short_window=5, long_window=20)
        assert not signals.empty

        # 2. 运行回测
        results = backtester.run_backtest(signals)
        assert isinstance(results, dict)
        assert 'total_return' in results

        # 3. 生成图表
        chart = chart_gen.generate_price_chart(signals)
        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_strategy_backtest_consistency(self, analysis_pipeline, sample_price_data):
        """测试策略和回测的一致性"""
        strategy = analysis_pipeline['strategy']
        backtester = analysis_pipeline['backtester']

        # 生成信号
        signals = strategy.rsi_strategy(sample_price_data)

        # 确保信号数据包含价格信息
        signals['close_price'] = sample_price_data['close_price']

        # 回测
        results = backtester.run_backtest(signals)

        # 验证结果合理性
        assert isinstance(results['total_trades'], int)
        assert results['total_trades'] >= 0


class TestAnalysisEdgeCases:
    """分析模块边界情况测试"""

    @pytest.fixture
    def strategy(self):
        return SimpleStrategy()

    @pytest.fixture
    def backtester(self):
        return SimpleBacktester()

    @pytest.fixture
    def chart_generator(self):
        return SimpleChartGenerator()

    def test_strategy_with_minimum_data(self, strategy):
        """测试策略最小数据量"""
        # 只有2个数据点
        minimal_data = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now() + timedelta(hours=1)],
            'close_price': [40000, 40100]
        })

        signals = strategy.moving_average_strategy(minimal_data, short_window=2, long_window=2)

        # 应该返回数据框，但信号可能为空
        assert isinstance(signals, pd.DataFrame)

    def test_backtester_with_no_trades(self, backtester):
        """测试无交易的回测"""
        # 所有信号都是0（持有）
        no_trade_signals = pd.DataFrame({
            'timestamp': [datetime.now() + timedelta(hours=i) for i in range(10)],
            'close_price': [40000 + i*100 for i in range(10)],
            'signal': [0] * 10
        })

        results = backtester.run_backtest(no_trade_signals)

        assert results['total_trades'] == 0
        assert results['win_rate'] == 0.0

    def test_chart_with_single_point(self, chart_generator):
        """测试单点图表"""
        single_point = pd.DataFrame({
            'timestamp': [datetime.now()],
            'price': [40000]
        })

        chart = chart_generator.generate_price_chart(single_point)

        assert isinstance(chart, str)
        assert len(chart) > 0

    def test_extreme_price_values(self, strategy):
        """测试极端价格值"""
        extreme_data = pd.DataFrame({
            'timestamp': [datetime.now() + timedelta(hours=i) for i in range(10)],
            'close_price': [1e-10, 1e20, 0, -1000, 1e15, 50000, 1e10, 1e-5, 1e25, 1e30]
        })

        signals = strategy.mean_reversion_strategy(extreme_data)

        # 应该能处理极端值而不崩溃
        assert isinstance(signals, pd.DataFrame)
