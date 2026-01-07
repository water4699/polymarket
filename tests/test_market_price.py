import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

GAMMA_BASE = "https://gamma-api.polymarket.com"


def fetch_markets(limit=50):
    url = f"{GAMMA_BASE}/markets"
    params = {
        "active": "true",
        "limit": limit
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️  API访问失败: {e}")
        print("💡 使用模拟数据进行测试...")

        # 返回模拟市场数据用于测试 - 包含新旧市场来测试过滤
        return [
            # 最近的市场 (2024年)
            {
                "id": "2024-001",
                "question": "Will Ethereum reach $10,000 before 2025?",
                "category": "Crypto",
                "active": True,
                "resolved": None,
                "endDate": "2024-12-31T23:59:59Z",
                "volume": 150000,
                "liquidity": 25000,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0.65", "0.35"]'
            },
            {
                "id": "2024-002",
                "question": "Will the US Federal Reserve cut interest rates in 2024?",
                "category": "Economics",
                "active": True,
                "resolved": None,
                "endDate": "2024-12-15T23:59:59Z",
                "volume": 200000,
                "liquidity": 35000,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0.55", "0.45"]'
            },
            {
                "id": "2024-003",
                "question": "Will OpenAI release GPT-5 in 2024?",
                "category": "Technology",
                "active": True,
                "resolved": None,
                "endDate": "2024-11-30T23:59:59Z",
                "volume": 180000,
                "liquidity": 30000,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0.4", "0.6"]'
            },
            # 旧市场 (2020-2021年) - 应该被过滤掉
            {
                "id": "12",
                "question": "Will Joe Biden get Coronavirus before the election?",
                "category": "US-current-affairs",
                "active": True,
                "resolved": None,
                "endDate": "2020-11-03T23:59:59Z",  # 2020年
                "volume": 32257.445115,
                "liquidity": 0,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0", "0"]'
            },
            {
                "id": "17",
                "question": "Will Airbnb begin publicly trading before Jan 1, 2021?",
                "category": "Tech",
                "active": True,
                "resolved": None,
                "endDate": "2020-12-31T23:59:59Z",  # 2020年
                "volume": 89665.252158,
                "liquidity": 0,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0", "0"]'
            },
            {
                "id": "18",
                "question": "Will a new Supreme Court Justice be confirmed before Nov 3rd, 2020?",
                "category": "US-current-affairs",
                "active": True,
                "resolved": None,
                "endDate": "2020-11-03T23:59:59Z",  # 2020年
                "volume": 43279.456005,
                "liquidity": 0,
                "outcomes": ["Yes", "No"],
                "outcomePrices": '["0", "0"]'
            }
        ]


def is_recent_market(m):
    """检查市场是否是最近的（2024年及以后）"""
    end_date = m.get("endDate")
    if not end_date:
        return False

    try:
        from datetime import datetime
        # 处理不同的日期格式
        if isinstance(end_date, str):
            # 尝试解析ISO格式日期
            if 'T' in end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                # 如果是其他格式，尝试直接解析
                end_dt = datetime.strptime(end_date[:10], "%Y-%m-%d")
        else:
            return False

        # 只保留2024年及以后的市场
        return end_dt.year >= 2024

    except (ValueError, TypeError):
        return False


def is_tradable_market(m):
    """检查市场是否有交易价格数据"""
    prices = m.get("outcomePrices")
    outcomes = m.get("outcomes")

    if not prices or not outcomes:
        return False

    # 处理Polymarket API的数据格式
    if isinstance(prices, str):
        # 如果是字符串，尝试解析为JSON列表
        try:
            import json
            parsed_prices = json.loads(prices)
            if isinstance(parsed_prices, list) and len(parsed_prices) > 0:
                return True
        except (json.JSONDecodeError, TypeError):
            return False
    elif isinstance(prices, list):
        # 如果已经是列表，直接检查
        if len(prices) == 0:
            return False
        return True

    return False


def is_currently_active(m):
    """综合判断：最近 + 可交易"""
    return is_recent_market(m) and is_tradable_market(m)


def main():
    print("=== Fetching active markets ===")
    markets = fetch_markets(limit=50)
    print(f"Fetched {len(markets)} markets\n")

    # 调试：分析前几个市场的结构
    print("=== Market Analysis (first 5) ===")
    for i, m in enumerate(markets[:5]):
        print(f"\nMarket {i+1}:")
        print(f"  ID: {m.get('id')}")
        print(f"  Question: {m.get('question', 'N/A')[:50]}...")
        print(f"  End Date: {m.get('endDate', 'N/A')}")
        print(f"  Active: {m.get('active')}")
        print(f"  Resolved: {m.get('resolved')}")
        print(f"  Has outcomes: {bool(m.get('outcomes'))}")
        prices = m.get('outcomePrices')
        print(f"  Has prices: {bool(prices)}")
        print(f"  Prices type: {type(prices)}")

        # 显示价格内容
        if isinstance(prices, str):
            print(f"  Prices content: {prices[:50]}{'...' if len(prices) > 50 else ''}")
        elif isinstance(prices, list):
            print(f"  Prices len: {len(prices)}")
        else:
            print(f"  Prices content: {prices}")

        print(f"  Is recent: {is_recent_market(m)}")
        print(f"  Is tradable: {is_tradable_market(m)}")
        print(f"  Is currently active: {is_currently_active(m)}")

    print("\n=== Filtering Results ===")

    shown = 0
    recent_count = 0
    tradable_count = 0
    active_count = 0

    for m in markets:
        if is_recent_market(m):
            recent_count += 1
        if is_tradable_market(m):
            tradable_count += 1
        if is_currently_active(m):
            active_count += 1

    print(f"Total markets: {len(markets)}")
    print(f"Recent markets (2024+): {recent_count}")
    print(f"Tradable markets: {tradable_count}")
    print(f"Currently active markets: {active_count}")
    print()

    for m in markets:
        if not is_currently_active(m):
            continue

        print("────────────────────────────────────")
        print(f"Market ID : {m.get('id')}")
        print(f"Question  : {m.get('question')}")
        print(f"Category  : {m.get('category')}")
        print(f"Resolved  : {m.get('resolved')}")
        print(f"Volume    : {m.get('volume')}")
        print(f"Liquidity : {m.get('liquidity')}")

        outcomes = m.get("outcomes")
        prices_raw = m.get("outcomePrices")

        # 处理价格数据格式
        prices = []
        if isinstance(prices_raw, str):
            # 如果是字符串，先尝试直接解析JSON
            try:
                import json
                prices = json.loads(prices_raw)
            except (json.JSONDecodeError, TypeError):
                # 如果解析失败，可能已经是字符串数组格式如 ["0.45", "0.55"]
                # 尝试手动解析
                if prices_raw.startswith('["') and prices_raw.endswith('"]'):
                    # 移除外层引号和方括号
                    content = prices_raw[2:-2]  # 移除 [" 和 "]
                    if content:
                        # 按逗号分割
                        prices = [p.strip().strip('"') for p in content.split('","')]
                        if '",' in content:  # 处理带引号的情况
                            prices = [p.strip() for p in content.split('","')]
                            prices = [p.strip('"') for p in prices]
                    else:
                        prices = []
                else:
                    prices = []
        elif isinstance(prices_raw, list):
            prices = prices_raw
        else:
            prices = []

        print("Outcomes & Prices:")
        if outcomes and prices and len(outcomes) == len(prices):
            for o, p in zip(outcomes, prices):
                try:
                    # 尝试将价格转换为float显示
                    price_float = float(p)
                    print(f"  - {o}: {price_float:.4f}")
                except (ValueError, TypeError):
                    print(f"  - {o}: {p}")
        elif outcomes:
            print(f"  Outcomes: {outcomes}")
            print(f"  Prices (raw): {prices_raw}")
        else:
            print("  No outcomes data available")

        shown += 1
        if shown >= 3:
            break

    if shown == 0:
        print("❌ No tradable markets found")


if __name__ == "__main__":
    main()
