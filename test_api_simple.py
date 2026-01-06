#!/usr/bin/env python3
"""
简化版API测试 - 只测试基本功能
"""

from modules.api_key_manager import EtherscanAPIManager

# 数据库连接 URL
DATABASE_URL = "postgresql://predictlab_user:your_password@localhost:5432/polymarket"

def main():
    print("🧪 简化版API测试")
    print("=" * 40)

    try:
        # 创建管理器
        manager = EtherscanAPIManager(DATABASE_URL)
        print("✅ 管理器创建成功")

        # 测试获取可用API
        api_config = manager.get_available_api()
        if api_config:
            print(f"✅ 获取API配置成功: {api_config['api_key'][:10]}...")
        else:
            print("❌ 无法获取API配置")
            return

        # 测试简单的balance查询 (不需要代理，网络限制小)
        print("\n🧪 测试balance查询...")
        test_params = {
            'chainid': 1,
            'module': 'account',
            'action': 'balance',
            'address': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'  # Vitalik地址
        }

        response = manager.make_api_request(test_params)

        if response and response.get("status") == "1":
            print("✅ Balance查询成功!")
            balance_wei = int(response.get('result', 0))
            balance_eth = balance_wei / 10**18
            print(f"余额: {balance_eth:.6f}")
        elif response and response.get("status") == "0":
            error_msg = response.get("message", "Unknown error")
            print(f"❌ API返回错误: {error_msg}")

            if "notok" in error_msg.lower():
                print("🔍 NOTOK错误诊断:")
                print("   - API key可能无效")
                print("   - 账户可能被限制")
                print("   - 试试更换API key")
        else:
            print("❌ 请求完全失败")

    except Exception as e:
        print(f"❌ 测试异常: {e}")

if __name__ == "__main__":
    main()

