#!/usr/bin/env python3
"""
Polymarket 分类市场抓取脚本（每个分类只抓最近3条）

功能：
- 按分类抓取活跃市场（Politics/Crypto/Sports）
- 每个分类只抓 3 条最近市场
- 显示市场信息、outcome 价格
- 尝试抓 orderbook
- 保存数据到 data/

体育赛事API使用说明：
- 使用 /sports 端点获取所有支持的体育联赛
- 使用 /events?series_id=X 获取特定联赛的赛事
- 可通过 tag_id=100639 过滤为游戏投注（非期货）
- 示例：NBA联赛ID通常为10345

API端点示例：
  GET /sports                           # 获取所有体育联赛
  GET /events?series_id=10345&active=true&closed=false  # NBA赛事
  GET /events?series_id=10345&tag_id=100639&active=true&closed=false  # NBA游戏投注
"""

import requests
import json
import os
from datetime import datetime, timezone

# ----------------------------
# 配置
# ----------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PolymarketBot/1.0)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://polymarket.com",
    "Referer": "https://polymarket.com/"
}

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"

TARGET_CATEGORIES = ["Politics", "Crypto", "Sports"]
MARKET_PER_CATEGORY = 10
DATA_DIR = "data"

# ----------------------------
# 函数
# ----------------------------

def get_sport_display_name(sport_code):
    """将运动类型缩写转换为可读名称"""
    sport_names = {
        'ncaab': 'NCAA Basketball',
        'nfl': 'NFL',
        'nba': 'NBA',
        'mlb': 'MLB',
        'nhl': 'NHL',
        'soccer': 'Soccer',
        'football': 'Football',
        'basketball': 'Basketball',
        'baseball': 'Baseball',
        'hockey': 'Hockey',
        'tennis': 'Tennis',
        'golf': 'Golf',
        'boxing': 'Boxing',
        'mma': 'MMA',
        'racing': 'Racing',
        'esports': 'E-Sports'
    }
    return sport_names.get(sport_code.lower(), sport_code.upper())

