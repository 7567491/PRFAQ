import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from db.backup_db import backup_database

class DatabaseError(Exception):
    """数据库错误基类"""
    pass

def check_column_mapping(conn: sqlite3.Connection) -> dict:
    """检查列映射关系"""
    c = conn.cursor()
    
    # 获取当前表结构
    c.execute("PRAGMA table_info(users)")
    current_columns = {row[1]: row[2] for row in c.fetchall()}
    
    # 定义新旧列名映射
    column_mapping = {
        'daily_limit': 'daily_chars_limit',
        'used_today': 'used_chars_today',
        'api_calls': 'total_chars'
    }
    
    # 检查实际存在的列
    existing_mappings = {}
    for old_col, new_col in column_mapping.items():
        if old_col in current_columns:
            existing_mappings[old_col] = new_col
    
    return existing_mappings

def get_current_columns(conn: sqlite3.Connection) -> list:
    """获取当前表的所有列名"""
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    return [row[1] for row in c.fetchall()]

def generate_migration_sql(conn: sqlite3.Connection, mappings: dict) -> str:
    """生成迁移SQL语句"""
    current_columns = get_current_columns(conn)
    
    # 基本列（新表中的所有列）
    new_columns = [
        'user_id', 'username', 'password', 'email', 'phone', 
        'org_name', 'role', 'is_active', 'created_at', 'last_login',
        'total_chars', 'total_cost', 'daily_chars_limit', 'used_chars_today'
    ]
    
    # 构建SELECT部分
    select_parts = []
    for col in new_columns:
        if col in current_columns:  # 如果列已存在
            select_parts.append(col)
        elif col in mappings.values():  # 如果是需要重命名的列
            old_col = [k for k, v in mappings.items() if v == col][0]
            select_parts.append(f"{old_col} as {col}")
        else:  # 如果是新列，使用默认值
            if col in ['total_chars', 'used_chars_today']:
                select_parts.append("0 as " + col)
            elif col == 'daily_chars_limit':
                select_parts.append("100000 as " + col)
            elif col == 'total_cost':
                select_parts.append("0.0 as " + col)
            else:
                select_parts.append("NULL as " + col)
    
    return f"""
    INSERT INTO users_new (
        {', '.join(new_columns)}
    )
    SELECT 
        {', '.join(select_parts)}
    FROM users
    """

def check_upgrade_needed(conn: sqlite3.Connection) -> bool:
    """检查是否需要升级"""
    c = conn.cursor()
    needs_upgrade = False
    
    try:
        # 检查用户表是否有积分字段
        c.execute("PRAGMA table_info(users)")
        user_columns = {row[1] for row in c.fetchall()}
        if 'points' not in user_columns:
            needs_upgrade = True
        
        # 检查是否存在积分交易记录表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='point_transactions'")
        if not c.fetchone():
            needs_upgrade = True
        
        # 检查是否存在充值记录表
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recharge_records'")
        if not c.fetchone():
            needs_upgrade = True
        
        # 检查账单表是否有积分消费字段
        c.execute("PRAGMA table_info(bills)")
        bill_columns = {row[1] for row in c.fetchall()}
        if 'points_cost' not in bill_columns:
            needs_upgrade = True
        
        return needs_upgrade
        
    except sqlite3.Error as e:
        print(f"检查数据库结构时出错: {str(e)}")
        return True

