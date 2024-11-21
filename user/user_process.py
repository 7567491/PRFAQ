import streamlit as st
from datetime import datetime, timedelta, timezone
from user.user_base import UserManager
from user.logger import add_log
from user.user_add import UserRegistration
from pathlib import Path
import json
import portalocker
import os
from typing import Optional
import sqlite3
import traceback
import hashlib

# 添加新的常量定义
MP_SESSION_FILE = Path("./config/mp_session.json")
MP_SESSION_TIMEOUT = 5  # minutes

def init_session_state():
    """初始化session state中的用户相关变量"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    
    # 从 query params 获取保存的登录信息
    try:
        if 'saved_username' in st.query_params and 'saved_password' in st.query_params:
            st.session_state.saved_username = st.query_params['saved_username']
            st.session_state.saved_password = st.query_params['saved_password']
    except:
        pass

def save_login_info(username: str, password: str):
    """保存登录信息到 query params"""
    try:
        st.query_params['saved_username'] = username
        st.query_params['saved_password'] = password
    except:
        pass

def clear_login_info():
    """清除保存的登录信息"""
    try:
        st.query_params.clear()
    except:
        pass

def show_login_page():
    """显示登录页面"""
    st.title("六页纸AI登录")
    
    # 如果是注册状态，显示注册表单
    if st.session_state.get('show_registration', False):
        from user.user_add import show_registration_form
        show_registration_form()
        return
    
    user_mgr = UserManager()
    registration = UserRegistration()
    
    # 获取默认的用户名和密码
    default_username = ""
    default_password = ""
    
    # 检查是否有新注册用户信息
    new_user = st.session_state.get('new_registered_user')
    if new_user:
        default_username = new_user['username']
        default_password = new_user['password']
        # 清除注册信息
        del st.session_state.new_registered_user
    # 检查是否有保存的登录信息
    elif 'saved_username' in st.session_state and 'saved_password' in st.session_state:
        default_username = st.session_state.saved_username
        default_password = st.session_state.saved_password
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown("""
            <input type="text" name="username" placeholder="用户名" 
                   autocomplete="username" style="display:none">
            <input type="password" name="password" placeholder="密码" 
                   autocomplete="current-password" style="display:none">
        """, unsafe_allow_html=True)
        
        username = st.text_input("用户名", 
                               value=default_username,
                               key="username_input", 
                               autocomplete="username",
                               placeholder="请输入用户名")
        password = st.text_input("密码", 
                               value=default_password,
                               type="password", 
                               key="password_input", 
                               autocomplete="current-password",
                               placeholder="请输入密码")
        remember = st.checkbox("记住登录状态", value=True)
        
        # 创建两列布局放置按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            try:
                submitted = st.form_submit_button("用户登录", use_container_width=True)
            except Exception as e:
                # 如果出现渲染错误，尝试使用备选文本
                add_log("warning", f"登录按钮渲染出错: {str(e)}, 使用备选文本")
                try:
                    submitted = st.form_submit_button("登录", use_container_width=True)
                except Exception as e:
                    # 如果备选文本也失败，使用最简单的文本
                    add_log("error", f"备选登录按钮渲染也失败: {str(e)}, 使用基础文本")
                    submitted = st.form_submit_button("登", use_container_width=True)
        with col2:
            try:
                register = st.form_submit_button("👉 新用户注册", use_container_width=True)
            except Exception as e:
                # 如果注册按钮渲染出错，使用简单文本
                add_log("warning", f"注册按钮渲染出错: {str(e)}, 使用简单文本")
                register = st.form_submit_button("注册", use_container_width=True)
        
        if submitted:
            if username and password:
                if user_mgr.verify_user(username, password):
                    user_info = user_mgr.get_user_info(username)
                    if user_info:
                        if not user_info['is_active']:
                            st.error("账户已被禁用，请联系管理员")
                            return
                        
                        st.session_state.user = username
                        st.session_state.authenticated = True
                        st.session_state.user_role = user_info['role']
                        
                        if remember:
                            # 保存登录信息
                            save_login_info(username, password)
                        else:
                            # 清除登录信息
                            clear_login_info()
                        
                        # 处理每日登录奖励
                        registration.award_daily_login(user_info['user_id'], username)
                        
                        user_mgr.update_last_login(username)
                        add_log("info", f"用户 {username} 登录成功")
                        st.rerun()
                    else:
                        st.error("获取用户信息失败")
                else:
                    st.error("用户名或密码错误")
            else:
                st.error("请输入用户名和密码")
        
        if register:
            st.session_state.show_registration = True
            st.rerun()

def handle_logout():
    """处理用户退出登录"""
    if st.session_state.user:
        add_log("info", f"用户 {st.session_state.user} 退出登录")
    # 清除登录信息
    clear_login_info()
    st.session_state.clear()
    st.rerun()

def load_marketplace_session(session_id: str) -> Optional[dict]:
    """加载AWS Marketplace会话信息"""
    try:
        if not MP_SESSION_FILE.exists():
            return None
            
        with open(MP_SESSION_FILE, "r") as f:
            sessions = json.load(f)
            if session_id not in sessions:
                return None
                
            session = sessions[session_id]
            
            # 解析时间戳
            session_time = datetime.fromisoformat(session["timestamp"])
            current_time = datetime.now(timezone.utc)
            
            # 检查会话是否过期（5分钟）
            if (current_time - session_time).total_seconds() > MP_SESSION_TIMEOUT * 60:
                add_log("warning", f"Marketplace session {session_id} expired")
                return None
                
            return session
    except Exception as e:
        add_log("error", f"Error loading marketplace session: {str(e)}")
        return None

def register_marketplace_user(user_info: dict) -> bool:
    """注册AWS Marketplace用户"""
    try:
        # 检查用户是否已存在
        user_mgr = UserManager()
        customer_id = user_info["CustomerIdentifier"]
        
        if not user_mgr.user_exists(customer_id):
            # 创建新用户
            user_data = {
                "user_id": customer_id,
                "username": customer_id,  # 使用CustomerIdentifier作为用户名
                "aws_account_id": user_info["CustomerAWSAccountId"],
                "product_code": user_info["ProductCode"],
                "entitlements": user_info.get("Entitlements", {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "role": "user",
                "is_active": True,
                "last_login": None
            }
            user_mgr.add_user(user_data)
            add_log("info", f"Registered new marketplace user: {customer_id}")
            return True
        else:
            add_log("info", f"Marketplace user already exists: {customer_id}")
            return True
            
    except Exception as e:
        add_log("error", f"Error registering marketplace user: {str(e)}")
        return False

def handle_marketplace_login() -> bool:
    """处理AWS Marketplace登录"""
    try:
        # 获取URL参数
        session_id = st.query_params.get("session_id")
        if not session_id:
            return False
            
        # 加载marketplace会话
        session = load_marketplace_session(session_id)
        if not session:
            return False
            
        user_info = session["user_info"]
        customer_id = user_info["CustomerIdentifier"]
        
        # 注册或更新用户
        if not register_marketplace_user(user_info):
            return False
            
        # 设置登录状态
        user_mgr = UserManager()
        user_info = user_mgr.get_user_info(customer_id)
        if user_info and user_info['is_active']:
            st.session_state.user = customer_id
            st.session_state.authenticated = True
            st.session_state.user_role = user_info['role']
            
            # 更新最后登录时间
            user_mgr.update_last_login(customer_id)
            
            add_log("info", f"Marketplace user {customer_id} logged in successfully")
            return True
            
        return False
        
    except Exception as e:
        add_log("error", f"Error handling marketplace login: {str(e)}")
        return False

def check_auth():
    """检查用户是否已登录，包括处理 AWS Marketplace 会话"""
    init_session_state()
    
    # 如果已经认证，直接返回
    if st.session_state.authenticated:
        return True
        
    # 检查 AWS Marketplace 会话
    try:
        session_id = st.query_params.get('session_id')
        if session_id:
            session = load_marketplace_session(session_id)
            if session:
                # 使用 AWS 客户标识符作为用户名
                username = session['user_info']['CustomerIdentifier']
                user_mgr = UserManager()
                
                # 获取或创建用户
                if not user_mgr.user_exists(username):
                    # 这里可以添加创建 Marketplace 用户的逻辑
                    add_log("info", f"Creating new marketplace user: {username}")
                    # TODO: 实现创建用户的逻辑
                    pass
                
                user_info = user_mgr.get_user_info(username)
                if user_info and user_info['is_active']:
                    st.session_state.user = username
                    st.session_state.authenticated = True
                    st.session_state.user_role = user_info['role']
                    
                    # 更新最后登录时间
                    user_mgr.update_last_login(username)
                    
                    # 更新会话状态
                    update_marketplace_session(session_id, "processed")
                    
                    add_log("info", f"Marketplace user {username} logged in successfully")
                    return True
    except Exception as e:
        add_log("error", f"Error processing marketplace session: {str(e)}")
    
    # 如果 Marketplace 认证失败或不存在，显示常规登录页面
    show_login_page()
    return False

class UserManager:
    def __init__(self):
        self.db_file = "db/users.db"
        self.user_file = "config/users.json"  # 保留json文件用于marketplace用户
        
        # 确保目录存在
        Path(self.db_file).parent.mkdir(exist_ok=True)
        Path(self.user_file).parent.mkdir(exist_ok=True)
        
        # 初始化数据库
        self._init_db()
        
        # 加载json用户（marketplace用户）
        if not Path(self.user_file).exists():
            with open(self.user_file, "w") as f:
                json.dump({}, f)
        self.load_users()

    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                    (username TEXT PRIMARY KEY, 
                     password TEXT,
                     role TEXT,
                     is_active INTEGER,
                     created_at TEXT,
                     last_login TEXT)''')
        conn.commit()
        conn.close()

    def _hash_password(self, password: str) -> str:
        """对密码进行SHA-256哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_user(self, username: str, password: str) -> bool:
        """验证用户名和密码"""
        try:
            # 对输入的密码进行哈希处理
            hashed_password = self._hash_password(password)
            
            # 首先检查SQLite数据库（普通用户）
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute('SELECT username, password, role, is_active FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            conn.close()
            
            if result and result[1] == hashed_password:
                add_log("info", f"Database user verified: {username}")
                return True
            
        except Exception as e:
            add_log("error", f"Database verification error: {str(e)}")
        
        # 如果数据库中没有，检查json文件（marketplace用户）
        if username in self.users:
            json_password = self.users[username].get('password')
            if json_password == hashed_password:
                add_log("info", f"Marketplace user verified: {username}")
                return True
        
        return False

    def get_user_info(self, username: str) -> dict:
        """获取用户信息"""
        try:
            # 首先检查数据库
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute('''SELECT user_id, username, role, is_active, created_at, 
                        last_login, total_chars, total_cost, daily_chars_limit, 
                        used_chars_today, points, status 
                        FROM users WHERE username = ?''', (username,))
            result = c.fetchone()
            conn.close()
            
            if result:
                user_info = {
                    "user_id": result[0],
                    "username": result[1],
                    "role": result[2],
                    "is_active": bool(result[3]),
                    "created_at": result[4],
                    "last_login": result[5],
                    "total_chars": result[6],
                    "total_cost": result[7],
                    "daily_chars_limit": result[8],
                    "used_chars_today": result[9],
                    "points": result[10],
                    "status": result[11]
                }
                return user_info
            
        except Exception as e:
            add_log("error", f"Error getting user info from database: {str(e)}")
        
        # 如果数据库中没有，检查json文件
        return self.users.get(username, {})

    def update_last_login(self, username: str):
        """更新最后登录时间"""
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            # 更新数据库
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            c.execute('UPDATE users SET last_login = ? WHERE username = ?', 
                     (now, username))
            conn.commit()
            conn.close()
            add_log("info", f"Updated last login for database user: {username}")
        except Exception as e:
            add_log("error", f"Error updating last login in database: {str(e)}")
        
        # 如果是marketplace用户，也更新json
        if username in self.users:
            self.users[username]['last_login'] = now
            self.save_users()
            add_log("info", f"Updated last login for marketplace user: {username}")

    def load_users(self):
        with open(self.user_file, "r") as f:
            self.users = json.load(f)

    def save_users(self):
        with open(self.user_file, "w") as f:
            portalocker.lock(f, portalocker.LOCK_EX)
            try:
                json.dump(self.users, f, indent=2)
            finally:
                portalocker.unlock(f)

    def user_exists(self, username: str) -> bool:
        return username in self.users

    def add_user(self, user_data: dict):
        username = user_data["username"]
        self.users[username] = user_data
        self.save_users()