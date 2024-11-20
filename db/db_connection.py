import sqlite3
import streamlit as st
from pathlib import Path
from user.logger import add_log

def get_db_connection():
    """获取数据库连接"""
    try:
        # 确保数据库目录存在
        db_dir = Path("db")
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
            
        # 连接到数据库（确保使用正确的数据库文件名）
        conn = sqlite3.connect('db/users.db')  # 修改为 users.db
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        add_log("error", f"数据库连接失败: {str(e)}")
        st.error(f"数据库连接失败: {str(e)}")
        return None 