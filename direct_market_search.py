#!/usr/bin/env python3
"""
直接通过markets API搜索比特币涨跌市场
"""

import requests
import json
import os
from datetime import datetime

# 配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PolymarketBot/1.0)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://polymarket.com",
    "Referer": "https://polymarket.com/"
}

GAMMA_BASE = "https://gamma-api.polymarket.com"
DATA_DIR = "data"

def search_btc_market():
    """搜索比特币涨跌市场"""
    url = f"{GAMMA_BASE}/markets"
    
    # 搜索参数 - 扩大搜索范围
    params = {
        "active": "false",  # 包括已结束的市场
        "closed": "true",   # 包括已关闭的市场
        "limit": 1000,      # 增加搜索范围
        "order": "createdAt",
        "ascending": "false"  # 最新的在前
    }
    
    print("🔍 搜索比特币涨跌市场...")
    
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        all_markets = r.json()
        
        print(f"📊 获取到 {len(all_markets)} 个市场，开始筛选...")
        
        # 筛选比特币涨跌市场
        btc_markets = []
        for market in all_markets:
            question = market.get('question', '').lower()
            slug = market.get('slug', '')
            
            # 匹配条件
            is_btc = 'bitcoin' in question or 'btc' in question
            is_updown = 'up or down' in question or 'up down' in question or 'up/down' in question
            has_time = '12:30' in question or '12:45' in question or 'january 7' in question
            
            if is_btc and (is_updown or has_time):
                end_date = market.get('endDate', '')
                # 检查是否是2026年1月7日的市场
                if '2026-01-07' in end_date:
                    btc_markets.append(market)
                    print(f"✅ 找到潜在匹配: {market['question'][:60]}...")
                    print(f"   ID: {market.get('id')}, Slug: {slug}")
                    print(f"   结束时间: {end_date}")
                    print(f"   交易量: ${market.get('volumeNum', 0):,.0f}")
                    print()
        
        if btc_markets:
            print(f"🎯 找到 {len(btc_markets)} 个匹配的市场")
            return btc_markets[0]  # 返回第一个匹配的市场
        else:
            print("❌ 未找到匹配的比特币涨跌市场")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 搜索失败: {e}")
        return None

def get_contract_addresses(market):
    """获取市场的合约地址信息"""
    contract_info = {}
    
    # Conditional Tokens条件ID
    condition_id = market.get("conditionId")
    if condition_id:
        contract_info["condition_id"] = condition_id
        # 在conditionId字段下添加合约地址信息
        contract_info["contract_addresses"] = {
            "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
            "clob_exchange": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e", 
            "fee_module": "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"
        }
    
    # CLOb Token IDs
    clob_tokens = market.get("clobTokenIds")
    if clob_tokens:
        try:
            # 解析JSON字符串
            if isinstance(clob_tokens, str):
                clob_tokens = json.loads(clob_tokens)
            contract_info["clob_token_ids"] = clob_tokens
        except:
            contract_info["clob_token_ids"] = clob_tokens
    
    return contract_info

def save_market_data(market_data, filename):
    """保存市场数据到文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    
    data_to_save = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source_url": "https://polymarket.com/event/btc-updown-15m-1767763800?tid=1767767121687",
            "fetch_method": "markets_api_direct_search"
        },
        "market": market_data
    }
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        print(f"💾 数据已保存到: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None

def display_market_info(market):
    """显示市场信息"""
    print("\n" + "="*60)
    print("📊 比特币涨跌预测市场详情")
    print("="*60)
    
    print(f"🆔 Market ID: {market.get('id', 'N/A')}")
    print(f"🔗 Slug: {market.get('slug', 'N/A')}")
    print(f"❓ 问题: {market.get('question', 'N/A')}")
    
    # 时间信息
    created_at = market.get('createdAt', 'N/A')
    end_date = market.get('endDate', 'N/A')
    print(f"📅 创建时间: {created_at}")
    print(f"🏁 结束时间: {end_date}")
    
    # 交易信息
    volume = market.get('volumeNum', 0)
    liquidity = market.get('liquidityNum', 0)
    print(f"💰 交易量: ${volume:,.0f}")
    print(f"💧 流动性: ${liquidity:,.0f}")
    
    # 状态信息
    active = market.get('active', False)
    closed = market.get('closed', False)
    status = "活跃" if active else ("已关闭" if closed else "未知")
    print(f"📊 状态: {status}")
    
    # 结果信息
    outcomes = market.get('outcomes', [])
    outcome_prices = market.get('outcomePrices', [])
    print("\n🎯 选项赔率:")
    for i, outcome in enumerate(outcomes):
        try:
            price = float(outcome_prices[i]) if i < len(outcome_prices) else 0
            print(f"  • {outcome}: {price:.4f} ({price*100:.1f}%)")
        except:
            print(f"  • {outcome}: 暂无赔率")
    
    # 合约信息
    condition_id = market.get('conditionId', 'N/A')
    clob_tokens = market.get('clobTokenIds', 'N/A')
    print("\n🔗 合约信息:")
    print(f"  • Condition ID: {condition_id}")
    print(f"  • CLOb Token IDs: {clob_tokens}")
    
    # 合约地址
    contract_info = get_contract_addresses(market)
    if contract_info.get('contract_addresses'):
        print("\n🏛️ Polymarket合约地址:")
        for name, address in contract_info['contract_addresses'].items():
            print(f"  • {name}: {address}")

def main():
    """主函数"""
    print("🚀 直接搜索比特币涨跌市场")
    print("="*35)
    
    # 搜索市场
    market = search_btc_market()
    
    if market:
        # 添加合约地址信息
        contract_info = get_contract_addresses(market)
        market.update(contract_info)
        
        # 显示信息
        display_market_info(market)
        
        # 保存数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"btc_updown_market_found_{timestamp}.json"
        save_market_data(market, filename)
        
        print("\n✅ 市场数据获取完成！")
        print(f"📄 数据已保存到: data/{filename}")
        
        # 为Polygon交易获取做准备
        print("\n🔗 Polygon交易获取准备:")
        print("   • 使用上面的合约地址和Token IDs")
        print("   • 时间范围: 市场创建时间到结束时间")
        print("   • 需要获取: ERC-1155转账, ERC-20转账, 合约调用")
        
        return market
    else:
        print("❌ 未找到比特币涨跌市场")
        print("💡 可能原因:")
        print("   • 该市场可能不存在或已被删除")
        print("   • 时间范围或问题描述不匹配")
        print("   • API返回的数据格式已改变")
        return None

if __name__ == "__main__":
    main()
