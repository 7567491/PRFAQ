import sqlite3
import pandas as pd

def read_database():
    """读取数据库信息"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 获取表结构
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    schema = c.fetchone()[0]
    
    # 获取所有用户数据，包括账单统计
    c.execute("""
        SELECT u.*, 
               COUNT(DISTINCT b.bill_id) as bills_count,
               COALESCE(SUM(b.input_letters + b.output_letters), 0) as total_letters,
               COALESCE(SUM(b.total_cost), 0) as total_bill_cost
        FROM users u
        LEFT JOIN bills b ON u.user_id = b.user_id
        GROUP BY u.user_id
    """)
    users = c.fetchall()
    columns = [description[0] for description in c.description]
    
    # 获取账单详细信息
    c.execute("""
        SELECT u.username, b.*
        FROM bills b
        JOIN users u ON b.user_id = u.user_id
        ORDER BY b.timestamp DESC
    """)
    bills = c.fetchall()
    bill_columns = ['username'] + [description[0] for description in c.description[1:]]
    
    # 获取总计数据
    c.execute("""
        SELECT 
            COUNT(*) as total_count,
            SUM(input_letters) as total_input,
            SUM(output_letters) as total_output,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT DATE(timestamp)) as unique_days,
            SUM(total_cost) as total_cost
        FROM bills
    """)
    bills_stats = c.fetchone()
    
    c.execute("""
        SELECT 
            COUNT(*) as total_count,
            COUNT(DISTINCT user_id) as unique_users,
            COUNT(DISTINCT type) as unique_types,
            COUNT(DISTINCT DATE(timestamp)) as unique_days
        FROM history
    """)
    history_stats = c.fetchone()
    
    # 检查账单关联情况
    c.execute("""
        SELECT b.user_id, COUNT(*) as count
        FROM bills b
        LEFT JOIN users u ON b.user_id = u.user_id
        WHERE u.user_id IS NULL
        GROUP BY b.user_id
    """)
    orphaned_bills = c.fetchall()
    
    conn.close()
    
    # 创建DataFrame
    df = pd.DataFrame(users, columns=columns)
    bills_df = pd.DataFrame(bills, columns=bill_columns)
    
    return {
        'schema': schema,
        'users': df,
        'bills': bills_df,
        'bills_count': bills_stats[0],
        'bills_stats': {
            'total_count': bills_stats[0],
            'total_input': bills_stats[1],
            'total_output': bills_stats[2],
            'unique_users': bills_stats[3],
            'unique_days': bills_stats[4],
            'total_cost': bills_stats[5]
        },
        'history_count': history_stats[0],
        'history_stats': {
            'total_count': history_stats[0],
            'unique_users': history_stats[1],
            'unique_types': history_stats[2],
            'unique_days': history_stats[3]
        },
        'orphaned_bills': orphaned_bills
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