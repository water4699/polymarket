#!/usr/bin/env python3
"""
PredictLab 数据库迁移模板
提供常用的迁移模式和最佳实践示例
"""
from typing import Dict, List, Any, Optional
from datetime import datetime


class MigrationTemplate:
    """迁移模板生成器"""

    @staticmethod
    def create_add_column_template(table_name: str, column_name: str,
                                 column_type: str, nullable: bool = True,
                                 default: Optional[str] = None,
                                 comment: Optional[str] = None) -> str:
        """添加字段模板"""
        template = f'''"""
添加字段 {column_name} 到表 {table_name}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """添加字段 {column_name}"""
    op.add_column('{table_name}',
        sa.Column('{column_name}', {column_type}, nullable={str(nullable).lower()}'''

        if default:
            template += f",\n                 server_default=sa.text('{default}')"

        if comment:
            template += f",\n                 comment='{comment}'"

        template += '''
    )

def downgrade() -> None:
    """移除字段 {column_name}"""
    op.drop_column('{table_name}', '{column_name}')
'''

        return template

    @staticmethod
    def create_add_index_template(table_name: str, index_name: str,
                                columns: List[str], unique: bool = False,
                                concurrent: bool = True) -> str:
        """添加索引模板"""
        columns_str = ', '.join([f"'{col}'" for col in columns])

        concurrent_note = ""
        if concurrent:
            concurrent_note = "\n    # 注意：生产环境使用 CONCURRENTLY 创建索引，避免阻塞"

        template = f'''"""
为表 {table_name} 添加索引 {index_name}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """添加索引 {index_name}"""{concurrent_note}
    op.create_index('{index_name}', '{table_name}',
                   [{columns_str}], unique={str(unique).lower()}'''

        if concurrent:
            template += ''',
                   postgresql_concurrently=True'''

        template += '''
    )

def downgrade() -> None:
    """移除索引 {index_name}"""
    op.drop_index('{index_name}', table_name='{table_name}')
'''

        return template

    @staticmethod
    def create_create_table_template(table_name: str, columns: List[Dict[str, Any]],
                                   indexes: Optional[List[Dict[str, Any]]] = None) -> str:
        """创建表模板"""
        columns_code = []
        for col in columns:
            col_def = f"        sa.Column('{col['name']}', {col['type']}, nullable={str(col.get('nullable', True)).lower()}"
            if 'default' in col:
                col_def += f", server_default=sa.text('{col['default']}')"
            if 'comment' in col:
                col_def += f", comment='{col['comment']}'"
            col_def += ")"
            columns_code.append(col_def)

        columns_str = ',\n'.join(columns_code)

        indexes_code = ""
        if indexes:
            indexes_code = "\n    # 创建索引\n"
            for idx in indexes:
                idx_columns = ', '.join([f"'{col}'" for col in idx['columns']])
                indexes_code += f"    op.create_index('{idx['name']}', '{table_name}', [{idx_columns}], unique={str(idx.get('unique', False)).lower()})\n"

        drop_indexes_code = ""
        if indexes:
            drop_indexes_code = "\n    # 删除索引\n"
            for idx in indexes:
                drop_indexes_code += f"    op.drop_index('{idx['name']}', table_name='{table_name}')\n"

        template = f'''"""
创建表 {table_name}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """创建表 {table_name}"""
    op.create_table('{table_name}',
{columns_str}
    ){indexes_code}

def downgrade() -> None:
    """删除表 {table_name}"""{drop_indexes_code}
    op.drop_table('{table_name}')
'''

        return template

    @staticmethod
    def create_data_migration_template(description: str, upgrade_sql: str,
                                     downgrade_sql: str) -> str:
        """数据迁移模板"""
        template = f'''"""
{description}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """{description}"""
    # 执行数据迁移
    op.execute("""
{upgrade_sql}
    """)

def downgrade() -> None:
    """回滚数据迁移"""
    op.execute("""
{downgrade_sql}
    """)
'''

        return template

    @staticmethod
    def create_safe_table_rename_template(old_table: str, new_table: str) -> str:
        """安全表重命名模板（带数据迁移）"""
        template = f'''"""
重命名表 {old_table} 为 {new_table}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """重命名表 {old_table} -> {new_table}"""
    # 使用安全的重命名方式（PostgreSQL 兼容）
    op.execute(f'ALTER TABLE {old_table} RENAME TO {new_table}')

    # 更新相关约束和索引名称（如果需要）
    # op.execute(f'ALTER INDEX idx_{old_table}_field RENAME TO idx_{new_table}_field')

def downgrade() -> None:
    """重命名表 {new_table} -> {old_table}"""
    op.execute(f'ALTER TABLE {new_table} RENAME TO {old_table}')

    # 恢复约束和索引名称
    # op.execute(f'ALTER INDEX idx_{new_table}_field RENAME TO idx_{old_table}_field')
'''

        return template

    @staticmethod
    def create_enum_migration_template(table_name: str, column_name: str,
                                     old_enum: List[str], new_enum: List[str]) -> str:
        """枚举类型迁移模板"""
        old_values = ', '.join([f"'{v}'" for v in old_enum])
        new_values = ', '.join([f"'{v}'" for v in new_enum])

        template = f'''"""
更新表 {table_name} 的枚举字段 {column_name}

Revision ID: [自动生成]
Revises: [前一版本]
Create Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '[自动生成]'
down_revision = '[前一版本]'

def upgrade() -> None:
    """更新枚举类型"""
    # 创建新的枚举类型
    op.execute(f"CREATE TYPE {column_name}_enum_new AS ENUM({new_values})")

    # 添加新列
    op.add_column('{table_name}',
        sa.Column('{column_name}_new', sa.Enum({', '.join([f"'{v}'" for v in new_enum])},
                                               name=f'{column_name}_enum_new'),
                 nullable=True)
    )

    # 迁移数据
    op.execute("""
        UPDATE {table_name}
        SET {column_name}_new = {column_name}::{column_name}_enum_new
        WHERE {column_name} IN ({old_values})
    """)

    # 删除旧列
    op.drop_column('{table_name}', '{column_name}')

    # 重命名新列
    op.alter_column('{table_name}', '{column_name}_new',
                   new_column_name='{column_name}')

    # 删除旧枚举类型
    op.execute(f"DROP TYPE {column_name}_enum_old")

def downgrade() -> None:
    """回滚枚举类型"""
    # 类似的反向操作...
    pass
'''

        return template


