import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import sqlite3
from bill.bill import BillManager
from user.user_process import UserManager
from user.logger import add_log, display_logs

def load_config():
    """Load configuration from config.json"""
    config_path = Path("config/config.json")
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_templates():
    """Load UI templates"""
    template_path = Path("config/templates.json")
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompts():
    """Load prompts from prompt.json"""
    try:
        with open('config/prompt.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("未找到 prompt.json 配置文件")
        return {}
    except json.JSONDecodeError:
        st.error("prompt.json 格式错误")
        return {}
    except Exception as e:
        st.error(f"加载提示词配置时发生错误: {str(e)}")
        return {}

def load_history():
    """从数据库加载历史记录"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT timestamp, content, type
        FROM history
        ORDER BY timestamp DESC
    ''')
    
    records = c.fetchall()
    conn.close()
    
    return [{
        'timestamp': record[0],
        'content': record[1],
        'type': record[2]
    } for record in records]

def save_history(content: str, history_type: str = 'unknown'):
    """保存历史记录到数据库"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 获取当前用户的user_id
    c.execute('SELECT user_id FROM users WHERE username = ?', (st.session_state.user,))
    user_id = c.fetchone()[0]
    
    c.execute('''
        INSERT INTO history (user_id, timestamp, content, type)
        VALUES (?, ?, ?, ?)
    ''', (user_id, datetime.now().isoformat(), content, history_type))
    
    conn.commit()
    conn.close()

def add_letters_record(input_letters: int, output_letters: int, api_name: str, operation: str) -> bool:
    """Add a new letters record"""
    try:
        # 获取当前用户ID
        user_mgr = UserManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        if not user_info:
            return False
        
        # 检查用户是否达到每日限制
        if not user_mgr.check_daily_limit(st.session_state.user):
            st.error("已达到每日字符使用限制")
            return False
        
        # 检查积分是否足够
        points_needed = input_letters + output_letters
        bill_mgr = BillManager()
        current_points = bill_mgr.get_user_points(user_info['user_id'])
        
        if current_points < points_needed:
            st.error(f"积分不足，需要 {points_needed} 积分，当前剩余 {current_points} 积分")
            return False
        
        # 添加账单记录
        success = bill_mgr.add_bill_record(
            user_id=user_info['user_id'],
            api_name=api_name,
            operation=operation,
            input_letters=input_letters,
            output_letters=output_letters
        )
        
        if not success:
            st.error("记录使用量失败")
            return False
        
        # 在侧边栏更新积分显示
        if 'sidebar_points' in st.session_state:
            st.session_state.sidebar_points = bill_mgr.get_user_points(user_info['user_id'])
        
        return True
            
    except Exception as e:
        st.error(f"记录使用量时出错: {str(e)}")
        return False

def load_letters():
    """从数据库加载账单数据"""
    bill_mgr = BillManager()
    return bill_mgr.get_all_bills()

def update_sidebar_points():
    """更新侧边栏积分显示"""
    if 'user' in st.session_state and st.session_state.user:
        user_mgr = UserManager()
        bill_mgr = BillManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        if user_info:
            st.session_state.sidebar_points = bill_mgr.get_user_points(user_info['user_id'])
