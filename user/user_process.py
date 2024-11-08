import streamlit as st
from datetime import datetime
from user.user_base import UserManager
from user.logger import add_log
from user.user_add import UserRegistration

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
    st.title("PRFAQ Pro 登录")
    
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

def check_auth():
    """检查用户是否已登录"""
    init_session_state()
    if not st.session_state.authenticated:
        show_login_page()
        return False
    return True