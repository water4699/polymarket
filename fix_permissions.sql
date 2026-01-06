-- ===========================================
-- PostgreSQL权限修复脚本
-- 解决API管理器的权限问题
-- ===========================================

-- 连接到polymarket数据库
-- \c polymarket

-- 1. 给数据库用户授权
GRANT ALL PRIVILEGES ON DATABASE polymarket TO predictlab_user;

-- 2. 给public schema授权
GRANT ALL PRIVILEGES ON SCHEMA public TO predictlab_user;

-- 3. 给etherscan_accounts表授权
GRANT ALL PRIVILEGES ON TABLE etherscan_accounts TO predictlab_user;

-- 4. 给序列授权（如果存在）
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO predictlab_user;

-- 5. 验证权限
SELECT
    grantee,
    privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'predictlab_user'
    AND table_name = 'etherscan_accounts';

-- 6. 检查表是否存在以及数据
SELECT COUNT(*) as total_accounts FROM etherscan_accounts;

-- 7. 显示样例数据
SELECT
    id,
    LEFT(api_key, 15) || '...' as api_key_short,
    daily_used,
    daily_limit,
    last_used
FROM etherscan_accounts
LIMIT 3;
