#!/bin/bash

echo "🎯 PostgreSQL 最终永久修复脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 停止所有可能存在的PostgreSQL进程
echo -e "${YELLOW}1. 清理所有PostgreSQL进程...${NC}"
pkill -9 postgres 2>/dev/null || true
pkill -9 postmaster 2>/dev/null || true
sleep 2

# 停止所有brew服务
echo -e "${YELLOW}2. 停止所有brew PostgreSQL服务...${NC}"
brew services stop postgresql@14 2>/dev/null || true
brew services stop postgresql@15 2>/dev/null || true
sleep 2

# 使用brew services启动PostgreSQL@15
echo -e "${YELLOW}3. 使用brew services启动PostgreSQL@15...${NC}"
brew services start postgresql@15

# 等待服务启动
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo -e "${YELLOW}4. 检查brew服务状态...${NC}"
SERVICE_STATUS=$(brew services list | grep postgresql@15)
if echo "$SERVICE_STATUS" | grep -q "started"; then
    echo -e "${GREEN}✅ brew服务状态正常${NC}"
else
    echo -e "${RED}❌ brew服务启动失败${NC}"
    echo "$SERVICE_STATUS"
    exit 1
fi

# 测试数据库连接
echo -e "${YELLOW}5. 测试数据库连接...${NC}"
if /opt/homebrew/opt/postgresql@15/bin/psql -U "$USER" -d postgres -c "SELECT version();" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 数据库连接成功${NC}"

    # 检查polymarket数据库
    if /opt/homebrew/opt/postgresql@15/bin/psql -U "$USER" -d postgres -l | grep -q polymarket; then
        echo -e "${GREEN}✅ polymarket数据库存在${NC}"

        # 测试数据
        MARKET_COUNT=$(/opt/homebrew/opt/postgresql@15/bin/psql -U "$USER" -d polymarket -t -c "SELECT COUNT(*) FROM markets;" 2>/dev/null || echo "0")
        if [ "$MARKET_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✅ 数据库包含 $MARKET_COUNT 个市场数据${NC}"
        else
            echo -e "${YELLOW}⚠️ 数据库为空，需要重新导入数据${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ polymarket数据库不存在，创建中...${NC}"
        /opt/homebrew/opt/postgresql@15/bin/createdb polymarket 2>/dev/null || true
    fi

else
    echo -e "${RED}❌ 数据库连接失败${NC}"
    exit 1
fi

echo
echo -e "${GREEN}🎉 PostgreSQL永久修复完成！${NC}"
echo
echo "📋 服务信息:"
echo "   • 状态: $(brew services list | grep postgresql@15)"
echo "   • 用户: $USER"
echo "   • 数据库: polymarket"
echo "   • 端口: 5432"
echo
echo "🔄 现在可以正常使用:"
echo "   psql -U $USER -d polymarket"
echo "   python3 import_polymarket_data.py"
echo "   python3 test_raw_json_storage.py"
echo
echo "💡 服务管理:"
echo "   • 启动: brew services start postgresql@15"
echo "   • 停止: brew services stop postgresql@15"
echo "   • 重启: brew services restart postgresql@15"
echo "   • 状态: brew services list | grep postgresql"

echo
echo -e "${GREEN}✅ PostgreSQL现在会在系统启动时自动运行！${NC}"

