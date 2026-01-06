import requests
import time

# -------------------------------
# 配置区
# -------------------------------
API_KEYS = [
    {
        "apikey": "QTZZ2KHYZTUHF9QE5FE1HTBDXCYFHPR3YG",
        "proxy": {
            "ip": "167.100.107.205",
            "port": "6774",
            "user": "xtsgqbla",
            "pass": "a337l88lug4v"
        }
    },
]

ADDRESS = "0xa27CEF8aF2B6575903b676e5644657FAe96F491F"  # 查询地址
PAGE_START = 1
OFFSET = 200
SLEEP_SEC = 0.2
MAX_PAGES = 1000  # 防止死循环
# -------------------------------

def get_proxies(proxy_info):
    proxy_str = f"http://{proxy_info['user']}:{proxy_info['pass']}@{proxy_info['ip']}:{proxy_info['port']}"
    return {"http": proxy_str, "https": proxy_str}

def fetch_erc20_tx(api_key_info, address, page, offset):
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": 1,  # 以太坊主网
        "module": "account",
        "action": "tokentx",
        "address": address,
        "page": page,
        "offset": offset,
        "sort": "asc",
        "apikey": api_key_info["apikey"]
    }
    proxies = get_proxies(api_key_info["proxy"])
    try:
        resp = requests.get(url, params=params, proxies=proxies, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            print(f"第 {page} 页请求失败:", data.get("message"))
            return []
        return data.get("result", [])
    except Exception as e:
        print(f"第 {page} 页请求异常:", str(e))
        return []

# -------------------------------
# 主程序
# -------------------------------
all_txs = []
page = PAGE_START
api_index = 0
fail_count = 0

while page <= MAX_PAGES:
    api_key_info = API_KEYS[api_index]
    txs = fetch_erc20_tx(api_key_info, ADDRESS, page, OFFSET)
    if not txs:
        fail_count += 1
        if fail_count >= 3:  # 连续3次无数据或异常则退出
            print("抓取结束或连续失败，退出")
            break
        time.sleep(SLEEP_SEC)
        continue
    fail_count = 0  # 重置失败计数
    for tx in txs:
        try:
            value = int(tx.get("value", 0)) / 10**int(tx.get("tokenDecimal", 18))
        except Exception:
            value = 0
        print(f"{tx.get('tokenSymbol','N/A'):6} | {tx.get('from','')[:6]} → {tx.get('to','')[:6]} | {value:.4f} | block:{tx.get('blockNumber','')}")
    all_txs.extend(txs)
    page += 1
    time.sleep(SLEEP_SEC)

print(f"总共抓取 {len(all_txs)} 条交易")
