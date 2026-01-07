#!/usr/bin/env python3
"""
完整ABI解码数据生成脚本 - 为Polymarket交易生成完整解码参数
生成文件: data/polymarket_complete_all_functions_decoded.json

使用方法:
1. 确保有基础交易数据文件
2. 运行: python3 generate_complete_abi_decoded_data.py
3. 生成包含完整ABI解码参数的JSON文件

依赖:
- eth-abi
- eth-utils
"""

import json
import os
from datetime import datetime
from eth_abi import decode_abi
from eth_utils import decode_hex


class CompletePolymarketABIDecoder:
    """完整的Polymarket ABI解码器"""
    
    def __init__(self):
        """初始化ABI解码器"""
        self.function_abis = {
            # matchOrders - 复杂订单匹配 (核心交易函数)
            '0x2287e350': {
                'name': 'matchOrders',
                'description': '匹配taker订单与多个maker订单',
                'inputs': [
                    {
                        'name': 'takerOrder',
                        'type': 'tuple',
                        'description': 'taker订单结构体',
                        'components': [
                            {'name': 'salt', 'type': 'uint256', 'description': '随机盐值'},
                            {'name': 'maker', 'type': 'address', 'description': 'maker地址'},
                            {'name': 'signer', 'type': 'address', 'description': '签名者地址'},
                            {'name': 'taker', 'type': 'address', 'description': 'taker地址'},
                            {'name': 'tokenId', 'type': 'uint256', 'description': '代币ID'},
                            {'name': 'makerAmount', 'type': 'uint256', 'description': 'maker数量'},
                            {'name': 'takerAmount', 'type': 'uint256', 'description': 'taker数量'},
                            {'name': 'expiration', 'type': 'uint256', 'description': '过期时间'},
                            {'name': 'nonce', 'type': 'uint256', 'description': 'nonce值'},
                            {'name': 'feeRateBps', 'type': 'uint256', 'description': '手续费率'},
                            {'name': 'side', 'type': 'uint8', 'description': '买卖方向'},
                            {'name': 'signatureType', 'type': 'uint8', 'description': '签名类型'},
                            {'name': 'signature', 'type': 'bytes', 'description': '签名数据'}
                        ]
                    },
                    {
                        'name': 'makerOrders',
                        'type': 'tuple[]',
                        'description': 'maker订单数组',
                        'components': [
                            {'name': 'salt', 'type': 'uint256', 'description': '随机盐值'},
                            {'name': 'maker', 'type': 'address', 'description': 'maker地址'},
                            {'name': 'signer', 'type': 'address', 'description': '签名者地址'},
                            {'name': 'taker', 'type': 'address', 'description': 'taker地址'},
                            {'name': 'tokenId', 'type': 'uint256', 'description': '代币ID'},
                            {'name': 'makerAmount', 'type': 'uint256', 'description': 'maker数量'},
                            {'name': 'takerAmount', 'type': 'uint256', 'description': 'taker数量'},
                            {'name': 'expiration', 'type': 'uint256', 'description': '过期时间'},
                            {'name': 'nonce', 'type': 'uint256', 'description': 'nonce值'},
                            {'name': 'feeRateBps', 'type': 'uint256', 'description': '手续费率'},
                            {'name': 'side', 'type': 'uint8', 'description': '买卖方向'},
                            {'name': 'signatureType', 'type': 'uint8', 'description': '签名类型'},
                            {'name': 'signature', 'type': 'bytes', 'description': '签名数据'}
                        ]
                    },
                    {'name': 'takerFillAmount', 'type': 'uint256', 'description': 'taker成交数量'},
                    {'name': 'takerReceiveAmount', 'type': 'uint256', 'description': 'taker接收数量'},
                    {'name': 'makerFillAmounts', 'type': 'uint256[]', 'description': 'maker成交数量数组'},
                    {'name': 'takerFeeAmount', 'type': 'uint256', 'description': 'taker手续费'},
                    {'name': 'makerFeeAmounts', 'type': 'uint256[]', 'description': 'maker手续费数组'}
                ]
            },
            
            # registerToken - 代币注册
            '0x68c7450f': {
                'name': 'registerToken',
                'description': '注册预测代币',
                'inputs': [
                    {'name': 'token', 'type': 'uint256', 'description': '代币ID'},
                    {'name': 'complement', 'type': 'uint256', 'description': '互补代币ID'},
                    {'name': 'metadata', 'type': 'bytes', 'description': '元数据'}
                ]
            },
            
            # redeemPositions - 赎回仓位
            '0x01b7037c': {
                'name': 'redeemPositions',
                'description': '赎回预测仓位',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address', 'description': '抵押代币地址'},
                    {'name': 'parentCollectionId', 'type': 'bytes32', 'description': '父集合ID'},
                    {'name': 'conditionId', 'type': 'bytes32', 'description': '条件ID'},
                    {'name': 'indexSets', 'type': 'uint256[]', 'description': '索引集合'}
                ]
            },
            
            # mergePositions - 合并仓位
            '0x9e7212ad': {
                'name': 'mergePositions',
                'description': '合并预测仓位',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address', 'description': '抵押代币地址'},
                    {'name': 'parentCollectionId', 'type': 'bytes32', 'description': '父集合ID'},
                    {'name': 'conditionId', 'type': 'bytes32', 'description': '条件ID'},
                    {'name': 'indexSets', 'type': 'uint256[]', 'description': '索引集合'},
                    {'name': 'amount', 'type': 'uint256', 'description': '合并数量'}
                ]
            },
            
            # setApprovalForAll - 批量授权
            '0xa22cb465': {
                'name': 'setApprovalForAll',
                'description': '设置批量授权',
                'inputs': [
                    {'name': 'operator', 'type': 'address', 'description': '操作者地址'},
                    {'name': 'approved', 'type': 'bool', 'description': '是否授权'}
                ]
            },
            
            # splitPosition - 拆分仓位
            '0x72ce4275': {
                'name': 'splitPosition',
                'description': '拆分预测仓位',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address', 'description': '抵押代币地址'},
                    {'name': 'parentCollectionId', 'type': 'bytes32', 'description': '父集合ID'},
                    {'name': 'conditionId', 'type': 'bytes32', 'description': '条件ID'},
                    {'name': 'partition', 'type': 'uint256[]', 'description': '分区数组'},
                    {'name': 'amount', 'type': 'uint256', 'description': '拆分数量'}
                ]
            },
            
            # prepareCondition - 准备条件
            '0x7b3b4c9d': {
                'name': 'prepareCondition',
                'description': '准备预测条件',
                'inputs': [
                    {'name': 'oracle', 'type': 'address', 'description': '预言机地址'},
                    {'name': 'questionId', 'type': 'bytes32', 'description': '问题ID'},
                    {'name': 'outcomeSlotCount', 'type': 'uint256', 'description': '结果插槽数量'}
                ]
            },
            
            # reportPayouts - 报告结果
            '0xd712b918': {
                'name': 'reportPayouts',
                'description': '报告支付结果',
                'inputs': [
                    {'name': 'questionId', 'type': 'bytes32', 'description': '问题ID'},
                    {'name': 'payouts', 'type': 'uint256[]', 'description': '支付数组'}
                ]
            },
            
            # safeTransferFrom - 安全转账
            '0x42842e0e': {
                'name': 'safeTransferFrom',
                'description': '安全转账ERC1155代币',
                'inputs': [
                    {'name': 'from', 'type': 'address', 'description': '发送地址'},
                    {'name': 'to', 'type': 'address', 'description': '接收地址'},
                    {'name': 'id', 'type': 'uint256', 'description': '代币ID'},
                    {'name': 'amount', 'type': 'uint256', 'description': '转账数量'},
                    {'name': 'data', 'type': 'bytes', 'description': '附加数据'}
                ]
            },
            
            # safeBatchTransferFrom - 批量安全转账
            '0x2eb2c2d6': {
                'name': 'safeBatchTransferFrom',
                'description': '批量安全转账ERC1155代币',
                'inputs': [
                    {'name': 'from', 'type': 'address', 'description': '发送地址'},
                    {'name': 'to', 'type': 'address', 'description': '接收地址'},
                    {'name': 'ids', 'type': 'uint256[]', 'description': '代币ID数组'},
                    {'name': 'amounts', 'type': 'uint256[]', 'description': '转账数量数组'},
                    {'name': 'data', 'type': 'bytes', 'description': '附加数据'}
                ]
            }
        }
    
    def decode_function_input(self, input_hex):
        """解码函数输入数据"""
        if not input_hex or len(input_hex) < 10:
            return None
            
        method_sig = input_hex[:10]
        
        if method_sig not in self.function_abis:
            return None
            
        func_abi = self.function_abis[method_sig]
        
        try:
            input_bytes = decode_hex(input_hex)
            data_bytes = input_bytes[4:]  # 移除方法签名
            
            # 构建类型字符串
            types = []
            for inp in func_abi['inputs']:
                if inp['type'] == 'tuple':
                    components = inp['components']
                    component_types = [comp['type'] for comp in components]
                    types.append(f"({','.join(component_types)})")
                elif inp['type'].endswith('[]'):
                    base_type = inp['type'][:-2]
                    if base_type == 'tuple':
                        components = inp['components']
                        component_types = [comp['type'] for comp in components]
                        types.append(f"({','.join(component_types)})[]")
                    else:
                        types.append(inp['type'])
                else:
                    types.append(inp['type'])
            
            decoded = decode_abi(types, data_bytes)
            
            # 构建参数列表
            result = []
            param_idx = 0
            
            for inp in func_abi['inputs']:
                if inp['type'] == 'tuple':
                    struct_data = decoded[param_idx]
                    for i, comp in enumerate(inp['components']):
                        result.append({
                            'name': f"{inp['name']}.{comp['name']}",
                            'type': comp['type'],
                            'description': comp.get('description', ''),
                            'data': struct_data[i].hex() if comp['type'] == 'bytes' and struct_data[i] else str(struct_data[i])
                        })
                elif inp['type'].endswith('[]'):
                    if inp['type'] == 'tuple[]':
                        array_data = decoded[param_idx]
                        for j, struct_data in enumerate(array_data):
                            for i, comp in enumerate(inp['components']):
                                result.append({
                                    'name': f"{inp['name']}[{j}].{comp['name']}",
                                    'type': comp['type'],
                                    'description': comp.get('description', ''),
                                    'data': struct_data[i].hex() if comp['type'] == 'bytes' and struct_data[i] else str(struct_data[i])
                                })
                    else:
                        array_data = decoded[param_idx]
                        for j, value in enumerate(array_data):
                            result.append({
                                'name': f"{inp['name']}[{j}]",
                                'type': inp['type'][:-2],
                                'description': inp.get('description', ''),
                                'data': str(value)
                            })
                else:
                    result.append({
                        'name': inp['name'],
                        'type': inp['type'],
                        'description': inp.get('description', ''),
                        'data': str(decoded[param_idx])
                    })
                
                param_idx += 1
            
            return result
            
        except Exception as e:
            return [{'error': f'解码失败: {e}'}]