def upgrade_bills_table(conn: sqlite3.Connection) -> dict:
    """升级账单表结构"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    c = conn.cursor()
    try:
        # 1. 检查账单表结构
        c.execute("PRAGMA table_info(bills)")
        current_columns = {row[1] for row in c.fetchall()}
        
        # 如果已经是新结构，直接返回
        if 'total_cost' in current_columns and 'total_cost_rmb' not in current_columns:
            results['success'] = True
            results['message'] = "账单表已是最新结构"
            return results
        
        # 2. 创建新的账单表
        c.execute('''
        CREATE TABLE bills_new (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            api_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            input_letters INTEGER NOT NULL,
            output_letters INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        results['details'].append("创建新账单表成功")
        
        # 3. 迁移数据
        if 'total_cost_rmb' in current_columns:
            # 如果有旧的 total_cost_rmb 列
            c.execute('''
            INSERT INTO bills_new (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost
            )
            SELECT 
                user_id, timestamp, api_name, operation,
                input_letters, output_letters,
                total_cost_rmb
            FROM bills
            ''')
        else:
            # 如果没有，使用字符数计算费用
            c.execute('''
            INSERT INTO bills_new (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost
            )
            SELECT 
                user_id, timestamp, api_name, operation,
                input_letters, output_letters,
                (input_letters + output_letters) * 0.0001
            FROM bills
            ''')
        
        results['details'].append("数据迁移成功")
        
        # 4. 删除旧表并重命名新表
        c.execute('DROP TABLE bills')
        c.execute('ALTER TABLE bills_new RENAME TO bills')
        results['details'].append("表结构更新成功")
        
        results['success'] = True
        results['message'] = "账单表升级成功"
        
    except Exception as e:
        results['message'] = f"账单表升级失败: {str(e)}"
        results['details'].append(f"错误详情: {str(e)}")
        raise
    
    return results

def cleanup_temp_tables(conn: sqlite3.Connection) -> None:
    """清理临时表"""
    c = conn.cursor()
    try:
        c.execute("DROP TABLE IF EXISTS users_new")
        c.execute("DROP TABLE IF EXISTS bills_new")
        conn.commit()
    except sqlite3.Error as e:
        print(f"清理临时表失败: {str(e)}")

def upgrade_database() -> dict:
    """升级数据库结构"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    # 先进行备份
    try:
        backup_database()
        results['details'].append("数据库备份成功")
    except Exception as e:
        results['message'] = f"数据库备份失败: {str(e)}"
        return results
    
    conn = sqlite3.connect('db/users.db')
    
    try:
        # 0. 检查是否需要升级
        if not check_upgrade_needed(conn):
            results['success'] = True
            results['message'] = "数据库已是最新版本，无需升级"
            results['details'].append("检测到当前数据库结构已经是最新的")
            return results
        
        c = conn.cursor()
        
        # 1. 在用户表中添加积分字段
        c.execute('''
        ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 1000;
        ''')
        results['details'].append("用户表添加积分字段成功")
        
        # 2. 创建积分交易记录表
        c.execute('''
        CREATE TABLE IF NOT EXISTS point_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,  -- 'reward'(奖励), 'consume'(消费), 'recharge'(充值), 'admin'(管理员调整)
            amount INTEGER NOT NULL,  -- 正数表示增加，负数表示减少
            balance INTEGER NOT NULL, -- 交易后的余额
            description TEXT NOT NULL,
            operation_id TEXT,  -- 关联的操作ID（如账单ID）
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        results['details'].append("创建积分交易记录表成功")
        
        # 3. 创建充值记录表
        c.execute('''
        CREATE TABLE IF NOT EXISTS recharge_records (
            recharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            amount INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,  -- 'pending', 'success', 'failed'
            transaction_id TEXT,  -- 支付平台交易ID
            points_added INTEGER NOT NULL,  -- 实际增加的积分数
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        results['details'].append("创建充值记录表成功")
        
        # 4. 为所有现有用户添加初始积分
        c.execute('''
        UPDATE users 
        SET points = 1000 
        WHERE points IS NULL
        ''')
        results['details'].append("为现有用户添加初始积分成功")
        
        # 5. 修改bills表，添加积分消费字段
        c.execute('''
        ALTER TABLE bills 
        ADD COLUMN points_cost INTEGER DEFAULT 0;
        ''')
        results['details'].append("账单表添加积分消费字段成功")
        
        # 6. 更新现有账单记录的积分消费
        c.execute('''
        UPDATE bills 
        SET points_cost = input_letters + output_letters 
        WHERE points_cost = 0;
        ''')
        results['details'].append("更新现有账单积分消费成功")
        
        conn.commit()
        results['success'] = True
        results['message'] = "数据库升级成功"
        
    except Exception as e:
        conn.rollback()
        results['message'] = f"数据库升级失败: {str(e)}"
        results['details'].append(f"错误详情: {str(e)}")
    
    finally:
        conn.close()
    
    return results

if __name__ == "__main__":
    print("开始数据库升级...")
    results = upgrade_database()
    print(f"升级结果: {results['message']}")
    for detail in results['details']:
        print(f"- {detail}") 