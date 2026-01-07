#!/usr/bin/env python3
"""
增强版批量ABI解码脚本 - 为Polymarket交易添加完整的ABI解码参数
支持所有Polymarket合约函数的解码
"""

import json
import os
from datetime import datetime
from eth_abi import decode_abi
from eth_utils import decode_hex


class EnhancedPolymarketABIDecoder:
    """增强版Polymarket ABI解码器"""
    
    def __init__(self):
        """初始化ABI解码器"""
        self.function_abis = {
            # matchOrders - 复杂订单匹配 (核心交易函数)
            '0x2287e350': {
                'name': 'matchOrders',
                'inputs': [
                    {
                        'name': 'takerOrder',
                        'type': 'tuple',
                        'components': [
                            {'name': 'salt', 'type': 'uint256'},
                            {'name': 'maker', 'type': 'address'},
                            {'name': 'signer', 'type': 'address'},
                            {'name': 'taker', 'type': 'address'},
                            {'name': 'tokenId', 'type': 'uint256'},
                            {'name': 'makerAmount', 'type': 'uint256'},
                            {'name': 'takerAmount', 'type': 'uint256'},
                            {'name': 'expiration', 'type': 'uint256'},
                            {'name': 'nonce', 'type': 'uint256'},
                            {'name': 'feeRateBps', 'type': 'uint256'},
                            {'name': 'side', 'type': 'uint8'},
                            {'name': 'signatureType', 'type': 'uint8'},
                            {'name': 'signature', 'type': 'bytes'}
                        ]
                    },
                    {
                        'name': 'makerOrders',
                        'type': 'tuple[]',
                        'components': [
                            {'name': 'salt', 'type': 'uint256'},
                            {'name': 'maker', 'type': 'address'},
                            {'name': 'signer', 'type': 'address'},
                            {'name': 'taker', 'type': 'address'},
                            {'name': 'tokenId', 'type': 'uint256'},
                            {'name': 'makerAmount', 'type': 'uint256'},
                            {'name': 'takerAmount', 'type': 'uint256'},
                            {'name': 'expiration', 'type': 'uint256'},
                            {'name': 'nonce', 'type': 'uint256'},
                            {'name': 'feeRateBps', 'type': 'uint256'},
                            {'name': 'side', 'type': 'uint8'},
                            {'name': 'signatureType', 'type': 'uint8'},
                            {'name': 'signature', 'type': 'bytes'}
                        ]
                    },
                    {'name': 'takerFillAmount', 'type': 'uint256'},
                    {'name': 'takerReceiveAmount', 'type': 'uint256'},
                    {'name': 'makerFillAmounts', 'type': 'uint256[]'},
                    {'name': 'takerFeeAmount', 'type': 'uint256'},
                    {'name': 'makerFeeAmounts', 'type': 'uint256[]'}
                ]
            },
            
            # registerToken - 代币注册
            '0x68c7450f': {
                'name': 'registerToken',
                'inputs': [
                    {'name': 'token', 'type': 'uint256'},
                    {'name': 'complement', 'type': 'uint256'},
                    {'name': 'metadata', 'type': 'bytes'}
                ]
            },
            
            # redeemPositions - 赎回仓位
            '0x01b7037c': {
                'name': 'redeemPositions',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address'},
                    {'name': 'parentCollectionId', 'type': 'bytes32'},
                    {'name': 'conditionId', 'type': 'bytes32'},
                    {'name': 'indexSets', 'type': 'uint256[]'}
                ]
            },
            
            # mergePositions - 合并仓位
            '0x9e7212ad': {
                'name': 'mergePositions',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address'},
                    {'name': 'parentCollectionId', 'type': 'bytes32'},
                    {'name': 'conditionId', 'type': 'bytes32'},
                    {'name': 'indexSets', 'type': 'uint256[]'},
                    {'name': 'amount', 'type': 'uint256'}
                ]
            },
            
            # setApprovalForAll - 批量授权
            '0xa22cb465': {
                'name': 'setApprovalForAll',
                'inputs': [
                    {'name': 'operator', 'type': 'address'},
                    {'name': 'approved', 'type': 'bool'}
                ]
            },
            
            # splitPosition - 拆分仓位
            '0x72ce4275': {
                'name': 'splitPosition',
                'inputs': [
                    {'name': 'collateralToken', 'type': 'address'},
                    {'name': 'parentCollectionId', 'type': 'bytes32'},
                    {'name': 'conditionId', 'type': 'bytes32'},
                    {'name': 'partition', 'type': 'uint256[]'},
                    {'name': 'amount', 'type': 'uint256'}
                ]
            },
            
            # prepareCondition - 准备条件
            '0x7b3b4c9d': {
                'name': 'prepareCondition',
                'inputs': [
                    {'name': 'oracle', 'type': 'address'},
                    {'name': 'questionId', 'type': 'bytes32'},
                    {'name': 'outcomeSlotCount', 'type': 'uint256'}
                ]
            },
            
            # reportPayouts - 报告结果
            '0xd712b918': {
                'name': 'reportPayouts',
                'inputs': [
                    {'name': 'questionId', 'type': 'bytes32'},
                    {'name': 'payouts', 'type': 'uint256[]'}
                ]
            },
            
            # safeTransferFrom - 安全转账
            '0x42842e0e': {
                'name': 'safeTransferFrom',
                'inputs': [
                    {'name': 'from', 'type': 'address'},
                    {'name': 'to', 'type': 'address'},
                    {'name': 'id', 'type': 'uint256'},
                    {'name': 'amount', 'type': 'uint256'},
                    {'name': 'data', 'type': 'bytes'}
                ]
            },
            
            # safeBatchTransferFrom - 批量安全转账
            '0x2eb2c2d6': {
                'name': 'safeBatchTransferFrom',
                'inputs': [
                    {'name': 'from', 'type': 'address'},
                    {'name': 'to', 'type': 'address'},
                    {'name': 'ids', 'type': 'uint256[]'},
                    {'name': 'amounts', 'type': 'uint256[]'},
                    {'name': 'data', 'type': 'bytes'}
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
                                    'data': struct_data[i].hex() if comp['type'] == 'bytes' and struct_data[i] else str(struct_data[i])
                                })
                    else:
                        array_data = decoded[param_idx]
                        for j, value in enumerate(array_data):
                            result.append({
                                'name': f"{inp['name']}[{j}]",
                                'type': inp['type'][:-2],
                                'data': str(value)
                            })
                else:
                    result.append({
                        'name': inp['name'],
                        'type': inp['type'],
                        'data': str(decoded[param_idx])
                    })
                
                param_idx += 1
            
            return result
            
        except Exception as e:
            return [{'error': f'解码失败: {e}'}]


