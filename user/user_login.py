import streamlit as st
from datetime import datetime, timezone
from user.user_process import UserManager
from user.logger import add_log
from user.user_add import show_registration_form

def show_normal_login():
    """显示普通用户登录页面"""
    st.title("六页纸AI登录")
    
    # 如果是注册状态，显示注册表单
    if st.session_state.get('show_registration', False):
        show_registration_form()
        return False
    
    # 登录表单
    with st.form("login_form"):
        username = st.text_input("用户名", value=st.session_state.get('saved_username', ''))
        password = st.text_input("密码", type="password", value=st.session_state.get('saved_password', ''))
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("用户登录", use_container_width=True)
        with col2:
            if st.form_submit_button("新用户注册", use_container_width=True):
                st.session_state.show_registration = True
                st.rerun()
                return False
    
    if submitted:
        user_mgr = UserManager()
        if user_mgr.verify_user(username, password):
            # 获取用户信息
            user_info = user_mgr.get_user_info(username)
            if not user_info.get('is_active', True):
                st.error("账号已被禁用，请联系管理员")
                add_log("warning", f"Disabled user attempted login: {username}")
                return False
            
            # 设置登录状态
            st.session_state.user = username
            st.session_state.authenticated = True
            st.session_state.user_role = user_info.get('role', 'user')
            
            # 保存登录信息
            st.session_state.saved_username = username
            st.session_state.saved_password = password
            
            # 更新最后登录时间
            user_mgr.update_last_login(username)
            
            add_log("info", f"User logged in: {username}")
            st.rerun()
            return True
        else:
            st.error("用户名或密码错误")
            add_log("warning", f"Failed login attempt for user: {username}")
            return False
    
    return False 