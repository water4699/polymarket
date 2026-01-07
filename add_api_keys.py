#!/usr/bin/env python3
"""
添加 API Keys 到现有的 etherscan_accounts 表
不需要创建表，只添加 API Keys
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.api_key_manager import APIKeyManager
from config import config

def add_api_keys():
    """添加API Keys到现有表"""

    print("🔑 添加 API Keys 到 etherscan_accounts 表...")

    try:
        # 初始化API Key管理器（连接现有表）
        manager = APIKeyManager(config.postgres_url)

        # 添加你的真实API Keys（从CSV文件提取）
        your_api_keys = [
            "QTZZ2KHYZTUHF9QE5FE1HTBDXCYFHPR3YG",
            "R54VRAG5WWBM7RBW3B7X55P8MIHAUGMZTB",
            "JREEQVQP634FE55RAUJX4XHK3QM2FB2RJY",
            "7QREA6S8ZE8YTAG346FMRQ14CKV9SFIXF8",
            "FM3WP9N5FXHISVXVBVU3HHV1JNB1D5MCAA",
            "AYX25AJCD8ZCF9RRU7DETQJFBV88R3788M",
            "MRJ59U6SFXY92Z21BH2PV8F6NIMCD87SKA",
            "TQIXKR1VYBPA7KUJ3D846NTIJ8IUX77J5T",
            "TQ1YUTCXJR3Z5X63147DHAX1MDHVQJC57J",
            "R3Q3KJEWXH2I7CWIRBFSTIBRHRJ4IB6A22",
            "QKYAZSVC8GY4TRGMA4ZCBHH761Q1THHIZ6",
            "S5WRIGE4IFS4IV9C4IST27AUGUFTCTEP65",
            "SHYBVG1JYJ43X2GK4X4U1YP2Y367XEZKFW",
            "QYDVDWBSK2YE46I2HBNN8KYCY9I9EJ36KV",
            "8H5F5JSWQB53SF9HWBBIQNQ1Y7PU79SUHP",
            "EFXYGYTFTBCU3RB6CRTDUA8UT84YJGJX59",
            "TXSQPXVBHC51MEYB8429NYHAV8JQY9XFDR",
            "WJRASUMJEZBMQZ9PZZ8AAKVAH5PEPEIDBZ",
            "XXAX3ZWZHP4RYRIS9ZAGJ6T7PAG7FYK7X6",
            "N4VJ62M137A52Q7IYFKZDCGY4B6NN2JGGN",
            "R7EDYPS7AEK2SVXCJN4GN585ZM2CW71VUZ",
            "ICZ1A37TNJA653I7WEQJBR29NQ5VDZ3NZB",
            "R6B5CAFNKMX3UVRZ8HBE91XBWIWT2GJ87M",
            "FZXNTDB85TW14A26XMXFIEGI862EQIF6DX",
            "JKZMI6BCZ6HFF6A3SKG9NIM1XMTHZUGDC1",
            "66AFY49MR5C9XXHNJ1CM9TR8VC37S4FV1F",
            "DB3H8ATAGBKSZD5CWQW3MX6FPYSM6IHTYM",
            "2ER9QCDWKXXMWPBUGHTFXH8GZSMSH7WEJG",
            "6CE2YJMF63336NZW17FPMUUEJFAM39FH7D",
            "UEUFKU8AKY6NSRKJZRRJ8G5MST9W39NQ7T",
            "Q3ZD5C98DK752AUVW7SIA5E2RTA4HNZAPH",
            "52BH6RJCSKQN5N8R5GKT5KPXMC25RRKXFJ",
            "JKTJ5QXCX8A5IUVZBES6JXKKRWV2PPEYNW",
            "CXHI7Z8JSQ5E4BTXEPJ7KKQ6Y2P3J71X2D",
            "WSC5RK6GAPJ5HUIXUP1DQTDWZIJRBWIJWA",
            "1MUUIZ89NDWM4665PPMQ76ZBP3IZUUMRKE",
            "YMWY9MID4UBUHU17ID9C1B93RZI6SZAVMX",
            "7HZEY5PBCZX52D4TZIJ5W5BWJJ1ANTFEXZ",
            "XHTWWZ9X3N81TPWFKTJRAJGFC15GM61TR6",
            "KW7NY51WT9A925B259DTRBG6D9VHFKRBYM",
            "V5U3CBAG6QK9CJD9WXYAERDXWIBY3TUN1H",
            "SKWP1F9B4ADZXI9MG8UV1ZFYTPQ14NQDC1",
            "BNG223N6K822G2UVK5U6T8PNBY4ZHVIG5V",
            "UHJHSC6PTV8N8PB6HTXU31V9U78BXUID8M",
            "Q6NJP1B16F8VBHYHFWMKPRAFJ6BAZMVAHZ",
            "8XMQE62PCNG26ZK1Z6VT6BX1KPBQXBBFNF",
            "PYFRDMAIT4PR8KB6ZN7999EP8GGF5JKIJC",
            "SNVBK2EITSWWQZ2BZRFPBEISHX5WE9I56V",
            "UTI13NSMNR13EE4D4YJ2FIJF6E313YU1YF",
            "QSVHIU93JP98GA9626DNZSNXC62938BSW6",
            "PQ2AUGJ5UD8BKVD4QVB2S84U2FD77QH94I",
            "VINDZQTVIB3HZ3IUF9BDUFK88D4DY4WY72",
            "MYA3GVX1I8BJV4M1FZ2K3FZAXUASHVP3K5",
            "HD21PITYEM5NEJP8X9E24YDE79QB27IS6Y",
            "TYECQQCTN6PCBRJNYSC7E321QMFU5T15VR",
            "KQJU5924UQ2R86USWEBTKMNU7M9CU228HJ",
            "9P1YXY3VKKAE85Y8E5UAX736WIA3X5QTBI",
            "PE17UUCCMUT9A4FY19HNX6Q5DPGAX797TE",
            "ZV833ZTP2DEKYCZ4KEJ6Y1AGMMT9VNPXG6",
            "3NC1S8HWUYY6EVFDAKTVUTICPZFCJQFGR4",
            "PFXD3IHJE3HWAFQFH41358229V3RVCC2VJ",
            "4AFZ6DRVFHUSNCY9K4E8NUZEM5FWCU7DXQ",
            "UHUPJDBTF7SGUGX17TQJFN9Y4RA2DD36MC",
            "GZG3WFUNI8BVFM6Q9W42IIFBR768KQK2FB",
            "CWVMMAA15VTEDP4IJZNUHHKT3PSS8SDHGH",
            "88A92ITW4Q1GJFIZIP41XZQU8DBA5QYDYP",
            "RGYH4CGR159VD4WQHC39BR7B3SIKHNIVKT",
            "FZQQMHK3AG28GR56IUBRT9I581XJE7G7QS",
            "ZFP8ZAV7YG2C18GUHUWIB76SVKSS4S9AWV",
            "NBQMDS8FJWZXGP2AYFQDACQ826WFPJZZZQ",
        ]

        print("🔑 添加API Keys...")
        added_count = 0
        for key in your_api_keys:
            if key.startswith("你的"):
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
        print("📊 当前状态:")
        print(f"   总Keys: {stats['total_keys']}")
        print(f"   可用Keys: {stats['available_keys']}")

        print("\\n✨ 添加完成！现在可以使用 Polygon 客户端了")

    except Exception as e:
        print(f"❌ 添加失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_api_keys()
