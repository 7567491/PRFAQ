import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from user.logger import add_log

class UserManager:
    def __init__(self):
        self.db_path = 'db/users.db'
    
    def get_db_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def hash_password(self, password: str) -> str:
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username: str, password: str) -> bool:
        """验证用户登录"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        c.execute('SELECT password FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        conn.close()
        
        if result and result[0] == self.hash_password(password):
            return True
        return False
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT user_id, username, email, phone, org_name, role, is_active,
                       created_at, last_login, total_chars, total_cost,
                       daily_chars_limit, used_chars_today
                FROM users WHERE username = ?
            ''', (username,))
            
            result = c.fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'phone': result[3],
                    'org_name': result[4],
                    'role': result[5],
                    'is_active': bool(result[6]),
                    'created_at': result[7],
                    'last_login': result[8],
                    'total_chars': result[9],
                    'total_cost': result[10],
                    'daily_chars_limit': result[11],
                    'used_chars_today': result[12]
                }
        except sqlite3.Error as e:
            add_log("error", f"获取用户信息失败: {str(e)}")
        finally:
            conn.close()
        
        return None

    def update_last_login(self, username: str):
        """更新最后登录时间"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE users 
                SET last_login = ? 
                WHERE username = ?
            ''', (datetime.now().isoformat(), username))
            
            conn.commit()
        except sqlite3.Error as e:
            add_log("error", f"更新最后登录时间失败: {str(e)}")
        finally:
            conn.close()

    def update_usage_stats(self, username: str, chars: int = 0, cost: float = 0.0):
        """更新用户使用统计"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE users 
                SET total_chars = total_chars + ?,
                    total_cost = total_cost + ?,
                    used_chars_today = used_chars_today + ?
                WHERE username = ?
            ''', (chars, cost, chars, username))
            
            conn.commit()
        except sqlite3.Error as e:
            add_log("error", f"更新使用统计失败: {str(e)}")
        finally:
            conn.close()

    def check_daily_limit(self, username: str) -> bool:
        """检查用户是否达到每日字符使用限制"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT daily_chars_limit, used_chars_today 
                FROM users WHERE username = ?
            ''', (username,))
            
            result = c.fetchone()
            if result:
                daily_limit, used_today = result
                return used_today < daily_limit
        except sqlite3.Error as e:
            add_log("error", f"检查每日限制失败: {str(e)}")
        finally:
            conn.close()
        
        return False

def init_session_state():
    """初始化session state中的用户相关变量"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

def show_login_page():
    """显示登录页面"""
    st.title("PRFAQ Pro 登录")
    
    user_mgr = UserManager()
    
    # 检查是否有保存的登录信息
    if 'saved_username' in st.session_state and 'saved_password' in st.session_state:
        username = st.session_state.saved_username
        password = st.session_state.saved_password
        if user_mgr.verify_user(username, password):
            # 自动登录
            user_info = user_mgr.get_user_info(username)
            if user_info:
                st.session_state.user = username
                st.session_state.authenticated = True
                st.session_state.user_role = user_info['role']
                add_log("info", f"用户 {username} 自动登录成功")
                st.rerun()
                return
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown("""
            <input type="text" name="username" placeholder="用户名" 
                   autocomplete="username" style="display:none">
            <input type="password" name="password" placeholder="密码" 
                   autocomplete="current-password" style="display:none">
        """, unsafe_allow_html=True)
        
        username = st.text_input("用户名", 
                               value="Jack",  # 设置默认用户名
                               key="username_input", 
                               autocomplete="username")
        password = st.text_input("密码", 
                               value="Amazon123",  # 设置默认密码
                               type="password", 
                               key="password_input", 
                               autocomplete="current-password")
        remember = st.checkbox("记住登录状态", value=True)
        submitted = st.form_submit_button("登录")
        
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
                            st.session_state.saved_username = username
                            st.session_state.saved_password = password
                        
                        user_mgr.update_last_login(username)
                        add_log("info", f"用户 {username} 登录成功")
                        st.rerun()
                    else:
                        st.error("获取用户信息失败")
                else:
                    st.error("用户名或密码错误")
            else:
                st.error("请输入用户名和密码")

def handle_logout():
    """处理用户退出登录"""
    if st.session_state.user:
        add_log("info", f"用户 {st.session_state.user} 退出登录")
    st.session_state.clear()
    st.rerun()

def check_auth():
    """检查用户是否已登录"""
    init_session_state()
    if not st.session_state.authenticated:
        show_login_page()
        return False
    return True