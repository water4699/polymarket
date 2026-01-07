import requests
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def fetch_market_detail(market_id: int):
    url = f"https://gamma-api.polymarket.com/markets/{market_id}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()

def main():
    market_id = 43
    data = fetch_market_detail(market_id)

    print("=== 市场详情 ===\n")
    print(f"Market ID : {data.get('id')}")
    print(f"Question  : {data.get('question')}")
    print(f"Category  : {data.get('category')}")
    print(f"End Date  : {data.get('endDate')}")
    print(f"Volume    : {data.get('volume')}")
    print(f"Liquidity : {data.get('liquidity')}")

    print("\n=== Outcomes ===")
    outcomes_raw = data.get("outcomes")

    # 处理不同的outcomes格式
    if outcomes_raw is None:
        print("No outcomes data available")
        return

    # 如果是字符串，尝试解析为JSON
    if isinstance(outcomes_raw, str):
        try:
            outcomes = json.loads(outcomes_raw)
            print(f"Outcomes从字符串解析为: {type(outcomes)}")
        except json.JSONDecodeError:
            # 如果无法解析，当作单个字符串处理
            print(f"- Outcome: {outcomes_raw}")
            return
    else:
        outcomes = outcomes_raw

    # 确保是列表
    if not isinstance(outcomes, list):
        print(f"Unexpected outcomes format: {type(outcomes)} - {outcomes}")
        return

    if not outcomes:
        print("Outcomes list is empty")
        return

    # 处理列表中的每个outcome
    for i, o in enumerate(outcomes):
        if isinstance(o, dict):
            # 如果是字典格式
            print(f"- Outcome {i+1}: {o.get('title', 'N/A')}")
            print(f"  Price : {o.get('price', 'N/A')}")
            print(f"  Token : {o.get('tokenAddress', 'N/A')}")
        elif isinstance(o, str):
            # 如果直接是字符串
            print(f"- Outcome {i+1}: {o}")
        else:
            # 其他格式
            print(f"- Outcome {i+1}: {str(o)}")
        print()

if __name__ == "__main__":
    main()
