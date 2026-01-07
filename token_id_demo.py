#!/usr/bin/env python3
"""
演示Token ID的生成过程
"""

from web3 import Web3
import json

def generate_token_ids(condition_id, num_outcomes=2):
    """
    从conditionId生成Token IDs
    """
    w3 = Web3()

    print("🔬 Token ID生成过程演示")
    print("=" * 35)

    # 移除0x前缀
    condition_id_clean = condition_id[2:] if condition_id.startswith('0x') else condition_id
    print(f"🔑 Condition ID: {condition_id}")
    print(f"   清理后: {condition_id_clean}")
    print(f"   长度: {len(condition_id_clean)} 字符")

    token_ids = []
    for i in range(num_outcomes):
        # 将conditionId和outcomeIndex拼接
        data = bytes.fromhex(condition_id_clean) + i.to_bytes(1, 'big')
        print(f"\n🧮 生成结果 {i} 的Token ID:")
        print(f"   拼接数据: conditionId + {i}")
        print(f"   字节长度: {len(data)} 字节")

        # 计算keccak256哈希
        token_id_hex = w3.keccak(data)
        token_id_int = int.from_bytes(token_id_hex, 'big')

        print(f"   keccak256结果: {token_id_hex.hex()}")
        print(f"   Token ID (整数): {token_id_int}")
        print(f"   Token ID (字符串): {str(token_id_int)}")

        token_ids.append(str(token_id_int))

    return token_ids

def demonstrate_with_real_data():
    """
    使用实际数据演示
    """
    # 从实际JSON文件中读取数据
    with open('data/polymarket_markets_Politics_20260106_162416.json', 'r') as f:
        data = json.load(f)

    market = data['markets'][0]
    condition_id = market['conditionId']

    print(f"\n🏷️  市场: {market['question'][:50]}...")
    print(f"🔑 Condition ID: {condition_id}")

    # 生成Token IDs
    generated_token_ids = generate_token_ids(condition_id, 2)

    # 从数据中获取实际的Token IDs
    actual_token_ids = market['clob_token_ids']

    print(f"\n📊 对比结果:")
    print(f"=" * 20)
    outcomes = ['Yes', 'No']

    for i in range(2):
        outcome = outcomes[i]
        generated = generated_token_ids[i]
        actual = actual_token_ids[i]

        match = "✅ 匹配" if generated == actual else "❌ 不匹配"
        print(f"\n{outcome}代币:")
        print(f"   生成的: {generated}")
        print(f"   实际的: {actual}")
        print(f"   结果: {match}")

def explain_erc1155_concept():
    """
    解释ERC-1155概念
    """
    print("\n📚 ERC-1155标准详解")
    print("=" * 25)

    print("🏗️  什么是ERC-1155?")
    print("   • 以太坊代币标准")
    print("   • 支持多种代币在一个合约中")
    print("   • 比ERC-20更高效")

    print("\n🆔 Token ID的作用:")
    print("   • 唯一标识代币类型")
    print("   • 一个合约可管理无数种代币")
    print("   • 支持批量转移操作")

    print("\n🎯 Polymarket的应用:")
    print("   • 每个预测市场 = 一个conditionId")
    print("   • 每种结果 = 一个Token ID")
    print("   • 结算时自动执行")

def main():
    try:
        demonstrate_with_real_data()
        explain_erc1155_concept()

        print("\n💡 使用建议:")
        print("   • Token ID用于查询交易记录")
        print("   • 在PolygonScan中按Token ID过滤")
        print("   • 可以分析市场交易行为")

    except FileNotFoundError:
        print("❌ 找不到数据文件，请确保JSON文件存在")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