def main():
    """主函数 - 增强版批量解码ABI参数"""
    print('🚀 增强版批量ABI解码脚本 - 为Polymarket交易添加完整参数')
    print('=' * 65)
    
    # 检查输入文件
    input_file = 'data/polymarket_complete_all_functions_decoded.json'
    output_file = 'data/polymarket_complete_all_functions_decoded_v2.json'
    
    if not os.path.exists(input_file):
        print(f'❌ 输入文件不存在: {input_file}')
        return
    
    print(f'📖 读取输入文件: {input_file}')
    
    # 读取数据
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    transactions = data['transactions']
    print(f'📊 总交易数: {len(transactions):,}')
    
    # 初始化解码器
    decoder = EnhancedPolymarketABIDecoder()
    supported_sigs = set(decoder.function_abis.keys())
    
    print(f'🔧 支持的函数签名: {len(supported_sigs)} 个')
    for sig, info in decoder.function_abis.items():
        print(f'   {sig}: {info["name"]}')
    
    # 统计当前解码状态
    current_decoded = sum(1 for tx in transactions if tx.get('decoded_input_data'))
    print(f'\\n📈 当前解码状态:')
    print(f'   已解码交易: {current_decoded:,}')
    print(f'   覆盖率: {current_decoded/len(transactions)*100:.1f}%')
    
    # 批量解码
    print('\\n🔄 开始增强解码...')
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
                    new_decoded_count += 1
                else:
                    error_msg = decoded_params[0].get('error', 'unknown') if decoded_params else 'decode failed'
                    print(f'   ⚠️ 解码失败 第{i+1}条: {error_msg}')
    
    print(f'\\n✅ 增强解码完成!')
    print(f'   新增解码交易: {new_decoded_count:,} 条')
    print(f'   跳过已解码: {skipped_count:,} 条')
    
    # 更新统计信息
    final_decoded = sum(1 for tx in transactions if tx.get('decoded_input_data'))
    data['total_decoded_functions'] = final_decoded
    data['supported_function_signatures'] = list(supported_sigs)
    data['enhancement_timestamp'] = datetime.now().isoformat()
    
    # 保存文件
    print(f'💾 保存增强版到: {output_file}')
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
    
    print('\\n✅ 增强版批量ABI解码脚本执行完成!')
    print(f'生成的增强数据文件: {output_file}')


if __name__ == '__main__':
    main()
