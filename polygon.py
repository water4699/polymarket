import json
from web3 import Web3

ERC1155_CONTRACT = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
CHAIN_ID_POLYGON = 137

TRANSFER_SINGLE_TOPIC = Web3.keccak(
    text="TransferSingle(address,address,address,uint256,uint256)"
).hex()


def get_token_logs(
    manager: EtherscanAPIManager,
    token_id: int,
    limit: int = 20
) -> List[Dict]:
    """
    抓指定 ERC-1155 tokenId 的最近交易 logs（Polygon）
    """

    params = {
        "chainid": CHAIN_ID_POLYGON,
        "module": "logs",
        "action": "getLogs",
        "address": ERC1155_CONTRACT,
        "topic0": TRANSFER_SINGLE_TOPIC,
        "fromBlock": "0",
        "toBlock": "latest"
    }

    data = manager.make_api_request(params)
    if not data or "result" not in data:
        return []

    results = []

    for log in reversed(data["result"]):
        # ERC1155: data = id + value (each 32 bytes)
        raw_data = log["data"].replace("0x", "")
        log_token_id = int(raw_data[:64], 16)

        if log_token_id != token_id:
            continue

        results.append({
            "blockNumber": int(log["blockNumber"], 16),
            "txHash": log["transactionHash"],
            "from": "0x" + log["topics"][2][-40:],
            "to": "0x" + log["topics"][3][-40:],
            "tokenId": log_token_id,
            "value": int(raw_data[64:128], 16),
            "timestamp": int(log["timeStamp"], 16)
        })

        if len(results) >= limit:
            break

    return results
