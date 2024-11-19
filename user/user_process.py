import streamlit as st
from user.user_base import UserManager
from modules.notifier import send_wecom_message, get_client_ip, get_client_os
from datetime import datetime

def init_session_state():
    """初始化session state中的用户相关变量"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'show_registration' not in st.session_state:
        st.session_state.show_registration = False

def show_registration_form():
    """显示注册表单"""
    st.title("新用户注册")
    
    with st.form("registration_form"):
        # 基本信息
        username = st.text_input("用户名 *")
        password = st.text_input("密码 *", type="password")
        confirm_password = st.text_input("确认密码 *", type="password")
        
        # 联系信息
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("电子邮箱 *", 
                                placeholder="example@company.com")
        with col2:
            phone = st.text_input("手机号码 *",
                                placeholder="13812345678")
        
        # 组织信息
        org_name = st.text_input("组织名称",
                               placeholder="公司/组织名称")
        
        # 用户协议
        st.markdown("""
        ### 用户协议
        1. 请确保提供的信息真实准确
        2. 我们将严格保护您的个人信息
        3. 禁止使用系统进行任何违法违规活动
        """)
        agree = st.checkbox("我已阅读并同意用户协议")
        
        submitted = st.form_submit_button("注册")
        
        if submitted:
            # 验证必填字段
            if not all([username, password, confirm_password, email, phone]):
                st.error("请填写所有必填项（带*号的字段）")
                return
                
            # 验证密码
            if password != confirm_password:
                st.error("两次输入的密码不一致")
                return
                
            # 验证用户协议
            if not agree:
                st.error("请阅读并同意用户协议")
                return
                
            # 准备用户数据
            user_data = {
                'email': email,
                'phone': phone,
                'org_name': org_name
            }
            
            user_mgr = UserManager()
            success, message = user_mgr.create_user(username, password, user_data)
            
            if success:
                # 发送注册通知
                ip = get_client_ip()
                os_info = get_client_os()
                send_wecom_message('login', username, ip=ip, os=os_info)
                
                st.success("注册成功！请使用新账号登录。")
                # 保存注册信息用于自动填充登录表单
                st.session_state.new_registered_user = {
                    'username': username,
                    'password': password
                }
                # 返回登录页面
                st.session_state.show_registration = False
                st.rerun()
            else:
                st.error(f"注册失败: {message}")
    
    # 添加返回登录按钮
    if st.button("返回登录"):
        st.session_state.show_registration = False
        st.rerun()

def award_daily_login(self, user_id, username):
    """处理每日登录奖励"""
    try:
        conn = self.get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # 检查今天是否已经领取过奖励
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT 1 FROM point_transactions 
            WHERE user_id = ? AND type = 'reward' 
            AND description = '每日登录奖励'
            AND DATE(timestamp) = ?
        """, (user_id, today))
        
        if not cursor.fetchone():
            # 获取当前积分
            cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
            current_points = cursor.fetchone()[0]
            
            # 添加5000积分奖励
            new_points = current_points + 5000
            
            # 更新用户积分
            cursor.execute("""
                UPDATE users 
                SET points = ? 
                WHERE user_id = ?
            """, (new_points, user_id))
            
            # 记录积分交易
            cursor.execute("""
                INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance,
                    description, operation_id
                ) VALUES (?, ?, 'reward', 5000, ?, '每日登录奖励', ?)
            """, (
                user_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                new_points,
                f"daily_login_{today}"
            ))
            
            conn.commit()
            
            # 发送通知
            send_wecom_message('action', username,
                action="获得每日登录奖励",
                details="奖励5000积分"
            )
            
            add_log("info", f"用户 {username} 获得每日登录奖励: 5000积分")
            
        conn.close()
        return True
        
    except Exception as e:
        add_log("error", f"处理每日登录奖励失败: {str(e)}")
        return False

def check_auth():
    """检查用户是否已认证"""
    init_session_state()
    
    if st.session_state.authenticated:
        return True
        
    # 如果是注册状态，显示注册表单
    if st.session_state.show_registration:
        show_registration_form()
        return False
    
    # 显示登录表单
    with st.form("login_form"):
        # 获取默认的用户名和密码
        default_username = ""
        default_password = ""
        
        # 检查是否有新注册用户信息
        if hasattr(st.session_state, 'new_registered_user'):
            default_username = st.session_state.new_registered_user['username']
            default_password = st.session_state.new_registered_user['password']
            # 清除注册信息
            del st.session_state.new_registered_user
        # 检查是否有保存的登录信息
        elif 'saved_username' in st.session_state and 'saved_password' in st.session_state:
            default_username = st.session_state.saved_username
            default_password = st.session_state.saved_password
        
        username = st.text_input("用户名", value=default_username)
        password = st.text_input("密码", type="password", value=default_password)
        remember = st.checkbox("记住登录状态", value=True)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("登录")
        with col2:
            register = st.form_submit_button("注册新用户")
        
        if submitted:
            if username and password:
                user_mgr = UserManager()
                if user_mgr.verify_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.user = username
                    st.session_state.user_role = user_mgr.get_user_role(username)
                    
                    # 获取用户信息
                    user_info = user_mgr.get_user_info(username)
                    
                    # 处理每日登录奖励
                    if user_info:
                        user_mgr.award_daily_login(user_info['user_id'], username)
                    
                    # 获取用户IP和操作系统信息
                    ip = get_client_ip()
                    os_info = get_client_os()
                    
                    # 发送登录通知
                    send_wecom_message('login', username, ip=ip, os=os_info)
                    
                    if remember:
                        st.session_state.saved_username = username
                        st.session_state.saved_password = password
                    
                    # 更新最后登录时间
                    user_mgr.update_last_login(username)
                    
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            else:
                st.error("请输入用户名和密码")
        
        if register:
            st.session_state.show_registration = True
            st.rerun()
            
    return False

def handle_logout():
    """处理用户退出登录"""
    if st.session_state.get('user'):
        # 发送退出登录通知
        send_wecom_message('action', st.session_state.user,
            action="退出登录",
            details="用户主动退出系统"
        )
        
    # 清除所有会话状态
    st.session_state.clear()
    
    # 清除URL参数
    st.experimental_set_query_params()
    
    # 重新加载页面
    st.rerun()

# 导出需要的函数和类
__all__ = ['check_auth', 'handle_logout', 'UserManager']