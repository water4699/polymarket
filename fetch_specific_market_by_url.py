#!/usr/bin/env python3
"""
根据Polymarket URL获取特定市场的详细信息和交易数据
针对URL: https://polymarket.com/event/btc-updown-15m-1767763800?tid=1767767121687
"""

import requests
import json
import os
from datetime import datetime, timedelta
from polygon import PolygonClient
from modules.api_key_manager import APIKeyManager
from config import config

# 配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PolymarketBot/1.0)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Origin": "https://polymarket.com",
    "Referer": "https://polymarket.com/"
}

GAMMA_BASE = "https://gamma-api.polymarket.com"
DATA_DIR = "data"

def get_event_by_slug(slug):
    """通过slug获取event详细信息"""
    url = f"{GAMMA_BASE}/events"
    params = {"slug": slug}
    
    print(f"🔍 获取event详情: {slug}")
    
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        events = r.json()
        
        if events and len(events) > 0:
            print(f"✅ 找到event: {events[0].get('title', 'Unknown')}")
            return events[0]
        else:
            print("❌ 未找到对应event")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取event失败: {e}")
        return None

def get_markets_by_event_id(event_id):
    """通过event ID获取相关市场"""
    url = f"{GAMMA_BASE}/events/{event_id}/markets"
    
    print(f"📊 获取event的市场列表: {event_id}")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        markets = r.json()
        
        print(f"✅ 找到 {len(markets)} 个市场")
        return markets
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取markets失败: {e}")
        return []

def get_market_details(market_id):
    """获取市场详细信息"""
    url = f"{GAMMA_BASE}/markets/{market_id}"
    
    print(f"📋 获取市场详情: {market_id}")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        market = r.json()
        
        print(f"✅ 获取市场详情成功")
        return market
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取市场详情失败: {e}")
        return None

def get_contract_addresses(market):
    """获取市场的合约地址信息"""
    contract_info = {}
    
    # Conditional Tokens条件ID
    condition_id = market.get("conditionId")
    if condition_id:
        contract_info["condition_id"] = condition_id
        # 在conditionId字段下添加合约地址信息
        contract_info["contract_addresses"] = {
            "conditional_tokens": "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",
            "clob_exchange": "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e", 
            "fee_module": "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"
        }
    
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
    
    return contract_info

def display_market_info(market):
    """显示市场信息"""
    print("\n" + "="*60)
    print("📊 比特币涨跌预测市场详情")
    print("="*60)
    
    print(f"🆔 Market ID: {market.get('id', 'N/A')}")
    print(f"🔗 Slug: {market.get('slug', 'N/A')}")
    print(f"❓ 问题: {market.get('question', 'N/A')}")
    
    # 时间信息
    created_at = market.get('createdAt', 'N/A')
    end_date = market.get('endDate', 'N/A')
    print(f"📅 创建时间: {created_at}")
    print(f"🏁 结束时间: {end_date}")
    
    # 交易信息
    volume = market.get('volumeNum', 0)
    liquidity = market.get('liquidityNum', 0)
    print(f"💰 交易量: ${volume:,.0f}")
    print(f"💧 流动性: ${liquidity:,.0f}")
    
    # 状态信息
    active = market.get('active', False)
    closed = market.get('closed', False)
    status = "活跃" if active else ("已关闭" if closed else "未知")
    print(f"📊 状态: {status}")
    
    # 结果信息
    outcomes = market.get('outcomes', [])
    outcome_prices = market.get('outcomePrices', [])
    print("\n🎯 选项赔率:")
    for i, outcome in enumerate(outcomes):
        try:
            price = float(outcome_prices[i]) if i < len(outcome_prices) else 0
            print(f"  • {outcome}: {price:.4f} ({price*100:.1f}%)")
        except:
            print(f"  • {outcome}: 暂无赔率")
    
    # 合约信息
    condition_id = market.get('conditionId', 'N/A')
    clob_tokens = market.get('clobTokenIds', 'N/A')
    print("\n🔗 合约信息:")
    print(f"  • Condition ID: {condition_id}")
    print(f"  • CLOb Token IDs: {clob_tokens}")
    
    # 合约地址
    contract_info = get_contract_addresses(market)
    if contract_info.get('contract_addresses'):
        print("\n🏛️ Polymarket合约地址:")
        for name, address in contract_info['contract_addresses'].items():
            print(f"  • {name}: {address}")