def analyze_sports_season():
    """分析当前时间可能有哪些体育赛事"""
    now = datetime.now(timezone.utc)
    current_month = now.month
    current_day = now.day

    print(f"  📅 当前时间: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print("  🏆 当前可能活跃的体育赛事:")

    season_info = []

    # NBA赛季 (10月-6月)
    if current_month in [10,11,12,1,2,3,4,5,6]:
        if current_month == 10 and current_day < 20:
            season_info.append("🏀 NBA:  preseason")
        elif current_month in [4,5,6] and current_day > 10:
            season_info.append("🏀 NBA:  playoffs")
        else:
            season_info.append("🏀 NBA:  regular season")

    # NFL赛季 (9月-2月)
    if current_month in [9,10,11,12,1,2]:
        if current_month == 9:
            season_info.append("🏈 NFL:  regular season")
        elif current_month in [1,2]:
            season_info.append("🏈 NFL:  playoffs/Super Bowl")
        else:
            season_info.append("🏈 NFL:  regular season")

    # MLB赛季 (4月-10月)
    if current_month in [4,5,6,7,8,9,10]:
        if current_month in [4,5] and current_day < 15:
            season_info.append("⚾ MLB:  opening games")
        elif current_month in [9,10]:
            season_info.append("⚾ MLB:  playoffs/World Series")
        else:
            season_info.append("⚾ MLB:  regular season")

    # NHL赛季 (10月-6月)
    if current_month in [10,11,12,1,2,3,4,5,6]:
        if current_month in [4,5,6]:
            season_info.append("🏒 NHL:  playoffs/Stanley Cup")
        else:
            season_info.append("🏒 NHL:  regular season")

    # NCAA Basketball (11月-3月)
    if current_month in [11,12,1,2,3]:
        if current_month == 3:
            season_info.append("🏀 NCAA:  March Madness tournament")
        else:
            season_info.append("🏀 NCAA:  regular season")

    # Soccer leagues (全年，但高峰期不同)
    season_info.append("⚽ Soccer:  various leagues active")

    if not season_info:
        season_info.append("❄️  Off-season for most major sports")

    for info in season_info:
        print(f"    {info}")

    return season_info

def fetch_markets_by_category_fallback(category, limit=3):
    """通用市场API回退函数，避免递归调用"""
    url = f"{GAMMA_BASE}/markets"

    # 获取更多市场以提高找到体育赛事的机会
    params = {
        "active": "true",
        "limit": 200,  # 增加数量
        "order": "volumeNum",  # 按交易量排序，可能体育赛事交易更活跃
        "ascending": "false"
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        all_markets = r.json()

        # 扩展体育关键词列表
        sports_keywords = [
            # 比赛类型
            "game", "match", "vs", "versus", "final", "quarterfinal", "semifinal",
            # 联赛和杯赛
            "nba", "nfl", "mlb", "nhl", "ncaa", "premier league", "la liga", "bundesliga",
            "serie a", "ligue 1", "champions league", "world cup", "euro", "copa america",
            # 体育项目
            "football", "basketball", "soccer", "baseball", "hockey", "tennis", "golf",
            "boxing", "mma", "ufc", "formula 1", "f1", "nascar", "super bowl", "world series",
            "stanley cup", "finals", "playoffs", "championship", "tournament", "olympics",
            # 球队和选手
            "lakers", "celtics", "warriors", "bulls", "yankees", "red sox", "chiefs", "patriots",
            "manchester united", "liverpool", "real madrid", "barcelona", "bayern munich",
            # 时间相关
            "season", "cup", "league", "trophy", "medal", "bracket", "round", "stage"
        ]

        # 本地按内容过滤体育分类
        filtered_markets = []
        for market in all_markets:
            if isinstance(market, dict):
                question = market.get("question", "").lower()
                # 检查是否包含体育关键词
                if any(keyword.lower() in question for keyword in sports_keywords):
                    filtered_markets.append(market)

        print(f"  📊 回退模式: 从 {len(all_markets)} 个市场中找到 {len(filtered_markets)} 个体育相关市场")

        # 如果还是没找到，尝试更宽泛的搜索
        if len(filtered_markets) == 0:
            print("  🔄 尝试更宽泛的体育关键词搜索...")
            broad_keywords = ["win", "winner", "champion", "score", "points", "victory", "defeat"]
            for market in all_markets[:50]:  # 只检查前50个高交易量市场
                question = market.get("question", "").lower()
                if any(keyword in question for keyword in broad_keywords):
                    # 检查是否可能是体育赛事（通过检查是否有球队名称或体育术语）
                    sports_indicators = ["team", "player", "coach", "stadium", "arena", "court", "field"]
                    if any(indicator in question for indicator in sports_indicators):
                        filtered_markets.append(market)

            print(f"  📊 宽泛搜索找到 {len(filtered_markets)} 个潜在体育市场")

        return filtered_markets[:limit]

    except requests.exceptions.RequestException as e:
        print(f"❌ 回退API调用失败: {e}")
        return []

def fetch_sports_leagues():
    """获取所有支持的体育联赛"""
    url = f"{GAMMA_BASE}/sports"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()

        # 调试信息：打印API响应结构
        if data and len(data) > 0:
            print(f"  🔍 API返回数据结构示例: {data[0]}")
            print(f"  📊 总共获取到 {len(data)} 个联赛项目")

        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取体育联赛失败: {e}")
        return []

def fetch_sports_events(series_id, tag_id=None, limit=10, active_only=False):
    """获取特定联赛的体育赛事"""
    url = f"{GAMMA_BASE}/events"

    if active_only:
        # 查找活跃赛事
        params = {
        "series_id": series_id,
        "active": "true",
        "closed": "false",
        "order": "startTime",
        "ascending": "true",
        "limit": limit
        }
    else:
        # 优先查找2025年11月开始的已结束活动
        params = {
            "series_id": series_id,
            "closed": "true",  # 查找已结束的活动
            "order": "startTime",  # 按开始时间排序（获取最近的赛事）
            "ascending": "false",  # 最新的活动优先
            "limit": limit * 2  # 获取更多用于时间过滤
    }

    # 如果指定了tag_id，添加过滤条件（用于区分游戏投注和期货）
    if tag_id:
        params["tag_id"] = tag_id
        print(f"  🔍 过滤游戏投注 (tag_id={tag_id})")

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        all_events = r.json()

        # 过滤2025年9月之后的数据
        cutoff_date = "2025-11-01T00:00:00Z"
        events = [e for e in all_events if e.get("createdAt", "") >= cutoff_date][:limit]

        # 调试信息
        if events:
            print(f"  ✅ 获取到 {len(events)} 个赛事")
            if len(events) > 0:
                first_event = events[0]
                event_title = first_event.get('title') or first_event.get('name') or 'Unknown'
                print(f"  📋 第一个赛事: {event_title}")
        else:
            print(f"  📭 该联赛暂无活跃赛事")

        return events
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取联赛 {series_id} 赛事失败: {e}")
        return []

def fetch_sports_markets(limit=3):
    """获取真实的体育预测市场数据（从Markets API）"""
    print("  🏆 获取真实的体育预测市场...")

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

    # 排除非体育关键词（避免误匹配）
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

        print(f"  📊 从 {len(all_markets)} 个活跃市场中筛选体育市场...")

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
                    markets.append(market_copy)
                    print(f"  ✅ 发现体育市场: {market['question'][:50]}... (交易量: {volume})")

        # 如果活跃市场不够，补充一些已结束但仍有价值的体育市场
        if len(markets) < limit:
            print(f"  🔄 活跃体育市场不足({len(markets)}/{limit})，补充已结束市场...")

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
                        markets.append(market_copy)
                        print(f"  ✅ 补充已结束体育市场: {market['question'][:50]}... (交易量: {volume})")

        if markets:
            complete_markets = [m for m in markets if m.get("outcomes") and m.get("outcomePrices")]
            print(f"  ✅ 成功获取 {len(markets)} 个真实体育预测市场（{len(complete_markets)} 个有完整赔率）")
            return markets
        else:
            print("  ❌ 未找到任何真实的体育预测市场")
            print("  💡 可能原因: 当前时间段没有活跃的体育赛事预测市场")
            return []

    except Exception as e:
        print(f"  ❌ 体育市场获取失败: {e}")
        return []


# ----------------------------
# 体育API示例函数（演示如何使用新的体育端点）
# ----------------------------
def demo_sports_api_usage():
    """
    演示如何使用Polymarket体育API的示例函数

    根据API文档的最佳实践：
    1. 先获取所有体育联赛：GET /sports
    2. 选择感兴趣的联赛ID
    3. 获取该联赛的赛事：GET /events?series_id=X
    4. 可通过tag_id过滤特定类型的投注
    """

    print("🏆 Polymarket 体育API 使用示例")
    print("=" * 50)

    # 示例1：获取所有体育联赛
    print("📋 步骤1: 获取所有体育联赛")
    print("   API: GET /sports")
    print("   用途: 发现所有可用的体育联赛和series_id")
    print()

    # 示例2：获取NBA赛事
    print("🏀 步骤2: 获取NBA赛事 (假设NBA的series_id=10345)")
    print("   API: GET /events?series_id=10345&active=true&closed=false")
    print("   参数:")
    print("   - series_id: 联赛ID")
    print("   - active=true: 只获取活跃赛事")
    print("   - closed=false: 排除已关闭赛事")
    print("   - order=startTime&ascending=true: 按开始时间排序")
    print()

    # 示例3：只获取NBA游戏投注（非期货）
    print("🎯 步骤3: 获取NBA游戏投注 (tag_id=100639)")
    print("   API: GET /events?series_id=10345&tag_id=100639&active=true&closed=false&order=startTime&ascending=true")
    print("   用途: 过滤掉期货投注，只获取具体比赛的投注")
    print()

    # 示例4：实际代码调用
    print("💻 代码调用示例:")
    print("""
    # 获取体育联赛列表
    leagues = fetch_sports_leagues()

    # 获取NBA赛事
    nba_events = fetch_sports_events("10345", limit=5)

    # 获取NBA游戏投注
    nba_games = fetch_sports_events("10345", tag_id="100639", limit=5)
    """)

    print("🎮 其他体育联赛ID示例:")
    print("   NBA: series_id=10345")
    print("   NFL: series_id=XXXXX (需要从/sports查询获取)")
    print("   MLB: series_id=XXXXX")
    print("   NHL: series_id=XXXXX")
    print("   Soccer: 各种联赛ID")
    print("   Tennis: 各种赛事ID")
    print()

    print("💡 提示:")
    print("   - 先调用 fetch_sports_leagues() 获取所有可用联赛")
    print("   - 找到感兴趣的联赛后，使用其series_id调用 fetch_sports_events()")
    print("   - tag_id=100639 用于过滤游戏投注，排除期货和长期预测")

def fetch_crypto_markets(limit=3):
    """专门获取加密货币市场数据"""
    print("  🔍 获取加密货币市场...")

    crypto_markets = []

    try:
        # 策略1: 直接从markets API获取活跃市场，然后过滤加密货币相关的
        markets_url = f"{GAMMA_BASE}/markets"
        params = {
            "active": "true",  # 获取活跃市场
            "closed": "false",
            "limit": 500,  # 获取更多市场以确保找到加密货币市场
            "order": "volumeNum",  # 按交易量排序
            "ascending": "false"
        }

        r = requests.get(markets_url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        all_markets = r.json()

        # 过滤出加密货币相关的市场
        crypto_keywords = ['bitcoin', 'btc', 'ethereum', 'eth', 'solana', 'xrp', 'chainlink', 'polygon', 'bnb', 'ada', 'doge', 'shib', 'matic', 'blockchain', 'defi', 'nft']

        # 排除政治相关的关键词（因为政治市场有时会包含crypto相关的错误匹配）
        exclude_keywords = ['biden', 'trump', 'election', 'president', 'political', 'government', 'democratic', 'republican', 'nevada', 'swing', 'candidate', 'nomination', 'press conference', 'coronavirus']

        for market in all_markets:
            if len(crypto_markets) >= limit:
                break

            question = market.get("question", "").lower()
            description = market.get("description", "").lower()

            # 检查问题是否包含加密货币关键词，且不包含政治关键词
            has_crypto_keyword = any(keyword in question for keyword in crypto_keywords)
            has_exclude_keyword = any(exclude in question or exclude in description for exclude in exclude_keywords)

            if has_crypto_keyword and not has_exclude_keyword:
                # 放宽过滤条件：只要包含加密货币关键词且不包含政治关键词即可
                # 包括价格预测、达到目标价位等各种加密货币相关问题
                price_indicators = ['price', 'hit', 'reach', 'above', 'below', '$', 'usd', 'market cap', 'fdv', 'valuation', 'up or down', 'trading', 'exchange']
                if any(indicator in question for indicator in price_indicators) or 'will' in question:
                    # 避免重复
                    if not any(m.get("id") == market.get("id") for m in crypto_markets):
                        crypto_markets.append(market)

        print(f"  📊 从 {len(all_markets)} 个活跃市场中找到 {len(crypto_markets)} 个加密货币市场")

        # 如果还是没有找到，尝试获取已结束的加密货币市场
        if len(crypto_markets) == 0:
            print("  🔄 未找到活跃加密货币市场，尝试获取已结束市场...")

            params_closed = {
                "closed": "true",
                "limit": 500,
                "order": "volumeNum",
                "ascending": "false"
            }

            r_closed = requests.get(markets_url, headers=HEADERS, params=params_closed, timeout=10)
            r_closed.raise_for_status()
            closed_markets = r_closed.json()

            for market in closed_markets:
                if len(crypto_markets) >= limit:
                    break

                question = market.get("question", "").lower()
                description = market.get("description", "").lower()

                # 使用相同的过滤逻辑
                has_crypto_keyword = any(keyword in question for keyword in crypto_keywords)
                has_exclude_keyword = any(exclude in question or exclude in description for exclude in exclude_keywords)

                if has_crypto_keyword and not has_exclude_keyword:
                    price_indicators = ['price', 'hit', 'reach', 'above', 'below', '$', 'usd', 'market cap', 'fdv', 'valuation', 'up or down', 'trading', 'exchange']
                    if any(indicator in question for indicator in price_indicators) or 'will' in question:
                        if not any(m.get("id") == market.get("id") for m in crypto_markets):
                            crypto_markets.append(market)

            print(f"  📊 从已结束市场中找到 {len(crypto_markets)} 个加密货币市场")

    except Exception as e:
        print(f"  ❌ 获取加密货币市场失败: {e}")

    print(f"  ✅ 最终获取到 {len(crypto_markets)} 个加密货币市场")
    return crypto_markets[:limit]

def fetch_markets_by_category(category, limit=3):
    """按分类抓取活跃市场，限制条数"""

    # 加密货币分类使用专门的系列API
    if category == "Crypto":
        return fetch_crypto_markets(limit)

    # 体育分类使用专门的体育API
    if category == "Sports":
        return fetch_sports_markets(limit)

    # 其他分类使用通用市场API - 优先获取已结束的市场（有完整赔率数据）
    url = f"{GAMMA_BASE}/markets"

    # 获取已结束的市场（有完整的结果数据），然后进行时间过滤
    params = {
        "closed": "true",  # 已结束的市场
        "limit": 200,  # 获取更多市场用于后续过滤
        "order": "createdAt",  # 按创建时间排序
        "ascending": "false"  # 最新的在前
    }

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        all_markets = r.json()

        # 过滤2025年11月之后的数据（包含2026年的市场）
        cutoff_date = "2025-11-01T00:00:00Z"
        recent_markets = []
        for market in all_markets:
            created_at = market.get("createdAt", "")
            if created_at >= cutoff_date:
                recent_markets.append(market)

        print(f"  📅 从 {len(all_markets)} 个市场中过滤出 {len(recent_markets)} 个2025年9月之后的市场")

        # 本地按内容过滤分类
        filtered_markets = []
        category_keywords = {
            "Politics": ["election", "president", "political", "party", "government", "vote", "trump", "biden", "senate", "congress", "democrat", "republican", "primaries", "midterm", "ballot", "campaign", "policy", "legislation", "parliament", "minister"],
            "Crypto": ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "solana", "xrp", "chainlink", "polygon"],
            "Sports": ["game", "match", "season", "championship", "tournament", "football", "basketball", "soccer", "nfl", "nba"]
        }

        keywords = category_keywords.get(category, [])
        for market in recent_markets:
            question = market.get("question", "").lower()
            if any(keyword.lower() in question for keyword in keywords):
                filtered_markets.append(market)
                if len(filtered_markets) >= limit:
                    break

        # 如果已结束的市场中找不到足够的数据，回退到获取活跃市场
        if len(filtered_markets) < limit:
            print(f"  📈 已结束市场中只找到 {len(filtered_markets)} 个{category}市场，尝试获取活跃市场补充...")
            try:
                active_params = {
                    "active": "true",
                    "closed": "false",
                    "limit": 50,
                    "order": "volumeNum",
                    "ascending": "false"
                }
                active_r = requests.get(url, headers=HEADERS, params=active_params, timeout=10)
                active_r.raise_for_status()
                active_markets = active_r.json()

                # 从活跃市场中补充数据
                for market in active_markets:
                    if len(filtered_markets) >= limit:
                        break
                    question = market.get("question", "").lower()
                    if any(keyword.lower() in question for keyword in keywords):
                        # 检查是否已存在（避免重复）
                        if not any(m.get("id") == market.get("id") for m in filtered_markets):
                            filtered_markets.append(market)

            except requests.exceptions.RequestException as e:
                print(f"  ⚠️ 获取活跃市场补充数据失败: {e}")

        return filtered_markets[:limit]

    except requests.exceptions.RequestException as e:
        print(f"❌ 抓取分类 {category} 市场失败: {e}")
        return []
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ 抓取分类 {category} 市场失败: {e}")
        return []

def fetch_market_orderbook(market_id):
    """尝试抓取市场 orderbook"""
    url = f"{CLOB_BASE}/markets/{market_id}/orderbook"
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass
    return None

def parse_outcome_prices(price_data):
    """解析 outcomePrices"""
    if not price_data:
        return []
    if isinstance(price_data, list):
        return price_data
    if isinstance(price_data, str):
        try:
            prices = json.loads(price_data)
            if isinstance(prices, list):
                return prices
        except json.JSONDecodeError:
            # 如果不是有效的JSON，尝试按逗号分割的字符串
            if "," in price_data:
                prices = [p.strip().strip('"').strip("'") for p in price_data.split(",")]
                return prices
            pass
    return []

def infer_category(question):
    """根据问题内容推断分类"""
    question_lower = question.lower()

    # 政治相关关键词
    politics_keywords = ["election", "president", "political", "party", "government", "vote", "trump", "biden", "senate", "congress"]
    if any(k in question_lower for k in politics_keywords):
        return "Politics"

    # 加密货币相关关键词
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "cryptocurrency", "solana", "xrp", "chainlink", "polygon"]
    if any(k in question_lower for k in crypto_keywords):
        return "Crypto"

    # 体育相关关键词
    sports_keywords = ["game", "match", "season", "championship", "tournament", "football", "basketball", "soccer", "nfl", "nba", "super bowl", "bowl", "finals", "playoffs", "cup", "league", "trophy", "medal", "olympics", "world cup"]
    if any(k in question_lower for k in sports_keywords):
        return "Sports"

    return "Other"

def get_contracts_by_condition_id(condition_id):
    """基于condition ID获取对应的合约地址"""
    contracts = {
        "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
        "clob_exchange": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",
        "fee_module": "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"
    }

    # 尝试通过API获取最新的市场信息
    try:
        markets_url = "https://gamma-api.polymarket.com/markets"
        params = {
            "closed": "true",
            "limit": 100,
            "order": "createdAt",
            "ascending": "false"
        }

        response = requests.get(markets_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # 查找匹配的condition ID
                for market in data:
                    if market.get('conditionId') == condition_id:
                        # 获取CLOb Token IDs
                        clob_tokens = market.get('clobTokenIds')
                        if clob_tokens:
                            if isinstance(clob_tokens, str):
                                try:
                                    import ast
                                    clob_tokens = ast.literal_eval(clob_tokens)
                                except:
                                    clob_tokens = clob_tokens
                            if isinstance(clob_tokens, list):
                                contracts["clob_token_ids"] = clob_tokens
                        break
    except:
        pass

    # 如果API查询失败，使用默认的代币ID
    if "clob_token_ids" not in contracts:
        # 这是针对特定condition ID的默认值
        if condition_id == "0x77c56205d774dd5b7b9204f7cf718f8da1a58681e28c958e0d12785b1ae5f868":
            contracts["clob_token_ids"] = [
                "114603791532125824334106100104937539663660514876906877399579728573490388096852",
                "58170762178444881344411270304308822808501784222381155502926655084160294019978"
            ]

    return contracts

def get_contract_addresses(market):
    """获取市场的合约地址信息"""
    contract_info = {}

    # Conditional Tokens条件ID
    condition_id = market.get("conditionId")
    if condition_id:
        contract_info["condition_id"] = condition_id
        # 在conditionId字段下添加合约地址信息
        contract_info["contract_addresses"] = get_contracts_by_condition_id(condition_id)

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

    # Polymarket真实合约地址（来自官方文档和区块链验证）
    polymarket_contracts = {
        "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",  # Conditional Tokens主合约
        "clob_exchange": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",     # CLOb Exchange合约
        "fee_module": "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"        # Fee Module合约
    }

    contract_info["known_contracts"] = polymarket_contracts

    return contract_info

def explain_etherscan_lookup(market):
    """解释如何在Etherscan上查找交易历史"""
    print("\n🔍 Etherscan交易历史查询指南:")

    contract_info = get_contract_addresses(market)

    if contract_info.get("condition_id"):
        print("1️⃣ Conditional Tokens合约查询:")
        print(f"   条件ID: {contract_info['condition_id']}")
        print("   📝 这个ID用于Conditional Tokens合约中的条件")
        print("   🔗 查询: 搜索Conditional Tokens合约 + 这个条件ID")

    if contract_info.get("clob_token_ids"):
        print("\n2️⃣ CLOb Token交易查询:")
        print(f"   Token IDs: {contract_info['clob_token_ids']}")
        print("   📝 这些是订单簿中的ERC20代币")
        print("   🔗 在Etherscan搜索这些Token地址")

    print("\n3️⃣ Polymarket主要合约:")
    known = contract_info.get("known_contracts", {})
    for name, address in known.items():
        print(f"   {name}: {address}")

    print("\n💡 查询步骤:")
    print("   1. 去 https://etherscan.io/")
    print("   2. 搜索合约地址或Token ID")
    print("   3. 查看 'Token Transfers' 或 'Transactions' 标签")
    print("   4. 过滤特定时间范围的交易")

    print("\n⚠️ 注意:")
    print("   - Polymarket使用Conditional Tokens标准")
    print("   - 交易可能通过多个合约完成")
    print("   - 高频交易市场可能有大量交易记录")

def get_game_status(market):
    """分析比赛状态"""
    question = market.get("question", "").lower()
    end_date_str = market.get("endDate", "")

    # 检查是否是体育赛事
    is_sports = (
        "sports" in question or
        any(sport in question for sport in ["nba", "nfl", "mlb", "nhl", "game", "match", "vs", "versus"]) or
        market.get("sport_type") == "Sports" or
        market.get("event_type") == "game"
    )

    if not is_sports:
        return None

    # 解析结束时间
    try:
        if end_date_str and end_date_str != "N/A":
            # 处理不同的时间格式
            if end_date_str.endswith('Z'):
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            else:
                end_date = datetime.fromisoformat(end_date_str)

            now = datetime.now(timezone.utc)
            time_diff = end_date - now

            # 对于体育赛事的智能状态判断
            if time_diff.total_seconds() < -3600:  # 1小时前结束
                return "🏁 已结束"
            elif time_diff.total_seconds() < 0:  # 比赛时间已到但可能还在进行
                # 检查交易量，如果很高可能正在进行中
                volume = market.get("volumeNum", 0)
                if volume > 100000:  # 高交易量可能表示比赛进行中
                    return "🔴 比赛进行中"
                else:
                    return "🏁 可能已结束"
            elif time_diff.total_seconds() < 3600 * 2:  # 2小时内开始
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                if hours > 0:
                    return f"⏰ {hours}小时{minutes}分钟后开始"
                elif minutes > 5:
                    return f"⏰ {minutes}分钟后开始"
                else:
                    return "🔥 即将开始"
            elif time_diff.total_seconds() < 3600 * 24:  # 24小时内
                return f"📅 今天 {end_date.strftime('%H:%M')} 开始"
            elif time_diff.total_seconds() < 3600 * 24 * 7:  # 一周内
                return f"📅 {end_date.strftime('%m-%d %H:%M')} 开始"
            else:
                # 更远的比赛
                return f"📅 {end_date.strftime('%m-%d')} 开始"

    except (ValueError, AttributeError) as e:
        # 如果时间解析失败，但这是体育赛事，返回基本状态
        volume = market.get("volumeNum", 0)
        if volume > 50000:  # 高交易量
            return "🔴 可能正在进行"
        elif volume > 10000:  # 中等交易量
            return "⚽ 比赛相关"
        else:
            return "🏆 体育赛事"

    # 如果没有时间信息但确定是体育赛事
    volume = market.get("volumeNum", 0)
    if volume > 100000:
        return "🔴 高活跃度比赛"
    elif any(team in question for team in ["warriors", "lakers", "celtics", "heat", "bulls"]):
        return "🏀 NBA比赛"
    else:
        return "⚽ 体育赛事"

def display_market_info(market):
    """显示市场信息"""
    market_id = market.get("id")
    question = market.get("question", "N/A")
    category = infer_category(question)  # 使用推断的分类
    end_date = market.get("endDate", "N/A")
    volume = market.get("volumeNum", 0)
    liquidity = market.get("liquidityNum", 0)

    # 获取比赛状态
    game_status = get_game_status(market)

    # 解析outcomes JSON字符串
    outcomes_raw = market.get("outcomes", "[]")
    try:
        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
    except json.JSONDecodeError:
        outcomes = []

    outcome_prices = parse_outcome_prices(market.get("outcomePrices"))

    print("──────────────────────────────")
    print(f"Market ID : {market_id}")
    print(f"Question  : {question}")
    print(f"Category  : {category}")

    # 显示比赛状态（如果是体育赛事）
    if game_status:
        print(f"Status    : {game_status}")
    else:
        print(f"End Date  : {end_date}")

    print(f"Volume    : {volume}")
    print(f"Liquidity : {liquidity}")

    # 显示合约相关信息
    condition_id = market.get("conditionId", "N/A")
    clob_token_ids = market.get("clobTokenIds", "N/A")

    if condition_id != "N/A":
        print(f"Condition ID: {condition_id}")
    if clob_token_ids != "N/A":
        print(f"CLOb Tokens : {clob_token_ids}")

    # 如果用户想要详细的合约信息，提供说明
    if condition_id != "N/A" or clob_token_ids != "N/A":
        print("💡 使用 explain_etherscan_lookup(market) 查看Etherscan查询指南")

    # 显示 outcomes
    if outcomes:
        print("Outcomes & Prices:")
        for i, o in enumerate(outcomes):
            try:
                p = float(outcome_prices[i])
                print(f"  - {o}: {p:.4f} ({p*100:.1f}%)")
            except (IndexError, ValueError):
                print(f"  - {o}: 暂无价格")
    else:
        # 检查数据来源，如果是体育API，显示特殊提示
        if market.get("data_source") == "sports_api":
            print("Outcomes: 体育API暂不支持赔率数据")
        else:
            print("Outcomes: 暂无")

    # orderbook
    orderbook = fetch_market_orderbook(market_id)
    print("\n📊 Orderbook:")
    if orderbook and "bids" in orderbook and "asks" in orderbook:
        bids = orderbook.get("bids", [])
        asks = orderbook.get("asks", [])
        if bids and asks:
            best_bid = float(bids[0][0]) if bids[0] else 0
            best_ask = float(asks[0][0]) if asks[0] else 0
            mid_price = (best_bid + best_ask)/2 if best_bid>0 and best_ask>0 else 0
            print(f"  Best Bid: {best_bid}")
            print(f"  Best Ask: {best_ask}")
            print(f"  Mid Price: {mid_price}")
        else:
            print("  ❌ No active bids/asks")
    else:
        print("  ❌ Orderbook 不可用")

def save_markets_to_file(all_markets, filename=None):
    """保存市场数据到 JSON 文件"""
    if not all_markets:
        print("⚠️ 无市场数据可保存")
        return None

    os.makedirs(DATA_DIR, exist_ok=True)
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"polymarket_markets_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)

    data_to_save = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_markets": len(all_markets)
        },
        "markets": all_markets
    }

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        print(f"💾 数据已保存到 {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None

# ----------------------------
# 主函数
# ----------------------------
def main():
    print("🚀 Polymarket 分类市场抓取（每个分类只抓最近3条）\n")

    all_markets = []
    category_results = {}  # 存储各分类的结果

    for category in TARGET_CATEGORIES:
        print(f"\n🔹 抓取分类: {category}")
        markets = fetch_markets_by_category(category, limit=MARKET_PER_CATEGORY)
        category_results[category] = markets

        if markets:
            # 为分类市场添加合约地址信息
            markets_with_contracts = []
            for market in markets:
                contract_info = get_contract_addresses(market)
                if contract_info:
                    market_copy = market.copy()
                    market_copy.update(contract_info)
                    markets_with_contracts.append(market_copy)
                else:
                    markets_with_contracts.append(market)

            all_markets.extend(markets_with_contracts)
            print(f"  ✅ 抓取到 {len(markets)} 个市场")

            # 立即保存各分类的数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"polymarket_markets_{category}_{timestamp}.json"
            save_markets_to_file(markets_with_contracts, filename)
        else:
            print(f"  ⚠️ 分类 {category} 无数据")

    # 去重，确保每个市场只抓取一次（基于市场ID）
    seen_ids = set()
    unique_markets = []
    for market in all_markets:
        market_id = market.get('id')
        if market_id and market_id not in seen_ids:
            seen_ids.add(market_id)
            # 为每个市场添加合约地址信息
            contract_info = get_contract_addresses(market)
            if contract_info:
                # 将合约地址信息合并到市场数据中
                market.update(contract_info)
            unique_markets.append(market)

    if not all_markets:
        print("❌ 没有抓到任何市场")
        # 显示体育API使用说明
        print("\n💡 体育市场获取提示:")
        print("   如果需要体育数据，可以使用专门的体育API:")
        print("   1. 获取联赛列表：fetch_sports_leagues()")
        print("   2. 获取具体赛事：fetch_sports_events(series_id)")
        print("   详细用法请参考 demo_sports_api_usage() 函数")
        return

    # 保存总数据
    save_markets_to_file(all_markets)

    # 显示各分类的统计信息
    print("\n📊 抓取统计:")
    for category, markets in category_results.items():
        if markets:
            print(f"  {category}: {len(markets)} 个市场")
        else:
            print(f"  {category}: 0 个市场")

    # 显示所有抓到的市场（每个分类最多 3 条）
    print("\n📌 显示抓到的市场信息")
    for market in all_markets:
        display_market_info(market)

    print(f"\n✅ 脚本执行完成 - 共抓取 {len(all_markets)} 个市场")

if __name__ == "__main__":
    import sys

    # 如果命令行参数包含"demo"，显示体育API演示
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_sports_api_usage()
    else:
        main()
