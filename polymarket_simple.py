#!/usr/bin/env python3
"""
Polymarket 简化版 - 只获取真实的体育预测市场
"""

import requests
import json
import time
import sys
sys.path.append('.')
from polymarket_latest import get_contract_addresses
from datetime import datetime

# API配置
GAMMA_BASE = "https://gamma-api.polymarket.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; PolymarketBot/1.0)',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Origin': 'https://polymarket.com',
    'Referer': 'https://polymarket.com/'
}

def fetch_real_sports_markets(limit=3):
    """获取真实的体育预测市场数据（从Markets API）"""
    print("🏆 获取真实的体育预测市场...")

    # 体育关键词，用于识别体育市场
    sports_keywords = [
        # 联赛名称
        'premier league', 'championship', 'fa cup', 'carabao cup', 'efl cup',
        'bundesliga', 'la liga', 'serie a', 'ligue 1', 'eredivisie',
        'mls', 'nba', 'nfl', 'mlb', 'nhl', 'wnba', 'ncaab', 'ncaaf',
        # 球队关键词
        'fc', 'united', 'city', 'liverpool', 'chelsea', 'arsenal', 'tottenham',
        'manchester', 'barcelona', 'real madrid', 'bayern', 'psg', 'juventus',
        'lakers', 'celtics', 'warriors', 'bulls', 'heat', 'bucks',
        # 比赛关键词
        'vs', 'vs.', 'versus', 'at ', '@ ',
        # 体育术语
        'soccer', 'football', 'basketball', 'baseball', 'hockey', 'tennis'
    ]

    # 排除非体育关键词
    exclude_keywords = [
        'biden', 'trump', 'election', 'president', 'political', 'government',
        'crypto', 'bitcoin', 'ethereum', 'trading', 'market cap', 'price',
        'yang', 'walz', 'harris', 'nomination', 'press conference'
    ]

    markets = []

    try:
        # 从Markets API获取活跃的体育市场
        markets_url = f"{GAMMA_BASE}/markets"
        params = {
            "active": "true",
            "closed": "false",
            "limit": 200,  # 获取更多市场以找到体育市场
            "order": "volumeNum",
            "ascending": "false"
        }

        r = requests.get(markets_url, headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        all_markets = r.json()

        print(f"📊 从 {len(all_markets)} 个活跃市场中筛选体育市场...")

        # 筛选体育市场
        for market in all_markets:
            if len(markets) >= limit:
                break

            question = market.get("question", "").lower()
            description = market.get("description", "").lower()

            # 检查是否包含体育关键词
            has_sports_keyword = any(keyword in question for keyword in sports_keywords)

            # 排除非体育内容
            has_exclude_keyword = any(exclude in question or exclude in description for exclude in exclude_keywords)

            # 额外的体育验证：检查是否有体育相关的outcome选项
            outcomes = market.get("outcomes", [])
            has_team_names = False
            if outcomes and isinstance(outcomes, list):
                # 检查outcome中是否包含球队名称
                outcome_text = " ".join(str(o) for o in outcomes).lower()
                has_team_names = any(team in outcome_text for team in ['fc', 'united', 'city', 'liverpool', 'chelsea', 'lakers', 'celtics'])

            if has_sports_keyword and not has_exclude_keyword and (has_team_names or 'vs' in question):
                # 验证这是否是真正的体育市场（有赔率和交易量）
                volume = market.get("volumeNum", 0)
                outcome_prices = market.get("outcomePrices", [])
                liquidity = market.get("liquidityNum", 0)

                if volume > 1000 and outcome_prices and len(outcome_prices) >= 2:  # 有实际交易的体育市场
                    market_copy = market.copy()
                    market_copy["data_source"] = "markets_api"
                    market_copy["sport_type"] = "Sports"

                    # 添加真实的合约地址信息
                    contract_info = get_contract_addresses(market_copy)
                    if contract_info:
                        market_copy.update(contract_info)

                    markets.append(market_copy)
                    print(f"✅ 发现体育市场: {market['question'][:50]}... (交易量: {volume})")

        # 如果活跃市场不够，补充一些已结束但仍有价值的体育市场
        if len(markets) < limit:
            print(f"🔄 活跃体育市场不足({len(markets)}/{limit})，补充已结束市场...")

            params_closed = {
                "closed": "true",
                "limit": 100,
                "order": "volumeNum",
                "ascending": "false"
            }

            r_closed = requests.get(markets_url, headers=HEADERS, params=params_closed, timeout=15)
            r_closed.raise_for_status()
            closed_markets = r_closed.json()

            for market in closed_markets:
                if len(markets) >= limit:
                    break

                question = market.get("question", "").lower()
                description = market.get("description", "").lower()

                has_sports_keyword = any(keyword in question for keyword in sports_keywords)
                has_exclude_keyword = any(exclude in question or exclude in description for exclude in exclude_keywords)

                volume = market.get("volumeNum", 0)
                outcome_prices = market.get("outcomePrices", [])

                # 对于已结束市场，降低交易量要求
                if has_sports_keyword and not has_exclude_keyword and volume > 5000 and outcome_prices:
                    # 避免重复
                    if not any(m.get("id") == market.get("id") for m in markets):
                        market_copy = market.copy()
                        market_copy["data_source"] = "markets_api_closed"
                        market_copy["sport_type"] = "Sports"

                        # 添加真实的合约地址信息
                        contract_info = get_contract_addresses(market_copy)
                        if contract_info:
                            market_copy.update(contract_info)

                        markets.append(market_copy)
                        print(f"✅ 补充已结束体育市场: {market['question'][:50]}... (交易量: {volume})")

        if markets:
            complete_markets = [m for m in markets if m.get("outcomes") and m.get("outcomePrices")]
            print(f"✅ 成功获取 {len(markets)} 个真实体育预测市场（{len(complete_markets)} 个有完整赔率）")
            return markets
        else:
            print("❌ 未找到任何真实的体育预测市场")
            print("💡 可能原因: 当前时间段没有活跃的体育赛事预测市场")
            return []

    except Exception as e:
        print(f"❌ 体育市场获取失败: {e}")
        return []

def save_sports_markets_to_file(markets):
    """保存体育市场数据到文件"""
    if not markets:
        print("⚠️ 没有体育市场数据可保存")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/polymarket_markets_Sports_{timestamp}.json"

    data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_markets": len(markets)
        },
        "markets": markets
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 数据已保存到 {filename}")

def main():
    """主函数"""
    print("🚀 Polymarket 体育市场抓取工具")
    print("=" * 50)

    # 获取真实的体育预测市场
    sports_markets = fetch_real_sports_markets(limit=5)

    if sports_markets:
        # 保存数据
        save_sports_markets_to_file(sports_markets)

        # 显示结果
        print("\n📊 获取到的体育市场:")
        print("-" * 40)
        for i, market in enumerate(sports_markets, 1):
            print(f"{i}. {market['question']}")
            print(f"   交易量: {market.get('volumeNum', 0)}")
            print(f"   状态: {'活跃' if market.get('active') else '已结束'}")
            outcomes = market.get('outcomes', [])
            if outcomes:
                print(f"   选项: {', '.join(outcomes[:2])}")
            print()
    else:
        print("❌ 未获取到任何体育市场数据")

if __name__ == "__main__":
    main()
