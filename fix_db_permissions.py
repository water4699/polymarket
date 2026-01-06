#!/usr/bin/env python3
"""
PostgreSQL权限修复脚本
使用管理员权限修复predictlab_user的数据库权限
"""

import subprocess
import sys
from pathlib import Path

def run_psql_command(command: str, as_admin: bool = True) -> bool:
    """运行psql命令"""
    try:
        if as_admin:
            # 使用当前用户作为管理员（macOS Homebrew PostgreSQL默认）
            cmd = ["psql", "-U", "mac", "-d", "polymarket", "-c", command]
        else:
            # 使用predictlab_user
            cmd = ["psql", "-U", "predictlab_user", "-d", "polymarket", "-c", command]

        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("✅ 命令执行成功")
            if result.stdout.strip():
                print(f"输出: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ 命令执行失败: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ 命令执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return False

def main():
    """主函数"""
    print("🔧 PostgreSQL权限修复工具")
    print("=" * 40)

    print("📋 执行步骤:")
    print("1. 检查数据库连接")
    print("2. 导入表结构和数据")
    print("3. 修复用户权限")
    print("4. 验证权限设置")
    print()

    # 步骤1: 检查管理员连接
    print("1️⃣ 检查管理员连接...")
    if not run_psql_command("SELECT version();", as_admin=True):
        print("❌ 无法连接到数据库，请确保PostgreSQL正在运行")
        return 1

    # 步骤2: 导入数据（如果表不存在）
    print("\n2️⃣ 导入表结构和数据...")
    sql_file = Path("db/import_etherscan_accounts.sql")
    if not sql_file.exists():
        print(f"❌ SQL文件不存在: {sql_file}")
        return 1

    try:
        cmd = ["psql", "-U", "mac", "-d", "polymarket", "-f", str(sql_file)]
        print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            print("✅ 数据导入成功")
        else:
            print(f"⚠️ 导入可能有警告: {result.stderr.strip()}")
            # 继续执行，因为可能是表已存在的警告

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return 1

    # 步骤3: 修复权限
    print("\n3️⃣ 修复用户权限...")

    permission_commands = [
        "GRANT ALL PRIVILEGES ON TABLE etherscan_accounts TO predictlab_user;",
        "GRANT ALL PRIVILEGES ON SCHEMA public TO predictlab_user;",
        "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO predictlab_user;",
        "GRANT ALL PRIVILEGES ON DATABASE polymarket TO predictlab_user;"
    ]

    for cmd in permission_commands:
        if not run_psql_command(cmd, as_admin=True):
            print(f"⚠️ 权限命令执行失败: {cmd}")
            # 继续执行其他命令

    # 步骤4: 验证权限
    print("\n4️⃣ 验证权限设置...")
    test_commands = [
        ("SELECT COUNT(*) FROM etherscan_accounts;", "检查表访问权限"),
        ("SELECT * FROM etherscan_accounts LIMIT 1;", "检查数据读取权限"),
    ]

    for cmd, desc in test_commands:
        print(f"验证: {desc}")
        if run_psql_command(cmd, as_admin=False):  # 使用predictlab_user测试
            print("✅ 权限正常")
        else:
            print("❌ 权限异常")

    print("\n🎉 权限修复完成！")
    print("现在可以运行: python3 test_api_manager.py")

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
