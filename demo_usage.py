#!/usr/bin/env python3
"""
Polygon Polymarket 数据抓取使用演示
展示如何使用PolygonClient获取交易数据
"""

from typing import List, Dict
from polygon import PolygonClient
from modules.api_key_manager import APIKeyManager

def demo_api_key_manager():
    """演示API Key管理器功能"""
    print("🔑 API Key管理器演示")
    print("=" * 50)

    try:
        # 创建API Key管理器（连接数据库）
        from config import config
        manager = APIKeyManager(config.postgres_url)

        stats = manager.get_usage_stats()
        print("✅ API Key管理器连接数据库成功")
        print(f"   API Keys数量: {stats['total_keys']}")
        print(f"   可用Keys: {stats['available_keys']}")

        if stats['total_keys'] > 0:
            # 演示轮询功能
            print("\\n轮询获取API Keys:")
            for i in range(min(6, stats['total_keys'])):
                key = manager.get_next_key()
                if key:
                    print(f"  {i+1}. 获取到: {key[:10]}...")
                else:
                    print(f"  {i+1}. 无可用API Key")

            # 显示使用统计
            stats = manager.get_usage_stats()
            print(f"\\n使用统计: {stats}")

        print("✅ API Key管理器工作正常\\n")

    except Exception as e:
        print(f"❌ API Key管理器演示失败: {e}")
        print("请先运行: python3 init_etherscan_accounts.py\\n")

def demo_polygon_client_structure():
    """演示Polygon客户端结构（不发送真实请求）"""
    print("🌐 Polygon客户端结构演示")
    print("=" * 50)

    print("PolygonClient 功能:")
    print("  • 使用Etherscan API V2访问Polygon链")
    print("  • 支持ERC-1155 TransferSingle事件抓取")
    print("  • 支持conditionId和tokenId过滤")
    print("  • API Key自动轮询，避免限额中断")
    print("  • 线程安全，支持并发访问")

    print("\\n核心方法:")
    print("  • get_logs(condition_id=None, token_id=None, limit=20)")
    print("    - 获取ERC-1155交易日志")
    print("    - 支持按conditionId或tokenId过滤")
    print("    - 返回最近的交易记录")

    print("\\n使用示例:")
    print("```python")
    print("# 初始化客户端")
    print("from polygon import PolygonClient")
    print("client = PolygonClient(['your_api_key_1', 'your_api_key_2'])")
    print("")
    print("# 获取最近20条交易")
    print("logs = client.get_logs(limit=20)")
    print("")
    print("# 按conditionId过滤")
    print("condition_logs = client.get_logs(condition_id=12345, limit=10)")
    print("")
    print("# 按tokenId过滤")
    print("token_logs = client.get_logs(token_id=67890, limit=10)")
    print("```")

def show_real_usage_example():
    """显示真实使用的完整示例"""
    print("🚀 完整使用示例")
    print("=" * 50)

    usage_code = '''
# 1. 配置环境变量 (.env文件)
POLYGONSCAN_API_KEYS=["YOUR_API_KEY_1", "YOUR_API_KEY_2"]

# 2. 使用代码示例
from polygon import PolygonClient
from config import config

# 方法1: 使用配置中的API Keys
client = PolygonClient()

# 方法2: 直接传入API Keys
api_keys = ["your_key_1", "your_key_2"]
client = PolygonClient(api_keys)

# 3. 抓取Polymarket交易数据
try:
    # 获取最近交易
    recent_logs = client.get_logs(limit=20)

    # 按conditionId过滤
    condition_logs = client.get_logs(condition_id=12345, limit=10)

    # 按tokenId过滤
    token_logs = client.get_logs(token_id=67890, limit=10)

    # 处理结果
    for log in recent_logs:
        print(f"Block: {log['blockNumber']}")
        print(f"TxHash: {log['txHash']}")
        print(f"From: {log['from']}")
        print(f"To: {log['to']}")
        print(f"TokenId: {log['tokenId']}")
        print(f"Value: {log['value']}")
        print(f"ConditionId: {log['conditionId']}")
        print("---")

except Exception as e:
    print(f"错误: {e}")
'''

    print(usage_code)

def show_configuration_guide():
    """显示配置指南"""
    print("⚙️ 配置指南")
    print("=" * 50)

    print("1. 初始化数据库:")
    print("   python3 init_etherscan_accounts.py")

    print("\\n2. 获取Polygonscan API Key:")
    print("   - 访问: https://polygonscan.com/apis")
    print("   - 注册账号并申请免费API Key")
    print("   - 每日限额: 5次/秒, 100,000次/天")

    print("\\n3. 添加API Keys到数据库:")
    print("   编辑 init_etherscan_accounts.py 中的 sample_keys 列表")
    print("   填入真实的API Keys")
    print("   重新运行: python3 init_etherscan_accounts.py")

    print("\\n4. 多API Key轮询优势:")
    print("   - 自动切换，避免单Key限额")
    print("   - 提高抓取成功率")
    print("   - 支持高频数据采集")

    print("\\n5. 测试验证:")
    print("   python3 demo_usage.py")

if __name__ == "__main__":
    print("🎯 Polygon Polymarket 数据抓取系统演示\\n")

    # 演示各个组件
    demo_api_key_manager()
    demo_polygon_client_structure()
    show_real_usage_example()
    show_configuration_guide()

    print("\\n✨ 演示完成！请配置API Keys后进行真实测试")
