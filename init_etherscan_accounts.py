#!/usr/bin/env python3
"""
初始化 etherscan_accounts 表
创建表结构并添加示例API Keys
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api_key_manager import APIKeyManager, Base
from sqlalchemy import create_engine
from config import config

def init_etherscan_accounts():
    """初始化etherscan_accounts表"""

    print("🔧 初始化 etherscan_accounts 表...")

    # 创建数据库引擎
    engine = create_engine(config.postgres_url, echo=True)

    try:
        # 创建表
        print("📋 创建 etherscan_accounts 表...")
        Base.metadata.create_all(bind=engine)
        print("✅ 表创建成功")

        # 初始化API Key管理器
        manager = APIKeyManager(config.postgres_url)

        # 添加示例API Keys（用户需要替换为真实的）
        sample_keys = [
            "Your_PolygonScan_API_Key_1",  # 替换为真实Key
            "Your_PolygonScan_API_Key_2",  # 替换为真实Key
        ]

        print("🔑 添加示例API Keys...")
        added_count = 0
        for key in sample_keys:
            if key.startswith("Your_"):
                print(f"⚠️  请替换示例Key: {key}")
                continue

            try:
                manager.add_api_key(key)
                added_count += 1
                print(f"✅ 添加API Key: {key[:10]}...")
            except Exception as e:
                print(f"❌ 添加失败 {key[:10]}...: {e}")

        print(f"🎯 成功添加 {added_count} 个API Keys")

        # 显示使用统计
        stats = manager.get_usage_stats()
        print("📊 当前状态:"        print(f"   总Keys: {stats['total_keys']}")
        print(f"   可用Keys: {stats['available_keys']}")

        print("\\n✨ 初始化完成！")
        print("\\n📝 使用说明:")
        print("1. 在 https://polygonscan.com/apis 申请免费API Key")
        print("2. 替换上面的示例Keys为真实Keys")
        print("3. 重新运行此脚本")
        print("4. 运行 demo_usage.py 测试功能")

    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_etherscan_accounts()
