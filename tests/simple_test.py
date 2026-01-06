#!/usr/bin/env python3
"""
简单的Polygon RPC节点测试脚本
"""

import requests
import json

def test_rpc_node(rpc_url="http://161.97.152.72:8545"):
    """测试RPC节点功能"""
    print(f"🧪 测试RPC节点: {rpc_url}")
    print("=" * 50)

    def make_request(method, params=None):
        """发送JSON-RPC请求"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        try:
            response = requests.post(rpc_url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    tests = [
        ("🔗 连接测试", "net_version", []),
        ("📦 区块高度", "eth_blockNumber", []),
        ("⛽ Gas价格", "eth_gasPrice", []),
        ("📋 客户端版本", "web3_clientVersion", []),
        ("🌐 同步状态", "eth_syncing", []),
    ]

    passed = 0
    total = len(tests)

    for name, method, params in tests:
        print(f"\n{name}:")
        result = make_request(method, params)

        if "error" in result:
            print(f"  ❌ 失败: {result['error']}")
        elif "result" in result:
            if method == "eth_blockNumber":
                block_num = int(result['result'], 16)
                print(f"  ✅ 区块: {block_num}")
            elif method == "eth_gasPrice":
                gas_price = int(result['result'], 16) / 1e9
                print(f"  ✅ Gas价格: {gas_price:.2f} Gwei")
            elif method == "eth_syncing":
                if result['result']:
                    print("  ⚠️  正在同步区块数据")
                else:
                    print("  ✅ 同步完成")
            else:
                print(f"  ✅ {result['result']}")
            passed += 1
        else:
            print(f"  ❌ 无效响应: {result}")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！RPC节点运行正常")
        return True
    else:
        print("⚠️  部分测试失败，请检查节点状态")
        return False

if __name__ == "__main__":
    import sys

    rpc_url = sys.argv[1] if len(sys.argv) > 1 else "http://161.97.152.72:8545"

    try:
        test_rpc_node(rpc_url)
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
