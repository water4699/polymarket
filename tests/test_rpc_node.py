#!/usr/bin/env python3
"""
Polygon RPC节点测试脚本
测试你搭建的RPC节点的所有功能
"""

import asyncio
import json
import time
from typing import Dict, Any
import requests
from web3 import Web3
from config import config

class RPCNodeTester:
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url or config.api.WEB3_PROVIDER_URL
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        print(f"🔗 测试RPC节点: {self.rpc_url}")

    def make_request(self, method: str, params: list = None) -> Dict[str, Any]:
        """发送JSON-RPC请求"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }

        try:
            response = requests.post(self.rpc_url, json=payload, timeout=10)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始全面测试Polygon RPC节点...\n")

        tests = [
            self.test_connection,
            self.test_basic_info,
            self.test_block_info,
            self.test_gas_price,
            self.test_network_info,
            self.test_performance,
            self.test_contract_call
        ]

        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
                print()
            except Exception as e:
                print(f"❌ 测试失败: {e}")
                results.append(False)
                print()

        # 总结
        passed = sum(1 for r in results if r)
        total = len(results)
        print(f"📊 测试结果: {passed}/{total} 通过")

        if passed == total:
            print("🎉 所有测试通过！RPC节点运行正常")
        else:
            print("⚠️  部分测试失败，请检查节点状态")

    async def test_connection(self):
        """测试基本连接"""
        print("🔗 测试1: 基本连接")
        try:
            is_connected = self.web3.is_connected()
            if is_connected:
                print("✅ 连接成功")
                return True
            else:
                print("❌ 连接失败")
                return False
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False

    async def test_basic_info(self):
        """测试基本信息"""
        print("📋 测试2: 基本信息")

        # 客户端版本
        try:
            version = self.make_request("web3_clientVersion")
            if "result" in version:
                print(f"✅ 客户端版本: {version['result']}")
            else:
                print(f"❌ 获取版本失败: {version}")
                return False
        except Exception as e:
            print(f"❌ 版本检查失败: {e}")
            return False

        # 协议版本
        try:
            protocol = self.make_request("eth_protocolVersion")
            if "result" in protocol:
                print(f"✅ 协议版本: {protocol['result']}")
            else:
                print(f"❌ 获取协议版本失败: {protocol}")
                return False
        except Exception as e:
            print(f"❌ 协议版本检查失败: {e}")
            return False

        return True

    async def test_block_info(self):
        """测试区块信息"""
        print("📦 测试3: 区块信息")

        # 最新区块号
        try:
            block_number = self.make_request("eth_blockNumber")
            if "result" in block_number:
                block_num = int(block_number['result'], 16)
                print(f"✅ 最新区块: {block_num} (0x{block_number['result']})")
            else:
                print(f"❌ 获取区块号失败: {block_number}")
                return False
        except Exception as e:
            print(f"❌ 区块号检查失败: {e}")
            return False

        # 获取最新区块详情
        try:
            block_detail = self.make_request("eth_getBlockByNumber", ["latest", False])
            if "result" in block_detail and block_detail['result']:
                block = block_detail['result']
                print(f"✅ 区块哈希: {block.get('hash', 'N/A')[:20]}...")
                print(f"✅ 交易数量: {len(block.get('transactions', []))}")
                print(f"✅ Gas使用: {int(block.get('gasUsed', '0x0'), 16)}")
            else:
                print("⚠️  获取区块详情失败，可能还在同步中")
        except Exception as e:
            print(f"❌ 区块详情检查失败: {e}")

        return True

    async def test_gas_price(self):
        """测试Gas价格"""
        print("⛽ 测试4: Gas价格")

        try:
            gas_price = self.make_request("eth_gasPrice")
            if "result" in gas_price:
                price_wei = int(gas_price['result'], 16)
                price_gwei = price_wei / 1e9
                print(f"✅ Gas价格: {price_gwei:.2f} Gwei")
            else:
                print(f"❌ 获取Gas价格失败: {gas_price}")
                return False
        except Exception as e:
            print(f"❌ Gas价格检查失败: {e}")
            return False

        return True

    async def test_network_info(self):
        """测试网络信息"""
        print("🌐 测试5: 网络信息")

        # 网络ID
        try:
            network_id = self.make_request("net_version")
            if "result" in network_id:
                print(f"✅ 网络ID: {network_id['result']}")
            else:
                print(f"❌ 获取网络ID失败: {network_id}")
                return False
        except Exception as e:
            print(f"❌ 网络ID检查失败: {e}")
            return False

        # 对等节点数量
        try:
            peers = self.make_request("net_peerCount")
            if "result" in peers:
                peer_count = int(peers['result'], 16)
                print(f"✅ 对等节点: {peer_count}")
            else:
                print(f"❌ 获取对等节点失败: {peers}")
        except Exception as e:
            print(f"❌ 对等节点检查失败: {e}")

        # 同步状态
        try:
            sync_status = self.make_request("eth_syncing")
            if "result" in sync_status:
                if sync_status['result']:
                    sync = sync_status['result']
                    print(f"✅ 正在同步: 区块 {sync.get('currentBlock', 'N/A')} / {sync.get('highestBlock', 'N/A')}")
                else:
                    print("✅ 同步完成")
            else:
                print("⚠️  获取同步状态失败")
        except Exception as e:
            print(f"❌ 同步状态检查失败: {e}")

        return True

    async def test_performance(self):
        """测试性能"""
        print("⚡ 测试6: 性能测试")

        # 测试响应时间
        try:
            start_time = time.time()
            for _ in range(5):
                self.make_request("eth_blockNumber")
            end_time = time.time()
            avg_response_time = (end_time - start_time) / 5 * 1000
                print(f"✅ 平均响应时间: {avg_response_time:.2f}ms")
            if avg_response_time < 100:
                print("✅ 性能良好")
            elif avg_response_time < 500:
                print("⚠️  性能一般")
            else:
                print("❌ 性能较差")
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            return False

        return True

    async def test_contract_call(self):
        """测试合约调用"""
        print("📄 测试7: 合约调用测试")

        # Polygon上的一个知名合约地址 (WMATIC)
        wmatic_address = "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270"

        try:
            # 获取合约代码
            code = self.make_request("eth_getCode", [wmatic_address, "latest"])
            if "result" in code and code['result'] != "0x":
                print(f"✅ 合约存在: {wmatic_address}")
                print(f"✅ 合约代码长度: {len(code['result'])} 字符")
            else:
                print(f"⚠️  合约检查失败: {code}")
        except Exception as e:
            print(f"❌ 合约调用测试失败: {e}")
            return False

        return True

def print_usage():
    """打印使用说明"""
    print("""
🧪 Polygon RPC节点测试工具

用法:
    python3 test_rpc_node.py                    # 使用默认配置
    python3 test_rpc_node.py http://your-rpc-url:8545  # 指定URL

测试内容:
    1. 🔗 基本连接测试
    2. 📋 客户端和协议信息
    3. 📦 区块信息查询
    4. ⛽ Gas价格查询
    5. 🌐 网络信息和同步状态
    6. ⚡ 性能响应时间测试
    7. 📄 智能合约调用测试

示例输出:
    ✅ 表示测试通过
    ❌ 表示测试失败
    ⚠️  表示警告或部分成功
    """)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    # 获取RPC URL
    rpc_url = sys.argv[1] if len(sys.argv) > 1 else None

    # 运行测试
    tester = RPCNodeTester(rpc_url)

    try:
        asyncio.run(tester.run_all_tests())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
