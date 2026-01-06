# test_etherscan_tx_v2.py
from modules.api_key_manager import EtherscanAPIManager

# 数据库连接 URL
DATABASE_URL = "postgresql://predictlab_user:your_password@localhost:5432/polymarket"

def main():
    manager = EtherscanAPIManager(DATABASE_URL)

    # 交易哈希
    tx_hash = "0x26b5f7f3a545d70e76ce0c4af8e64f505bcb7d3ab1f1d1477bc07f4a953834fd"

    # V2 接口: 通过账户抓 ERC-20 或普通交易，然后匹配 txhash
    # 这里示例用 ERC-20 token 转账查询
    address = "0x015ADB97B5609478901c3a4ca34A67674d1eb576"  # 交易发送者
    params = {
        "chainid": 1,  # Etherscan V2 必需参数
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,  # 当前区块高度
        "sort": "desc",  # 最新交易在前
        "page": 1,
        "offset": 10  # 限制返回数量，避免过多数据
    }

    print("=== 抓取交易信息 ===")
    print(f"查询地址: {address}")
    print(f"目标交易哈希: {tx_hash}")
    print(f"请求参数: {params}")

    response = manager.make_api_request(params)

    if response and response.get("status") == "1":
        tx_list = response.get("result", [])
        print(f"获取到 {len(tx_list)} 条交易记录")

        # 查找匹配的交易哈希
        tx_info = next((tx for tx in tx_list if tx.get("hash") == tx_hash), None)

        if tx_info:
            print("✅ 找到匹配的交易!")
            print("=== 交易详情 ===")
            print(f"交易哈希: {tx_info.get('hash')}")
            print(f"From: {tx_info.get('from')}")
            print(f"To: {tx_info.get('to')}")
            print(f"Token: {tx_info.get('tokenSymbol', 'Unknown')}")
            try:
                amount = int(tx_info.get('value', 0)) / (10 ** int(tx_info.get('tokenDecimal', 18)))
                print(f"Amount: {amount}")
            except:
                print(f"Amount: {tx_info.get('value', 'Unknown')}")
            print(f"Block: {tx_info.get('blockNumber')}")
            print(f"TimeStamp: {tx_info.get('timeStamp')}")
        else:
            print("❌ 交易未在账户列表中找到")
            # 显示前几条交易作为示例
            if tx_list:
                print("\n📋 该地址的最新交易:")
                for i, tx in enumerate(tx_list[:3]):
                    print(f"{i+1}. {tx.get('hash')} - {tx.get('tokenSymbol')}")

    elif response and response.get("status") == "0":
        # API返回错误
        error_msg = response.get("message", "Unknown error")
        print(f"❌ API返回错误: {error_msg}")

        if "api key" in error_msg.lower():
            print("💡 建议: 检查API key是否有效，或尝试其他key")
        elif "limit" in error_msg.lower():
            print("💡 建议: 已达到API调用限制，请稍后再试")
        elif "notok" in error_msg.lower():
            print("💡 NOTOK错误可能原因:")
            print("   - API key无效或过期")
            print("   - 请求参数格式错误")
            print("   - 账户权限不足")
            print("   - 网络或代理问题")

    else:
        print("❌ 请求失败或无交易记录")
        if response:
            print(f"响应内容: {response}")

    # 额外诊断信息
    print("\n🔍 诊断信息:")
    print(f"   - 使用的API账户ID: 检查日志中的'选择API Key'信息")
    print(f"   - 目标地址是否有交易: {address}")
    print(f"   - endblock参数可能过大，建议使用当前区块高度")

if __name__ == "__main__":
    main()
