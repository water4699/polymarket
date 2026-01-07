#!/usr/bin/env python3
"""
查询特定Polymarket市场交易记录的工具
"""

import json
import webbrowser
from datetime import datetime

def load_market_data(json_file):
    """加载市场数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['markets'][0]  # 获取第一个市场

def analyze_market(market):
    """分析市场数据"""
    print("🔍 市场分析报告")
    print("=" * 50)

    # 基本信息
    print(f"🏷️  市场ID: {market['id']}")
    print(f"❓ 问题: {market['question']}")
    print(f"📊 成交量: ${market['volumeNum']:,.2f} USDC")
    print(f"🏦 流动性: ${market['liquidityNum']:.2f}")
    print(f"📅 创建时间: {market['createdAt'][:19].replace('T', ' ')}")
    print(f"🏁 结束时间: {market['endDate'][:19].replace('T', ' ')}")
    print(f"🔒 状态: {'已结束' if market['closed'] else '进行中'}")

    # 结果信息
    outcomes = json.loads(market['outcomes'])
    outcome_prices = json.loads(market['outcomePrices'])
    print(f"🎯 结果选项: {outcomes}")
    print(f"💰 当前价格: {outcome_prices}")

    # 区块链信息
    print("\n🔗 区块链信息:")
    print(f"   📍 网络: Polygon (Matic)")
    print(f"   📄 合约地址: {market['contract_addresses']['conditional_tokens']}")
    print(f"   🔑 Condition ID: {market['conditionId']}")

    # Token IDs
    token_ids = market['clob_token_ids']
    print("\n🪙 Token IDs:")
    for i, token_id in enumerate(token_ids):
        outcome = outcomes[i] if i < len(outcomes) else f"Option {i+1}"
        print(f"   {'✅' if outcome == 'Yes' else '❌'} {outcome}: {token_id}")

def generate_query_links(market):
    """生成查询链接"""
    contract_address = market['contract_addresses']['conditional_tokens']
    token_ids = market['clob_token_ids']
    outcomes = json.loads(market['outcomes'])

    print("\n🌐 PolygonScan查询链接:")
    print("=" * 40)

    for i, token_id in enumerate(token_ids):
        outcome = outcomes[i] if i < len(outcomes) else f"Option {i+1}"
        emoji = "✅" if outcome == "Yes" else "❌"

        link = f"https://polygonscan.com/token/{contract_address}?a={token_id}"
        print(f"\n{emoji} {outcome}代币查询:")
        print(f"🔗 {link}")

def open_in_browser(market):
    """在浏览器中打开查询页面"""
    contract_address = market['contract_addresses']['conditional_tokens']
    token_ids = market['clob_token_ids']
    outcomes = json.loads(market['outcomes'])

    print("\n🔍 正在浏览器中打开查询页面...")
    for i, token_id in enumerate(token_ids):
        outcome = outcomes[i] if i < len(outcomes) else f"Option {i+1}"
        link = f"https://polygonscan.com/token/{contract_address}?a={token_id}"
        print(f"📂 打开{outcome}代币查询...")
        webbrowser.open(link)

    # 同时打开合约页面
    contract_link = f"https://polygonscan.com/address/{contract_address}"
    print("🏛️ 打开合约总览页面...")
    webbrowser.open(contract_link)

def main():
    json_file = "data/polymarket_markets_Politics_20260106_162416.json"

    try:
        market = load_market_data(json_file)
        analyze_market(market)
        generate_query_links(market)

        print("\n🚀 选项:")
        print("1. 在浏览器中打开所有查询页面")
        print("2. 只显示链接（不打开浏览器）")
        print("3. 退出")

        choice = input("\n请选择 (1/2/3): ").strip()

        if choice == "1":
            open_in_browser(market)
        elif choice == "2":
            print("\n📋 链接已生成，请手动复制使用")
        else:
            print("👋 再见!")

    except FileNotFoundError:
        print(f"❌ 找不到文件: {json_file}")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
