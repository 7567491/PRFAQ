import sqlite3
import os
from datetime import datetime
import hashlib
import streamlit as st
from user.logger import add_log

def init_database():
    """初始化数据库"""
    status_container = st.empty()
    status_container.info("正在初始化数据库...")
    
    try:
        add_log("info", "开始初始化数据库...")
        
        # 确保db目录存在
        if not os.path.exists('db'):
            os.makedirs('db')
        
        # 连接数据库并创建表
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 删除现有表
        cursor.execute("DROP TABLE IF EXISTS history")
        cursor.execute("DROP TABLE IF EXISTS bills")
        cursor.execute("DROP TABLE IF EXISTS users")
        
        # 创建表
        # ... (创建表的SQL语句保持不变)
        
        # 创建默认用户
        current_time = datetime.now().isoformat()
        default_users = [
            {
                'user_id': 'jack',
                'username': 'Jack',
                'password': get_password_hash('Amazon123'),
                'role': 'admin',
                'is_active': 1,
                'created_at': current_time
            },
            {
                'user_id': 'rose',
                'username': 'Rose',
                'password': get_password_hash('Amazon123'),
                'role': 'user',
                'is_active': 1,
                'created_at': current_time
            }
        ]
        
        # 插入默认用户
        for user in default_users:
            try:
                cursor.execute('''
                INSERT INTO users (
                    user_id, username, password, role, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user['user_id'],
                    user['username'],
                    user['password'],
                    user['role'],
                    user['is_active'],
                    user['created_at']
                ))
                add_log("info", f"创建用户: {user['username']} ({user['role']})")
            except sqlite3.IntegrityError:
                add_log("warning", f"用户已存在: {user['username']}")
        
        conn.commit()
        conn.close()
        
        add_log("info", "数据库初始化完成")
        status_container.success("数据库初始化成功！")
        return True
        
    except Exception as e:
        error_msg = f"初始化数据库失败: {str(e)}"
        add_log("error", error_msg)
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        status_container.error(error_msg)
        return False

def get_password_hash(password: str) -> str:
    """获取密码哈希值"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    init_database()