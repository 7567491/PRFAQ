import sqlite3
import hashlib
from datetime import datetime
import uuid
from user.logger import add_log

def init_database() -> bool:
    """初始化数据库"""
    try:
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
            used_chars_today INTEGER DEFAULT 0,
            points INTEGER DEFAULT 1000
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
            points_cost INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # 创建历史记录表
        c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # 创建积分交易记录表
        c.execute('''
        CREATE TABLE IF NOT EXISTS point_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            balance INTEGER NOT NULL,
            description TEXT NOT NULL,
            operation_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # 创建充值记录表
        c.execute('''
        CREATE TABLE IF NOT EXISTS recharge_records (
            recharge_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            amount INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            transaction_id TEXT,
            points_added INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # 添加默认用户
        default_users = [
            {
                'username': 'Jack',
                'password': 'Amazon123',
                'role': 'admin',
                'is_active': 1
            },
            {
                'username': 'Rose',
                'password': 'Amazon123',
                'role': 'user',
                'is_active': 1
            }
        ]
        
        for user in default_users:
            user_id = str(uuid.uuid4())
            hashed_password = hashlib.sha256(user['password'].encode()).hexdigest()
            
            c.execute('''
            INSERT OR IGNORE INTO users (
                user_id, username, password, role, is_active, 
                created_at, points
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                user['username'],
                hashed_password,
                user['role'],
                user['is_active'],
                datetime.now().isoformat(),
                1000  # 初始积分
            ))
            
            # 为新用户添加初始积分记录
            c.execute('''
            INSERT INTO point_transactions (
                user_id, timestamp, type, amount, balance,
                description, operation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                'reward',
                1000,
                1000,
                '新用户注册奖励',
                None
            ))
        
        conn.commit()
        add_log("info", "数据库初始化成功")
        return True
        
    except Exception as e:
        add_log("error", f"数据库初始化失败: {str(e)}")
        return False
        
    finally:
        conn.close()