def get_time_range(market):
    """获取交易查询的时间范围"""
    created_at = market.get('createdAt', '')
    end_date = market.get('endDate', '')
    
    try:
        # 解析创建时间
        if created_at.endswith('Z'):
            start_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        else:
            start_time = datetime.fromisoformat(created_at)
        
        # 解析结束时间
        if end_date.endswith('Z'):
            end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_time = datetime.fromisoformat(end_date)
        
        # 扩展时间范围：从创建前1小时到结束后24小时
        start_time = start_time - timedelta(hours=1)
        end_time = end_time + timedelta(hours=24)
        
        print(f"📅 时间范围: {start_time.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return start_time, end_time
        
    except Exception as e:
        print(f"⚠️ 时间解析失败: {e}")
        # 默认时间范围：当前时间前后24小时
        now = datetime.now()
        return now - timedelta(hours=24), now + timedelta(hours=24)

def fetch_all_transactions(market, polygon_client):
    """获取该市场相关的所有交易"""
    print("\n🔄 开始获取Polygon交易数据...")
    
    # 获取时间范围
    start_time, end_time = get_time_range(market)
    
    # 获取合约地址
    condition_id = market.get('conditionId')
    clob_tokens = market.get('clobTokenIds')
    
    print(f"🔗 Condition ID: {condition_id}")
    print(f"🪙 CLOb Tokens: {clob_tokens}")
    
    all_transactions = {
        'metadata': {
            'market_id': market.get('id'),
            'market_question': market.get('question'),
            'market_slug': market.get('slug'),
            'condition_id': condition_id,
            'clob_token_ids': clob_tokens,
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'fetch_timestamp': datetime.now().isoformat(),
            'data_sources': []
        },
        'erc1155_transfers': [],
        'erc20_transfers': [],
        'contract_calls': []
    }
    
    try:
        # 1. 获取ERC-1155转账 (条件代币)
        if condition_id:
            print("\n🏷️ 获取ERC-1155转账...")
            erc1155_tx = polygon_client.fetch_erc1155_transfers(
                condition_id=condition_id,
                start_time=start_time,
                end_time=end_time
            )
            all_transactions['erc1155_transfers'] = erc1155_tx or []
            all_transactions['metadata']['data_sources'].append('erc1155_transfers')
            print(f"   ✅ ERC-1155转账: {len(all_transactions['erc1155_transfers'])} 条")
        
        # 2. 获取ERC-20转账 (USDC等)
        print("\n💰 获取ERC-20转账...")
        erc20_tx = polygon_client.fetch_erc20_transfers(
            start_time=start_time,
            end_time=end_time,
            # 可以指定特定的代币地址，如果知道的话
        )
        all_transactions['erc20_transfers'] = erc20_tx or []
        all_transactions['metadata']['data_sources'].append('erc20_transfers')
        print(f"   ✅ ERC-20转账: {len(all_transactions['erc20_transfers'])} 条")
        
        # 3. 获取合约调用 (Polymarket合约交互)
        print("\n⚙️ 获取合约调用...")
        contract_addresses = [
            "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045",  # Conditional Tokens
            "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",    # CLOb Exchange
            "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"     # Fee Module
        ]
        
        contract_calls = []
        for address in contract_addresses:
            print(f"   📡 查询合约: {address}")
            calls = polygon_client.fetch_contract_transactions(
                contract_address=address,
                start_time=start_time,
                end_time=end_time
            )
            if calls:
                contract_calls.extend(calls)
        
        all_transactions['contract_calls'] = contract_calls
        all_transactions['metadata']['data_sources'].append('contract_calls')
        print(f"   ✅ 合约调用: {len(all_transactions['contract_calls'])} 条")
        
        # 统计信息
        total_tx = len(all_transactions['erc1155_transfers']) + \
                  len(all_transactions['erc20_transfers']) + \
                  len(all_transactions['contract_calls'])
        
        print(f"\n📊 交易统计:")
        print(f"   ERC-1155转账: {len(all_transactions['erc1155_transfers'])} 条")
        print(f"   ERC-20转账: {len(all_transactions['erc20_transfers'])} 条")
        print(f"   合约调用: {len(all_transactions['contract_calls'])} 条")
        print(f"   总计: {total_tx} 条")
        
        return all_transactions
        
    except Exception as e:
        print(f"❌ 获取交易失败: {e}")
        return all_transactions

def save_data(data, filename):
    """保存数据到文件"""
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 数据已保存到: {filepath}")
        return filepath
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 获取特定Polymarket URL的市场信息和Polygon交易数据")
    print("="*65)
    
    # 从URL解析信息
    # URL: https://polymarket.com/event/btc-updown-15m-1767763800?tid=1767767121687
    slug = "btc-updown-15m-1767763800"
    
    # 1. 获取event信息
    event = get_event_by_slug(slug)
    if not event:
        print("❌ 无法获取event信息")
        return
    
    # 2. 获取event下的markets
    event_id = event.get('id')
    if event_id:
        markets = get_markets_by_event_id(event_id)
        
        if markets:
            # 通常event下只有一个market，取第一个
            market = markets[0]
            
            # 3. 添加合约地址信息
            contract_info = get_contract_addresses(market)
            market.update(contract_info)
            
            # 4. 显示市场信息
            display_market_info(market)
            
            # 5. 保存市场数据
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            market_filename = f"btc_updown_market_{timestamp}.json"
            save_data({
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'source_url': "https://polymarket.com/event/btc-updown-15m-1767763800?tid=1767767121687",
                    'fetch_method': "event_slug_lookup"
                },
                'market': market
            }, market_filename)
            
            # 6. 初始化Polygon客户端并获取交易数据
            try:
                print("\n🔧 初始化Polygon客户端...")
                key_manager = APIKeyManager(config.postgres_url)
                polygon_client = PolygonClient(key_manager, config)
                print("✅ Polygon客户端初始化成功")
                
                # 7. 获取所有交易数据
                transactions_data = fetch_all_transactions(market, polygon_client)
                
                # 8. 保存交易数据
                if transactions_data:
                    trades_filename = f"btc_updown_polygon_trades_{timestamp}.json"
                    save_data(transactions_data, trades_filename)
                    
                    print("\n✅ 完整数据获取完成！")
                    print(f"📄 市场数据: data/{market_filename}")
                    print(f"📄 交易数据: data/{trades_filename}")
                    
                    # 显示数据摘要
                    metadata = transactions_data['metadata']
                    print("\n📊 交易数据摘要:")
                    print(f"   市场ID: {metadata['market_id']}")
                    print(f"   问题: {metadata['market_question']}")
                    print(f"   时间范围: {metadata['time_range']['start']} 到 {metadata['time_range']['end']}")
                    print(f"   数据源: {', '.join(metadata['data_sources'])}")
                
            except Exception as e:
                print(f"❌ Polygon交易获取失败: {e}")
                print("💡 请检查API密钥配置和网络连接")
            
        else:
            print("❌ 该event下没有市场")
    else:
        print("❌ event ID无效")

if __name__ == "__main__":
    main()
