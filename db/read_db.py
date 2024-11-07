import sqlite3
import pandas as pd

def read_database():
    """读取数据库信息"""
    try:
        conn = sqlite3.connect('db/users.db')  # 使用正确的数据库路径
        c = conn.cursor()
        
        # 获取表结构
        c.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schema = "\n\n".join([row[0] for row in c.fetchall() if row[0] is not None])
        
        # 获取用户数据
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        
        # 获取账单统计
        c.execute("""
            SELECT 
                COUNT(*) as total_count,
                SUM(input_letters) as total_input,
                SUM(output_letters) as total_output,
                COUNT(DISTINCT date(timestamp)) as unique_days
            FROM bills
        """)
        bills_stats = dict(zip(
            ['total_count', 'total_input', 'total_output', 'unique_days'],
            c.fetchone()
        ))
        
        # 获取历史记录统计
        c.execute("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(DISTINCT type) as unique_types,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT date(timestamp)) as unique_days
            FROM history
        """)
        history_stats = dict(zip(
            ['total_count', 'unique_types', 'unique_users', 'unique_days'],
            c.fetchone()
        ))
        
        # 检查未关联的账单
        c.execute("""
            SELECT b.*
            FROM bills b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
        orphaned_bills = c.fetchall()
        
        conn.close()
        
        return {
            'schema': schema,
            'users': users_df,
            'bills_stats': bills_stats,
            'history_stats': history_stats,
            'orphaned_bills': orphaned_bills
        }
        
    except Exception as e:
        raise Exception(f"读取数据库失败: {str(e)}")

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