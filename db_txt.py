import sqlite3
import os

def get_database_structure():
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        structure = []
        structure.append("# PRFAQ Pro 数据库结构说明\n")
        structure.append("## 当前数据库状态")
        
        # 获取数据库文件大小
        db_size = os.path.getsize('db/users.db')
        structure.append(f"- 数据库文件大小: {db_size/1024:.2f} KB")
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        structure.append(f"- 总表数量: {len(tables)}\n")
        
        # 获取每个表的详细信息
        for table in tables:
            table_name = table[0]
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # 获取表中的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            structure.append(f"\n## {table_name} 表")
            structure.append(f"当前记录数: {row_count}")
            structure.append("\n```sql")
            structure.append(f"CREATE TABLE {table_name} (")
            
            # 添加列定义
            for i, col in enumerate(columns):
                cid, name, type_, notnull, dflt_value, pk = col
                constraints = []
                if pk:
                    constraints.append("PRIMARY KEY")
                if notnull:
                    constraints.append("NOT NULL")
                if dflt_value is not None:
                    constraints.append(f"DEFAULT {dflt_value}")
                    
                constraint_str = " ".join(constraints)
                comma = "," if i < len(columns) - 1 else ""
                structure.append(f"    {name} {type_} {constraint_str}{comma}")
            
            structure.append(");")
            structure.append("```")
            
            # 获取索引信息
            cursor.execute(f"PRAGMA index_list({table_name});")
            indexes = cursor.fetchall()
            if indexes:
                structure.append("\n索引：")
                for idx in indexes:
                    index_name = idx[1]
                    cursor.execute(f"PRAGMA index_info({index_name});")
                    index_info = cursor.fetchall()
                    columns = ", ".join(info[2] for info in index_info)
                    structure.append(f"- {index_name}: ({columns})")
            
            # 获取外键信息
            cursor.execute(f"PRAGMA foreign_key_list({table_name});")
            foreign_keys = cursor.fetchall()
            if foreign_keys:
                structure.append("\n外键关系：")
                for fk in foreign_keys:
                    structure.append(f"- {fk[3]} -> {fk[2]}({fk[4]})")
            
            structure.append("")
        
        # 添加表之间的关系说明
        structure.append("\n## 表关系说明")
        structure.append("1. users 表是核心表，存储用户基本信息")
        structure.append("2. bills 表通过 user_id 关联到 users 表，记录用户的积分变动")
        structure.append("3. history 表通过 user_id 关联到 users 表，记录用户的操作历史")
        structure.append("4. point_transactions 表通过 user_id 关联到 users 表，记录积分交易详情")
        structure.append("5. recharge_records 表通过 user_id 关联到 users 表，记录充值记录\n")
        
        conn.close()
        return "\n".join(structure)
        
    except Exception as e:
        return f"获取数据库结构时出错: {str(e)}"

# 生成结构文件
with open('db/db1118.txt', 'w', encoding='utf-8') as f:
    f.write(get_database_structure())