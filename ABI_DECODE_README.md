# Polymarket ABI 解码数据生成脚本

## 概述

这个脚本用于为 Polymarket 区块链交易数据生成完整的 ABI (Application Binary Interface) 解码参数，使原始的十六进制 `input_data` 转换为人类可读的参数信息。

## 生成的文件

- **输出文件**: `data/polymarket_complete_all_functions_decoded.json`
- **文件大小**: ~128MB
- **交易数量**: 29,993 条
- **解码覆盖率**: 66.3%

## 支持的函数类型

| 函数签名 | 函数名称 | 描述 | 数量 | 占比 |
|---------|---------|------|------|------|
| `0x2287e350` | matchOrders | 匹配taker订单与多个maker订单 | - | - |
| `0x01b7037c` | redeemPositions | 赎回预测仓位 | 8,198 | 27.3% |
| `0x9e7212ad` | mergePositions | 合并预测仓位 | 674 | 2.2% |
| `0x68c7450f` | registerToken | 注册预测代币 | - | - |
| `0xa22cb465` | setApprovalForAll | 设置批量授权 | 639 | 2.1% |
| `0x72ce4275` | splitPosition | 拆分预测仓位 | 365 | 1.2% |
| `0x2eb2c2d6` | safeBatchTransferFrom | 批量安全转账ERC1155代币 | 6 | 0.0% |

## 使用方法

### 1. 运行脚本

```bash
cd /Users/mac/Desktop/PredictLab
python3 generate_complete_abi_decoded_data.py
```

### 2. 查看结果

脚本会自动生成包含完整解码参数的 JSON 文件。

## 数据结构

### 交易对象结构

```json
{
  "type": "Contract_Transaction",
  "hash": "0x...",
  "timestamp": 1767770165,
  "datetime": "2026-01-07T15:16:05",
  "from": "0x...",
  "to": "0x...",
  "function": "matchOrders(tuple takerOrder,tuple[] makerOrders,...)",
  "contract_name": "Fee Module",
  "input_data": {
    "raw_input": "0x2287e350...",
    "decoded_input_data": [
      {
        "name": "takerOrder.salt",
        "type": "uint256",
        "description": "随机盐值",
        "data": "286805281"
      },
      {
        "name": "takerOrder.maker",
        "type": "address",
        "description": "maker地址", 
        "data": "0xc3d00f7afff3b1b7cc6505f5298b8179ad66f131"
      }
    ],
    "decoded_function_name": "matchOrders",
    "function_description": "匹配taker订单与多个maker订单"
  }
}
```

## 依赖项

```bash
pip install eth-abi eth-utils
```

## 脚本功能

1. **自动检测输入文件**: 从多个候选文件中选择可用的数据源
2. **增量解码**: 只处理未解码的交易，避免重复工作
3. **错误处理**: 对解码失败的交易进行标记和记录
4. **进度显示**: 每处理1000条交易显示一次进度
5. **统计报告**: 生成详细的解码统计信息

## 使用示例

### 查询特定函数的交易

```python
import json

# 读取数据
with open('data/polymarket_complete_all_functions_decoded.json', 'r') as f:
    data = json.load(f)

# 查找所有 redeemPositions 交易
redeem_tx = [
    tx for tx in data['transactions'] 
    if tx.get('decoded_function_name') == 'redeemPositions'
]

print(f"找到 {len(redeem_tx)} 条赎回交易")
```

### 分析交易参数

```python
# 查看第一条 redeemPositions 交易的参数
if redeem_tx:
    params = redeem_tx[0]['decoded_input_data']
    for param in params:
        print(f"{param['name']}: {param['data']}")
```

## 输出说明

- **total_decoded_functions**: 已解码的交易总数
- **supported_function_signatures**: 支持的函数签名列表  
- **function_descriptions**: 函数描述映射
- **last_updated**: 最后更新时间戳

## 注意事项

1. 脚本会自动跳过已解码的交易，提高处理效率
2. 某些复杂交易可能无法完全解码，会标记为 "unknown"
3. 解码过程可能需要几分钟时间，取决于数据量
4. 输出文件较大，建议使用支持大文件的编辑器查看
