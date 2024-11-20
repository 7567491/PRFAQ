import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from user.logger import add_log

def read_database():
    """读取数据库信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 获取数据库结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        schema = cursor.fetchall()
        schema_text = "\n\n".join([row[0] for row in schema if row[0] is not None])
        
        # 读取用户数据
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        
        # 获取账单统计
        bills_stats = {
            'total_count': 0,
            'total_input': 0,
            'total_output': 0,
            'unique_days': 0
        }
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count,
                       SUM(input_tokens) as total_input,
                       SUM(output_tokens) as total_output,
                       COUNT(DISTINCT DATE(created_at)) as unique_days
                FROM bills
            """)
            result = cursor.fetchone()
            if result:
                bills_stats = {
                    'total_count': result[0] or 0,
                    'total_input': result[1] or 0,
                    'total_output': result[2] or 0,
                    'unique_days': result[3] or 0
                }
        except sqlite3.OperationalError:
            add_log("warning", "bills表不存在或结构不完整")
        
        # 获取历史记录统计
        history_stats = {
            'total_count': 0,
            'unique_types': 0,
            'unique_users': 0,
            'unique_days': 0
        }
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as count,
                       COUNT(DISTINCT type) as unique_types,
                       COUNT(DISTINCT username) as unique_users,
                       COUNT(DISTINCT DATE(created_at)) as unique_days
                FROM history
            """)
            result = cursor.fetchone()
            if result:
                history_stats = {
                    'total_count': result[0] or 0,
                    'unique_types': result[1] or 0,
                    'unique_users': result[2] or 0,
                    'unique_days': result[3] or 0
                }
        except sqlite3.OperationalError:
            add_log("warning", "history表不存在或结构不完整")
        
        # 获取积分统计
        points_stats = {
            'total_transactions': 0,
            'total_rewards': 0,
            'total_consumed': 0,
            'unique_users': 0
        }
        
        try:
            cursor.execute("""
                SELECT COUNT(*) as transactions,
                       SUM(CASE WHEN points > 0 THEN points ELSE 0 END) as rewards,
                       ABS(SUM(CASE WHEN points < 0 THEN points ELSE 0 END)) as consumed,
                       COUNT(DISTINCT user_id) as users
                FROM points
            """)
            result = cursor.fetchone()
            if result:
                points_stats = {
                    'total_transactions': result[0] or 0,
                    'total_rewards': result[1] or 0,
                    'total_consumed': result[2] or 0,
                    'unique_users': result[3] or 0
                }
        except sqlite3.OperationalError:
            add_log("warning", "points表不存在或结构不完整")
        
        return {
            'schema': schema_text,
            'users': users_df,
            'bills_stats': bills_stats,
            'history_stats': history_stats,
            'points_stats': points_stats
        }
        
    except Exception as e:
        add_log("error", f"读取数据库失败: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def read_history_records(username: str = None, record_type: str = None):
    """读取历史记录"""
    try:
        conn = sqlite3.connect('db/users.db')
        
        # 构建查询条件
        conditions = []
        params = []
        
        if username:
            conditions.append("username = ?")
            params.append(username)
        
        if record_type:
            conditions.append("type = ?")
            params.append(record_type)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 读取历史记录
        query = f"""
            SELECT id, username, type, content, created_at
            FROM history
            WHERE {where_clause}
            ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=params)
        
        # 转换时间戳
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        return df
        
    except Exception as e:
        add_log("error", f"读取历史记录失败: {str(e)}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals():
            conn.close() 