#!/usr/bin/env python3
"""
演示如何基于 condition_id 和 token 获取预测活动的交易信息
"""

from polygon import PolygonClient
import json

def demo_market_trades():
    """演示市场交易数据获取"""
    print("🎯 预测活动交易数据获取演示")
    print("=" * 60)

    try:
        # 初始化客户端
        client = PolygonClient()
        print("✅ Polygon 客户端初始化成功")

        # 示例1: 获取热门市场的一个condition_id
        print("\n📊 示例1: 获取热门市场的交易数据")
        popular_markets = client.get_popular_markets(limit=3)

        if popular_markets:
            market = popular_markets[0]
            condition_id = market['condition_id']

            print(f"选择市场: {market['question'][:50]}...")
            print(f"ConditionId: {condition_id}")

            # 获取该市场的详细交易信息
            trade_data = client.get_market_trades_by_condition_and_token(
                condition_id=condition_id,
                limit=5  # 每个token最多5条交易
            )

            print(f"\\n📈 交易数据汇总:")
            print(f"  • 总交易数: {trade_data['total_trades']}")
            print(f"  • Token数量: {trade_data['tokens_count']}")
            print(f"  • 有交易的Token数: {len(trade_data['token_trades'])}")

            # 显示每个token的交易情况
            for token_id, trades in trade_data['token_trades'].items():
                print(f"\\n  🏷️  TokenId: {token_id}")
                print(f"     交易数量: {len(trades)}")

                if trades:
                    # 显示最新的3条交易
                    for i, trade in enumerate(trades[:3], 1):
                        print(f"     {i}. Block: {trade['blockNumber']}, Value: {trade['value']}, Tx: {trade['txHash'][:10]}...")

        # 示例2: 指定特定的 condition_id 和 token_id
        print("\\n\\n🎯 示例2: 指定 condition_id 和 token_id")
        if popular_markets and len(popular_markets) > 0:
            market = popular_markets[0]
            condition_id = market['condition_id']
            token_ids = market.get('token_ids', [])

            if token_ids:
                specific_token_id = str(token_ids[0])  # 选择第一个token

                print(f"ConditionId: {condition_id}")
                print(f"TokenId: {specific_token_id}")

                # 获取特定token的交易
                token_trade_data = client.get_market_trades_by_condition_and_token(
                    condition_id=condition_id,
                    token_id=specific_token_id,
                    limit=10
                )

                print(f"\\n📊 特定Token交易数据:")
                print(f"  • 交易数量: {token_trade_data['total_trades']}")

                if token_trade_data['token_trades']:
                    trades = list(token_trade_data['token_trades'].values())[0]
                    print("  • 详细交易记录:")
                    for i, trade in enumerate(trades[:5], 1):
                        print(f"    {i}. Block: {trade['blockNumber']}")
                        print(f"       From: {trade['from']}")
                        print(f"       To: {trade['to']}")
                        print(f"       Value: {trade['value']}")
                        print(f"       TxHash: {trade['txHash']}")
                        print()

        # 示例3: 获取最近的交易记录（合并所有token）
        print("\\n🚀 示例3: 获取最近交易记录（合并排序）")
        if popular_markets:
            market = popular_markets[0]
            condition_id = market['condition_id']

            recent_trades = client.get_recent_market_trades(
                condition_id=condition_id,
                limit_per_token=3  # 每个token取3条
            )

            print(f"市场: {market['question'][:40]}...")
            print(f"最近交易总数: {len(recent_trades)}")

            if recent_trades:
                print("\\n📅 最新交易记录 (按时间倒序):")
                for i, trade in enumerate(recent_trades[:5], 1):
                    import datetime
                    timestamp = datetime.datetime.fromtimestamp(trade['timestamp'])
                    print(f"  {i}. {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Block: {trade['blockNumber']} - Value: {trade['value']}")

        print("\\n" + "=" * 60)
        print("✅ 演示完成！")
        print("\\n💡 使用提示:")
        print("1. condition_id: 可以在 data/ 目录的 JSON 文件中找到")
        print("2. token_id: 可选参数，不提供则获取该市场所有token的交易")
        print("3. limit: 控制每个token返回的交易数量")
        print("4. 交易数据按时间倒序返回，最新的在前面")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

def show_usage_examples():
    """显示使用示例代码"""
    print("\\n" + "=" * 60)
    print("📝 使用示例代码")
    print("=" * 60)

    examples = '''
# 基本使用方法

from polygon import PolygonClient

client = PolygonClient()

# 方法1: 获取指定市场的所有token交易
trade_data = client.get_market_trades_by_condition_and_token(
    condition_id="0x9708334534b504e2025a5a6af92f8600808c10be577e5066f920c40625fbec16",
    limit=10  # 每个token最多10条交易
)

print(f"总交易数: {trade_data['total_trades']}")
print(f"涉及Token数: {len(trade_data['token_trades'])}")

# 方法2: 获取特定token的交易
token_trades = client.get_market_trades_by_condition_and_token(
    condition_id="0x9708334534b504e2025a5a6af92f8600808c10be577e5066f920c40625fbec16",
    token_id="94401806442428580808350321395221392306408700984448347080151499651427713760581",
    limit=20
)

# 方法3: 获取最近交易（合并所有token，按时间排序）
recent_trades = client.get_recent_market_trades(
    condition_id="0x9708334534b504e2025a5a6af92f8600808c10be577e5066f920c40625fbec16",
    limit_per_token=5
)

# 交易记录包含以下字段:
# - blockNumber: 区块号
# - txHash: 交易哈希
# - timestamp: 时间戳
# - from: 发送者地址
# - to: 接收者地址
# - tokenId: Token ID
# - value: 交易数量
# - conditionId: 条件ID
'''

    print(examples)

if __name__ == "__main__":
    demo_market_trades()
    show_usage_examples()