class MigrationValidator:
    """迁移验证器"""

    @staticmethod
    def validate_migration_file(file_path: str) -> Dict[str, Any]:
        """验证迁移文件"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检查必需的结构
            if 'revision:' not in content:
                issues.append("缺少 revision 标识符")

            if 'down_revision:' not in content:
                issues.append("缺少 down_revision 标识符")

            if 'def upgrade():' not in content:
                issues.append("缺少 upgrade 函数")

            if 'def downgrade():' not in content:
                issues.append("缺少 downgrade 函数")

            # 检查潜在问题
            if 'DROP TABLE' in content.upper() and 'CASCADE' not in content.upper():
                issues.append("DROP TABLE 操作可能需要 CASCADE")

            if 'DELETE FROM' in content.upper() and 'WHERE' not in content.upper():
                issues.append("DELETE 操作缺少 WHERE 条件，可能删除所有数据")

        except Exception as e:
            issues.append(f"文件读取错误: {e}")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'file_path': file_path
        }

    @staticmethod
    def check_migration_conflicts(migration_dir: str) -> List[Dict[str, Any]]:
        """检查迁移冲突"""
        conflicts = []
        # 实现冲突检测逻辑
        return conflicts


class BestPractices:
    """迁移最佳实践"""

    @staticmethod
    def get_checklist() -> Dict[str, List[str]]:
        """获取迁移检查清单"""
        return {
            'before_migration': [
                '备份数据库',
                '检查磁盘空间',
                '通知相关团队',
                '准备回滚计划',
                '验证测试环境',
                '检查依赖服务'
            ],
            'during_migration': [
                '监控系统资源',
                '记录迁移日志',
                '检查数据完整性',
                '准备应急方案',
                '监控业务指标'
            ],
            'after_migration': [
                '验证数据一致性',
                '运行集成测试',
                '更新文档',
                '监控系统性能',
                '准备回滚验证'
            ]
        }

    @staticmethod
    def generate_migration_plan(changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成迁移计划"""
        plan = {
            'estimated_duration': 'TBD',
            'risk_level': 'medium',
            'rollback_complexity': 'medium',
            'required_downtime': False,
            'steps': [],
            'rollback_steps': [],
            'validation_queries': []
        }

        for change in changes:
            if change['type'] == 'add_column':
                plan['steps'].append(f"添加字段 {change['column']} 到表 {change['table']}")
                plan['rollback_steps'].append(f"删除字段 {change['column']} 从表 {change['table']}")
                plan['validation_queries'].append(f"SELECT COUNT(*) FROM {change['table']} WHERE {change['column']} IS NOT NULL")

            elif change['type'] == 'create_table':
                plan['steps'].append(f"创建表 {change['table']}")
                plan['rollback_steps'].append(f"删除表 {change['table']}")

            elif change['type'] == 'add_index':
                plan['steps'].append(f"创建索引 {change['index']} (并发创建)")
                plan['rollback_steps'].append(f"删除索引 {change['index']}")

        return plan


def main():
    """命令行工具"""
    import argparse

    parser = argparse.ArgumentParser(description='迁移模板生成器')
    parser.add_argument('template_type', choices=[
        'add_column', 'add_index', 'create_table', 'data_migration',
        'rename_table', 'enum_migration'
    ], help='模板类型')
    parser.add_argument('--table', help='表名')
    parser.add_argument('--column', help='字段名')
    parser.add_argument('--type', help='字段类型')
    parser.add_argument('--output', '-o', help='输出文件路径')

    args = parser.parse_args()

    if args.template_type == 'add_column':
        if not all([args.table, args.column, args.type]):
            print("add_column 需要 --table, --column, --type 参数")
            return

        template = MigrationTemplate.create_add_column_template(
            args.table, args.column, args.type
        )

    elif args.template_type == 'add_index':
        # 简化示例
        template = "# 添加索引模板\n# 请根据需要修改参数"

    else:
        template = f"# {args.template_type} 模板\n# 请参考 migration_README.md"

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(template)
        print(f"模板已保存到: {args.output}")
    else:
        print(template)


if __name__ == "__main__":
    main()
