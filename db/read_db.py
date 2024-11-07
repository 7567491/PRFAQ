import sqlite3
import pandas as pd

def read_database():
    """读取数据库内容"""
    conn = sqlite3.connect('db/users.db')
    
    # 获取表结构
    schema = ""
    tables = ['users', 'bills', 'history', 'point_transactions', 'recharge_records']
    
    for table in tables:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        schema += f"\n{table} 表结构:\n"
        for row in cursor:
            schema += f"{row[1]} {row[2]}\n"
        schema += "\n"
    
    # 读取用户数据
    users = pd.read_sql_query('''
        SELECT user_id, username, email, phone, org_name, role, 
               is_active, created_at, last_login, total_chars, 
               total_cost, daily_chars_limit, used_chars_today, points
        FROM users
    ''', conn)
    
    # 获取账单统计
    cursor = conn.execute('''
        SELECT 
            COUNT(*) as total_count,
            SUM(input_letters) as total_input,
            SUM(output_letters) as total_output,
            COUNT(DISTINCT date(timestamp)) as unique_days
        FROM bills
    ''')
    bills_stats = dict(zip(['total_count', 'total_input', 'total_output', 'unique_days'], 
                          cursor.fetchone()))
    
    # 获取历史记录统计
    cursor = conn.execute('''
        SELECT 
            COUNT(*) as total_count,
            COUNT(DISTINCT type) as unique_types,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT date(timestamp)) as unique_days
        FROM history
    ''')
    history_stats = dict(zip(['total_count', 'unique_types', 'unique_users', 'unique_days'], 
                            cursor.fetchone()))
    
    # 获取积分统计
    cursor = conn.execute('''
        SELECT 
            COUNT(*) as total_transactions,
            SUM(CASE WHEN type = 'reward' THEN amount ELSE 0 END) as total_rewards,
            SUM(CASE WHEN type = 'consume' THEN ABS(amount) ELSE 0 END) as total_consumed,
            COUNT(DISTINCT user_id) as unique_users
        FROM point_transactions
    ''')
    points_stats = dict(zip(['total_transactions', 'total_rewards', 'total_consumed', 'unique_users'], 
                           cursor.fetchone()))
    
    conn.close()
    
    return {
        'schema': schema,
        'users': users,
        'bills_stats': bills_stats,
        'history_stats': history_stats,
        'points_stats': points_stats
    }

def read_history_records():
    """读取历史生成记录"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 获取所有历史记录，包括用户信息
    c.execute("""
        SELECT h.timestamp, u.username, h.type, h.content
        FROM history h
        JOIN users u ON h.user_id = u.user_id
        ORDER BY h.timestamp DESC
    """)
    
    records = c.fetchall()
    columns = ['时间', '用户', '类型', '内容']
    
    conn.close()
    
    return pd.DataFrame(records, columns=columns) 