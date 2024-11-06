import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import sqlite3
from user.bill import BillManager
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
        # 计算总字符数和费用
        total_chars = input_letters + output_letters
        total_cost = total_chars * 0.0001  # 每字符0.0001元
        
        # 更新数据库
        user_mgr = UserManager()
        bill_mgr = BillManager()
        
        # 获取当前用户ID
        user_info = user_mgr.get_user_info(st.session_state.user)
        if not user_info:
            return False
            
        # 检查用户是否达到每日限制
        if not user_mgr.check_daily_limit(st.session_state.user):
            st.error("已达到每日字符使用限制")
            return False
            
        # 添加账单记录
        bill_mgr.add_bill_record(
            user_id=user_info['user_id'],
            api_name=api_name,
            operation=operation,
            input_letters=input_letters,
            output_letters=output_letters
        )
        
        # 更新用户使用统计
        user_mgr.update_usage_stats(
            username=st.session_state.user,
            chars=total_chars,
            cost=total_cost
        )
        
        return True
            
    except Exception as e:
        st.error(f"记录使用量时出错: {str(e)}")
        return False

def load_letters():
    """从数据库加载账单数据"""
    bill_mgr = BillManager()
    return bill_mgr.get_all_bills()
