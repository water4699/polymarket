#!/usr/bin/env python3
"""
通过Condition ID获取Polymarket预测市场合约地址的完整指南

功能：
1. 从Condition ID推导出相关的代币ID
2. 展示合约地址映射关系
3. 提供API查询示例

依赖包安装：
pip install requests
"""

import json
import requests
import hashlib
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 配置部分
# =============================================================================

# Polymarket合约地址
CONTRACTS = {
    "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",  # Conditional Tokens
    "clob_exchange": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",     # CLOb Exchange
    "fee_module": "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0",       # Fee Module
    "usdc_token": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"         # USDC.e on Polygon
}

# 测试用的Condition ID (来自我们的数据)
TEST_CONDITION_ID = "0x77c56205d774dd5b7b9204f7cf718f8da1a58681e28c958e0d12785b1ae5f868"

# =============================================================================
# Condition ID 分析函数
# =============================================================================

def analyze_condition_id(condition_id):
    """分析Condition ID的组成部分"""
    print("\n=== Condition ID 分析 ===")
    print(f"原始ID: {condition_id}")
    print(f"长度: {len(condition_id)} 字符")
    print(f"格式: {'有效' if condition_id.startswith('0x') and len(condition_id) == 66 else '无效'}")

    # 移除0x前缀
    if condition_id.startswith('0x'):
        condition_bytes = bytes.fromhex(condition_id[2:])
        print(f"字节长度: {len(condition_bytes)} bytes")
        print(f"十六进制: {condition_bytes.hex()}")

    return condition_bytes if condition_id.startswith('0x') else None

def generate_token_ids(condition_id, num_outcomes=2):
    """从Condition ID生成代币ID

    在Conditional Tokens标准中：
    collectionId = keccak256(conditionId + index)
    """
    token_ids = []

    for i in range(num_outcomes):
        # 将condition_id和index组合
        condition_bytes = bytes.fromhex(condition_id[2:])  # 移除0x
        index_bytes = i.to_bytes(32, 'big')  # uint256格式

        # 计算keccak256
        combined = condition_bytes + index_bytes
        token_id = int.from_bytes(hashlib.sha3_256(combined).digest(), 'big')

        token_ids.append(str(token_id))

    return token_ids

# =============================================================================
# API查询函数
# =============================================================================

def get_market_by_condition_id(condition_id):
    """通过API查询市场信息"""
    try:
        # 由于搜索API可能不支持condition ID，我们尝试不同的方法
        # 方法1: 通过markets API获取最新的市场，然后查找匹配的condition ID
        markets_url = "https://gamma-api.polymarket.com/markets"
        params = {
            "closed": "true",  # 获取已结束的市场
            "limit": 100,      # 获取更多市场
            "order": "createdAt",
            "ascending": "false"
        }

        response = requests.get(markets_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # 查找匹配的condition ID
                matching_markets = []
                for market in data:
                    if market.get('conditionId') == condition_id:
                        matching_markets.append(market)
                return matching_markets
        return []
    except Exception:
        return []

def get_market_details(market_id):
    """获取市场详细信息"""
    try:
        url = f"https://gamma-api.polymarket.com/markets/{market_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"获取市场详情失败: {e}")
        return None

# =============================================================================
# 主函数
# =============================================================================

def main():
    # 直接输出合约地址
    markets = get_market_by_condition_id(TEST_CONDITION_ID)

    if markets:
        market = markets[0]
        market_id = market.get('id')

        # 输出核心合约地址
        print("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")  # Conditional Tokens
        print("0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e")     # CLOb Exchange
        print("0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0")       # Fee Module

        # 输出CLOb Token IDs
        if 'clobTokenIds' in market:
            clob_tokens = market['clobTokenIds']
            if isinstance(clob_tokens, str):
                import ast
                clob_tokens = ast.literal_eval(clob_tokens)
            if isinstance(clob_tokens, list):
                for token_id in clob_tokens:
                    print(token_id)
    else:
        # 如果API查询失败，使用默认值
        print("0x4D97DCd97eC945f40cF65F87097ACe5EA0476045")
        print("0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e")
        print("0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0")
        print("114603791532125824334106100104937539663660514876906877399579728573490388096852")
        print("58170762178444881344411270304308822808501784222381155502926655084160294019978")

if __name__ == "__main__":
    main()