def find_input_data_file():
    """查找可用的输入数据文件"""
    candidates = [
        'data/polymarket_complete_all_functions_decoded.json',
        'data/polymarket_complete_with_decoded_input.json',
        'data/complete_btc_updown_trades_20260107_145018.json'
    ]
    
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    
    return None


def main():
    """主函数 - 生成完整ABI解码数据"""
    print('🚀 完整ABI解码数据生成脚本')
    print('=' * 50)
    
    # 查找输入文件
    input_file = find_input_data_file()
    if not input_file:
        print('❌ 未找到可用的输入数据文件')
        print('请确保以下文件之一存在:')
        print('  - data/polymarket_complete_all_functions_decoded.json')
        print('  - data/polymarket_complete_with_decoded_input.json')
        print('  - data/complete_btc_updown_trades_20260107_145018.json')
        return
    
    output_file = 'data/polymarket_complete_all_functions_decoded.json'
    
    print(f'📖 读取输入文件: {input_file}')
    
    # 读取数据
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    transactions = data['transactions']
    print(f'📊 总交易数: {len(transactions):,}')
    
    # 初始化解码器
    decoder = CompletePolymarketABIDecoder()
    supported_sigs = set(decoder.function_abis.keys())
    
    print(f'🔧 支持的函数签名: {len(supported_sigs)} 个')
    for sig, info in decoder.function_abis.items():
        print(f'   {sig}: {info["name"]} - {info["description"]}')
    
    # 统计当前解码状态
    current_decoded = sum(1 for tx in transactions if tx.get('decoded_input_data'))
    print(f'\\n📈 当前解码状态:')
    print(f'   已解码交易: {current_decoded:,}')
    print(f'   覆盖率: {current_decoded/len(transactions)*100:.1f}%')
    
    # 批量解码
    print('\\n🔄 开始完整解码...')
    new_decoded_count = 0
    skipped_count = 0
    
    for i, tx in enumerate(transactions):
        input_data = tx.get('input_data', {})
        raw_input = input_data.get('raw_input', '')
        
        if raw_input and len(raw_input) >= 10:
            method_sig = raw_input[:10]
            
            # 跳过已解码的交易
            if tx.get('decoded_input_data'):
                skipped_count += 1
                continue
                
            # 解码支持的函数
            if method_sig in supported_sigs:
                if (i + 1) % 1000 == 0:  # 每1000条显示进度
                    print(f'   处理到第 {i+1:,} 条交易...')
                
                decoded_params = decoder.decode_function_input(raw_input)
                
                if decoded_params and not any(p.get('error') for p in decoded_params):
                    tx['decoded_input_data'] = decoded_params
                    tx['decoded_function_name'] = decoder.function_abis[method_sig]['name']
                    tx['function_description'] = decoder.function_abis[method_sig]['description']
                    new_decoded_count += 1
                else:
                    error_msg = decoded_params[0].get('error', 'unknown') if decoded_params else 'decode failed'
                    print(f'   ⚠️ 解码失败 第{i+1}条: {error_msg}')
    
    print(f'\\n✅ 完整解码完成!')
    print(f'   新增解码交易: {new_decoded_count:,} 条')
    print(f'   跳过已解码: {skipped_count:,} 条')
    
    # 更新统计信息
    final_decoded = sum(1 for tx in transactions if tx.get('decoded_input_data'))
    data['total_decoded_functions'] = final_decoded
    data['supported_function_signatures'] = list(supported_sigs)
    data['function_descriptions'] = {sig: info['description'] for sig, info in decoder.function_abis.items()}
    data['last_updated'] = datetime.now().isoformat()
    
    # 保存文件
    print(f'💾 保存完整数据到: {output_file}')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 验证文件
    file_size = os.path.getsize(output_file)
    print(f'📄 文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)')
    
    print(f'\\n🎯 最终结果:')
    print(f'   总交易数: {len(transactions):,}')
    print(f'   已解码交易: {final_decoded:,}')
    print(f'   解码覆盖率: {final_decoded/len(transactions)*100:.1f}%')
    print(f'   新增解码率: {new_decoded_count/len(transactions)*100:.1f}%')
    
    # 统计函数类型
    function_stats = {}
    for tx in transactions:
        if tx.get('decoded_input_data'):
            func_name = tx.get('decoded_function_name', 'unknown')
            function_stats[func_name] = function_stats.get(func_name, 0) + 1
    
    print(f'\\n🔧 函数类型统计:')
    for func_name, count in sorted(function_stats.items(), key=lambda x: x[1], reverse=True):
        desc = decoder.function_abis.get(list(decoder.function_abis.keys())[list(decoder.function_abis.values()).index({'name': func_name, **decoder.function_abis[list(decoder.function_abis.keys())[0]]})], {}).get('description', '') if func_name != 'unknown' else ''
        print(f'   {func_name}: {count:,} ({count/final_decoded*100:.1f}%) - {desc}')
    
    print('\\n✅ 完整ABI解码数据生成完成!')
    print(f'📄 输出文件: {output_file}')
    print('\\n💡 使用提示:')
    print('  - 查看解码参数: data["transactions"][i]["decoded_input_data"]')
    print('  - 查询特定函数: 按 decoded_function_name 过滤')
    print('  - 分析交易模式: 统计各函数调用频率')


if __name__ == '__main__':
    main()
