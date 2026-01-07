import requests

URL = "https://gamma-api.polymarket.com/markets"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

TARGET_CATEGORIES = {"Politics", "Crypto", "Sports"}

def fetch_markets(limit=20):
    params = {
        "limit": limit,
        "active": "true"
    }
    resp = requests.get(URL, headers=HEADERS, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def main():
    print("=== 拉取 Polymarket 市场数据（测试） ===\n")
    markets = fetch_markets()

    count = 0
    for m in markets:
        category = m.get("category")
        if category not in TARGET_CATEGORIES:
            continue

        print(f"Market ID : {m.get('id')}")
        print(f"Question  : {m.get('question')}")
        print(f"Category  : {category}")
        print(f"Slug      : {m.get('slug')}")
        print(f"Active    : {m.get('active')}")
        print("-" * 50)

        count += 1
        if count >= 5:
            break

    print(f"\n共输出 {count} 条市场（测试完成）")

if __name__ == "__main__":
    main()
