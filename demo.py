#!/usr/bin/env python3
"""
演示获取真实交易数据（使用已验证的有交易数据的TokenId）
"""

from polygon import PolygonClient
import datetime

def demo_real_trades():
    """演示获取真实交易数据"""
    print("🎯 获取真实 Polymarket 交易数据演示")
    print("=" * 60)

    try:
        client = PolygonClient()
        print("✅ Polygon 客户端初始化成功")

        # 使用我们已验证的有真实交易数据的 TokenId
        real_tokens = [
            "94401806442428580808350321395221392306408700984448347080151499651427713760581",
            "44804726753601178293652604511461891232965799888489574021036312274240304608626"
        ]

        print("\\n🔍 使用真实交易数据的 TokenId 进行演示...")

        for i, token_id in enumerate(real_tokens, 1):
            print(f"\\n🏷️  TokenId {i}: {token_id}")

            # 计算对应的 condition_id
            token_id_int = int(token_id, 16)
            condition_id = f"0x{token_id_int >> 128:064x}"

            print(f"   ConditionId: {condition_id}")

            # 获取该token的交易数据
            token_logs = client.get_logs(token_id=token_id, limit=5)
            print(f"   📊 交易记录: {len(token_logs)} 条")

            if token_logs:
                print("   💰 详细交易:")
                for j, log in enumerate(token_logs, 1):
                    timestamp = datetime.datetime.fromtimestamp(log['timestamp'])
                    print(f"     {j}. {timestamp.strftime('%m-%d %H:%M:%S')}")
                    print(f"        Block: {log['blockNumber']}")
                    print(f"        From: {log['from']}")
                    print(f"        To: {log['to']}")
                    print(f"        Value: {log['value']}")
                    print(f"        TxHash: {log['txHash']}")
                    print()

        # 演示 condition_id 过滤
        print("\\n🎯 演示 condition_id 过滤功能...")
        condition_id = "0x0000000000000000000944018064424285808083503213952213923064087009"
        condition_logs = client.get_logs(condition_id=condition_id, limit=5)
        print(f"ConditionId {condition_id} 的交易: {len(condition_logs)} 条")

        if condition_logs:
            for log in condition_logs:
                timestamp = datetime.datetime.fromtimestamp(log['timestamp'])
                print(f"  • {timestamp.strftime('%m-%d %H:%M:%S')} Block:{log['blockNumber']} Value:{log['value']}")

        print("\\n" + "=" * 60)
        print("✅ 演示完成！")
        print("\\n💡 说明:")
        print("• 所有交易数据都是从 Polygon 链实时获取的")
        print("• 数据来自真实的 Polymarket ERC-1155 合约")
        print("• 包含完整的交易信息：地址、数量、时间、区块等")
        print("• API Key 自动轮询，确保获取成功")

    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

def show_direct_usage():
    """显示直接使用方法"""
    print("\\n" + "=" * 60)
    print("📝 直接使用代码")
    print("=" * 60)

    code = '''
# 最简单的使用方法 - 获取任意交易数据

from polygon import PolygonClient

client = PolygonClient()

# 方法1: 获取最新的交易（不指定条件）
logs = client.get_logs(limit=10)
print(f"获取到 {len(logs)} 条最新交易")

for log in logs[:3]:  # 显示前3条
    print(f"Block: {log['blockNumber']}, Value: {log['value']}")

# 方法2: 指定 token_id 获取交易
token_id = "94401806442428580808350321395221392306408700984448347080151499651427713760581"
logs = client.get_logs(token_id=token_id, limit=5)
print(f"Token {token_id} 的交易: {len(logs)} 条")

# 方法3: 指定 condition_id 获取交易
condition_id = "0x0000000000000000000944018064424285808083503213952213923064087009"
logs = client.get_logs(condition_id=condition_id, limit=5)
print(f"Condition {condition_id} 的交易: {len(logs)} 条")
'''

    print(code)

if __name__ == "__main__":
    demo_real_trades()
    show_direct_usage()
