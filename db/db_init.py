import sqlite3
import hashlib
from datetime import datetime

def init_database():
    """初始化数据库"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        org_name TEXT,
        role TEXT NOT NULL,
        is_active INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        last_login TEXT,
        total_chars INTEGER DEFAULT 0,
        total_cost REAL DEFAULT 0.0,
        daily_chars_limit INTEGER DEFAULT 100000,
        used_chars_today INTEGER DEFAULT 0
    )
    ''')
    
    # 创建账单表
    c.execute('''
    CREATE TABLE IF NOT EXISTS bills (
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
    
    # 创建历史记录表
    c.execute('''
    CREATE TABLE IF NOT EXISTS history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        content TEXT NOT NULL,
        type TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    # 创建默认管理员和用户账户
    default_password = hashlib.sha256('Amazon123'.encode()).hexdigest()
    current_time = datetime.now().isoformat()
    
    default_users = [
        ('admin_001', 'Jack', default_password, None, None, None, 'admin', 1, current_time),
        ('user_001', 'Rose', default_password, None, None, None, 'normal', 1, current_time)
    ]
    
    for user in default_users:
        try:
            c.execute('''
                INSERT INTO users 
                (user_id, username, password, email, phone, org_name, role, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', user)
        except sqlite3.IntegrityError:
            print(f"User {user[1]} already exists")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database() 