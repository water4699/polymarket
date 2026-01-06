# PredictLab 数据库迁移指南

PredictLab 使用 Alembic 进行数据库迁移和版本控制，提供完整的三层数据架构管理。

## 📋 目录

- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [基本命令](#基本命令)
- [迁移管理](#迁移管理)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install alembic sqlalchemy psycopg2-binary
```

### 2. 初始化数据库

```bash
# 开发环境
python migration_manager.py status --env development
python migration_manager.py upgrade --env development

# 测试环境
python migration_manager.py status --env testing
python migration_manager.py upgrade --env testing

# 生产环境（需要设置 DATABASE_URL）
export DATABASE_URL="postgresql://user:pass@host:port/db"
python migration_manager.py status --env production
python migration_manager.py upgrade --env production
```

### 3. 创建新迁移

```bash
# 自动生成迁移（推荐）
python migration_manager.py create --message "添加新功能字段"

# 手动创建迁移
python migration_manager.py create --message "自定义迁移" --no-auto-generate
```

## 🌍 环境配置

### 支持的环境

- **development**: 开发环境，用于日常开发
- **testing**: 测试环境，用于自动化测试
- **staging**: 暂存环境，用于集成测试
- **production**: 生产环境，线上正式环境

### 环境变量

```bash
# 设置当前环境
export PREDICTLAB_ENV=development

# 生产环境数据库URL（必需）
export DATABASE_URL="postgresql://user:password@host:5432/database"

# 测试环境数据库URL（可选）
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/predictlab_test"

# 备份配置（生产环境）
export BACKUP_BUCKET="my-backup-bucket"
export AWS_REGION="us-east-1"
```

### 查看环境信息

```bash
# 查看当前环境配置
python alembic/environments.py

# 查看特定环境
python alembic/environments.py production
```

## 🛠️ 基本命令

### 迁移管理器

```bash
# 查看帮助
python migration_manager.py --help

# 检查状态
python migration_manager.py status --env development

# 升级到最新版本
python migration_manager.py upgrade --env development

# 升级到指定版本
python migration_manager.py upgrade --revision 002 --env development

# 回滚到指定版本
python migration_manager.py downgrade --revision 001 --env development

# 查看迁移历史
python migration_manager.py history --env development

# 创建新迁移
python migration_manager.py create --message "添加用户表" --env development

# 备份数据库
python migration_manager.py backup --env production
```

### 原始 Alembic 命令

```bash
# 查看当前版本
alembic current

# 查看所有版本
alembic heads

# 查看迁移历史
alembic history

# 生成迁移（自动检测模型变化）
alembic revision --autogenerate -m "消息"

# 手动创建迁移
alembic revision -m "消息"

# 升级
alembic upgrade head

# 降级
alembic downgrade -1
```

## 📊 迁移管理

### 三层数据架构

PredictLab 使用三层数据架构，每层都有对应的表：

#### Raw Layer (原始数据层)
- `raw_market_data`: 市场原始数据
- `raw_onchain_data`: 链上交易原始数据

#### Clean Layer (清洗数据层)
- `clean_market_data`: 清洗后的市场数据
- `clean_kline_data`: K线数据
- `clean_onchain_transactions`: 链上交易数据

#### Feature Layer (特征数据层)
- `feature_technical_indicators`: 技术指标
- `feature_market_stats`: 市场统计
- `feature_onchain_metrics`: 链上指标

### 元数据表
- `metadata_data_sources`: 数据源配置
- `metadata_symbols`: 资产配置
- `metadata_data_quality`: 数据质量监控
- `metadata_validation_history`: 校验历史

### 增量迁移示例

#### 添加新字段

```python
def upgrade():
    op.add_column('clean_market_data',
        sa.Column('new_field', sa.String(length=100), nullable=True)
    )

def downgrade():
    op.drop_column('clean_market_data', 'new_field')
```

#### 添加新表

```python
def upgrade():
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('new_table')
```

#### 修改字段类型

```python
def upgrade():
    # PostgreSQL 兼容的类型修改
    op.execute('ALTER TABLE table_name ALTER COLUMN column_name TYPE new_type')

def downgrade():
    op.execute('ALTER TABLE table_name ALTER COLUMN column_name TYPE old_type')
```

## 📈 最佳实践

### 1. 迁移命名规范

```bash
# 好的命名
python migration_manager.py create --message "add_user_authentication_fields"
python migration_manager.py create --message "create_api_rate_limit_table"
python migration_manager.py create --message "add_data_validation_indexes"

# 不好的命名
python migration_manager.py create --message "fix"
python migration_manager.py create --message "update"
```

### 2. 迁移文件结构

```python
"""
添加用户认证字段
为用户表添加登录相关字段

Revision ID: 003
Revises: 002
Create Date: 2024-01-16 14:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'

def upgrade():
    # 正向迁移
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))

def downgrade():
    # 反向迁移
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'password_hash')
```

### 3. 环境隔离

- **开发环境**: 可以使用自动生成迁移，允许破坏性变更
- **测试环境**: 定期重置，使用最新迁移
- **暂存环境**: 手动审核迁移，不允许自动生成
- **生产环境**: 严格控制，只运行预测试迁移

### 4. 数据安全

```python
# 安全的数据迁移
def upgrade():
    # 1. 创建新表
    op.create_table('temp_users', ...)

    # 2. 迁移数据
    op.execute("""
        INSERT INTO temp_users (id, name, email)
        SELECT id, name, email FROM users
    """)

    # 3. 重命名表
    op.rename_table('users', 'users_old')
    op.rename_table('temp_users', 'users')

    # 4. 清理
    op.drop_table('users_old')

def downgrade():
    # 恢复原始状态
    op.rename_table('users', 'temp_users')
    op.rename_table('users_old', 'users')
    op.drop_table('temp_users')
```

### 5. 索引优化

```python
def upgrade():
    # 添加索引前检查数据量
    op.create_index('idx_large_table_field',
                   'large_table',
                   ['field'],
                   postgresql_concurrently=True)  # 并发创建，不阻塞

def downgrade():
    op.drop_index('idx_large_table_field', table_name='large_table')
```

## 🔧 故障排除

### 常见问题

#### 1. 迁移文件冲突

```bash
# 检查冲突
alembic heads

# 合并分支
alembic merge heads

# 强制解决（谨慎使用）
alembic revision --rev-id <new_id>
```

#### 2. 数据库连接问题

```bash
# 检查连接
python -c "from config import config; print('Connected' if config.postgres_url else 'Not configured')"

# 测试连接
python -c "from modules.data_storage.postgres_storage import PostgresStorage; s = PostgresStorage(); print(s.connect())"
```

#### 3. 迁移失败回滚

```bash
# 查看当前状态
python migration_manager.py status --env development

# 回滚一步
python migration_manager.py downgrade --revision -1 --env development

# 强制标记版本（紧急情况）
alembic stamp <revision_id>
```

#### 4. 生产环境迁移

```bash
# 1. 创建备份
python migration_manager.py backup --env production

# 2. 进入维护模式
# （应用层实现）

# 3. 运行迁移
python migration_manager.py upgrade --env production

# 4. 验证数据
python -c "from data_manager import DataManager; dm = DataManager(); dm.verify_migration()"

# 5. 退出维护模式
```

### 调试技巧

```bash
# 启用详细日志
export ALEMBIC_LOG_LEVEL=DEBUG

# 查看 SQL 语句
alembic upgrade --sql head

# 离线模式（不连接数据库）
alembic upgrade head --sql > migration.sql
```

## 📝 迁移模板

### 新功能迁移模板

```python
"""
添加 [功能名称]
[详细描述变更内容]

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: [自动生成]
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade():
    """正向迁移"""
    # 添加字段
    # 创建表
    # 修改数据
    pass

def downgrade():
    """反向迁移"""
    # 逆操作
    pass
```

### 数据迁移模板

```python
def upgrade():
    """数据迁移"""
    # 使用 op.execute() 执行原始 SQL
    op.execute("""
        UPDATE table_name
        SET new_column = CASE
            WHEN old_column = 'value1' THEN 'new_value1'
            WHEN old_column = 'value2' THEN 'new_value2'
            ELSE old_column
        END
    """)

def downgrade():
    """数据回滚"""
    op.execute("""
        UPDATE table_name
        SET old_column = CASE
            WHEN new_column = 'new_value1' THEN 'value1'
            WHEN new_column = 'new_value2' THEN 'value2'
            ELSE new_column
        END
    """)
```

## 🔒 安全考虑

1. **备份策略**: 生产环境迁移前必须备份
2. **审核流程**: 生产迁移需要人工审核
3. **回滚计划**: 每个迁移必须有明确的回滚方案
4. **测试验证**: 新迁移必须在测试环境验证
5. **监控告警**: 迁移过程需要监控和告警

## 📞 支持

如遇到问题，请：

1. 查看日志文件：`logs/alembic.log`
2. 检查数据库状态：`python migration_manager.py status`
3. 查看迁移历史：`python migration_manager.py history`
4. 参考本文档的故障排除部分

---

*最后更新: 2024-01-16*
