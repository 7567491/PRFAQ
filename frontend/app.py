import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path
from generators import generate_pr, generate_customer_faq, generate_internal_faq, generate_mlp
from billing import show_billing, add_quota_dialog
from styles import load_css

def init_session_state():
    """初始化会话状态"""
    # 初始化基本状态
    if 'API_URL' not in st.session_state:
        st.session_state.API_URL = "http://localhost:8000"
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'show_billing' not in st.session_state:
        st.session_state.show_billing = False
    if 'show_add_quota' not in st.session_state:
        st.session_state.show_add_quota = False
    if 'system_logs' not in st.session_state:
        st.session_state.system_logs = []
    
    # 从本地存储加载登录信息
    if 'saved_credentials' not in st.session_state:
        try:
            with open('.credentials.json', 'r') as f:
                import json
                credentials = json.load(f)
                st.session_state.saved_credentials = credentials
                # 自动登录
                if not st.session_state.token:
                    try:
                        response = requests.post(
                            f"{st.session_state.API_URL}/auth/token",
                            data={
                                "username": credentials["username"],
                                "password": credentials["password"]
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.token = data["access_token"]
                            st.session_state.current_user = credentials["username"]
                    except:
                        pass
        except:
            st.session_state.saved_credentials = None
    
    # 添加日志函数到session_state
    def add_log(message: str):
        if 'system_logs' not in st.session_state:
            st.session_state.system_logs = []
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.system_logs.append(f"[{timestamp}] {message}")
        # 保持最新的20条日志
        if len(st.session_state.system_logs) > 20:
            st.session_state.system_logs.pop(0)
    
    st.session_state.add_log = add_log

def login_page():
    """登录页面"""
    st.title("PRFAQ Pro - 登录")
    
    # 如果有保存的凭证，自动填充
    saved_username = ""
    saved_password = ""
    if st.session_state.saved_credentials:
        saved_username = st.session_state.saved_credentials.get("username", "")
        saved_password = st.session_state.saved_credentials.get("password", "")
    
    with st.form("login_form"):
        username = st.text_input("用户名", value=saved_username)
        password = st.text_input("密码", type="password", value=saved_password)
        remember_me = st.checkbox("记住我", value=bool(st.session_state.saved_credentials))
        submitted = st.form_submit_button("登录")
        
        if submitted:
            try:
                response = requests.post(
                    f"{st.session_state.API_URL}/auth/token",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.current_user = username
                    
                    # 如果选择了记住我，保存凭证到本地文件
                    if remember_me:
                        import json
                        credentials = {
                            "username": username,
                            "password": password
                        }
                        with open('.credentials.json', 'w') as f:
                            json.dump(credentials, f)
                        st.session_state.saved_credentials = credentials
                    else:
                        # 如果取消记住我，删除保存的凭证
                        import os
                        if os.path.exists('.credentials.json'):
                            os.remove('.credentials.json')
                        st.session_state.saved_credentials = None
                        
                    st.success("登录成功!")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            except Exception as e:
                st.error(f"登录失败: {str(e)}")
    
    # 注册链接
    if st.button("还没有账号？点击注册"):
        st.session_state.show_register = True
        st.rerun()

def register_page():
    """注册页面"""
    st.title("PRFAQ Pro - 注册")
    
    with st.form("register_form"):
        username = st.text_input("用户名")
        email = st.text_input("邮箱")
        password = st.text_input("密码", type="password")
        password2 = st.text_input("确认密码", type="password")
        submitted = st.form_submit_button("注册")
        
        if submitted:
            if not username or not email or not password:
                st.error("所有字段都必须填写")
                return
                
            if password != password2:
                st.error("两次输入的密码不一致")
                return
                
            try:
                # 构建注册数据
                register_data = {
                    "username": username.strip(),
                    "email": email.strip(),
                    "password": password
                }
                
                # 发送注册请求
                response = requests.post(
                    f"{st.session_state.API_URL}/auth/register",
                    json=register_data,
                    headers={"Content-Type": "application/json"}
                )
                
                # 检查响应
                if response.status_code == 200:
                    st.success("注册成功!请返回登录")
                    st.session_state.show_register = False
                    st.rerun()
                elif response.status_code == 400:
                    st.error(response.json()["detail"])
                else:
                    st.error(f"注册失败: HTTP {response.status_code}")
                    st.error(f"错误详情: {response.text}")
                    
            except Exception as e:
                st.error(f"注册失败: {str(e)}")
    
    # 返回登录
    if st.button("返回登录"):
        st.session_state.show_register = False
        st.rerun()

def main_page():
    """主页面"""
    # 创建两列布局：主内容和调试日志，调整比例为8:2
    main_col, log_col = st.columns([0.8, 0.2])  # 修改比例为8:2
    
    # 侧边栏和布局样式设置
    st.markdown("""
        <style>
        /* 恢复侧边栏默认宽度 */
        [data-testid="stSidebar"] {
            width: 260px !important;
        }
        
        /* 主内容区左对齐 */
        .main-content {
            text-align: left !important;
            padding-left: 0 !important;
            margin-left: 0 !important;
        }
        .main-content .stMarkdown {
            text-align: left !important;
        }
        
        /* 日志区右对齐 */
        .log-content {
            text-align: right !important;
            padding-right: 0 !important;
        }
        .log-content .stMarkdown {
            text-align: right !important;
        }
        .log-content pre {
            text-align: right !important;
            direction: rtl !important;
        }
        .log-content code {
            text-align: left !important;
            direction: ltr !important;
            display: inline-block !important;
        }
        
        /* 表单样式 */
        .stForm {
            text-align: left !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        # 添加logo到侧边栏顶部
        st.markdown(
            f"""
            <div class="sidebar-logo">
                <img src="data:image/jpg;base64,{get_base64_logo()}" alt="PRFAQ Pro Logo">
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown(f"👤 **{st.session_state.current_user}**")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.header("💰 账单管理")
        if st.button("查看账单", key="view_billing"):
            st.session_state.show_billing = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("🚪 退出登录", key="logout"):
            st.session_state.token = None
            st.session_state.current_user = None
            if 'stored_token' in st.session_state:
                del st.session_state['stored_token']
            st.rerun()
    
    # 主内容区
    with main_col:
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        st.markdown('<h1 class="main-title">PRFAQ Pro</h1>', unsafe_allow_html=True)
        
        if hasattr(st.session_state, 'show_billing') and st.session_state.show_billing:
            show_billing()
            if hasattr(st.session_state, 'show_add_quota') and st.session_state.show_add_quota:
                add_quota_dialog()
        else:
            tab1, tab2, tab3, tab4 = st.tabs([
                "📝 PR生成",
                "❓ 客户FAQ",
                "📋 内部FAQ",
                "🚀 MLP开发"
            ])
            
            with tab1:
                generate_pr()
            with tab2:
                generate_customer_faq()
            with tab3:
                generate_internal_faq()
            with tab4:
                generate_mlp()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 系统日志区
    with log_col:
        st.markdown('<div class="log-content">', unsafe_allow_html=True)
        st.markdown("### 系统日志")
        if 'system_logs' not in st.session_state:
            st.session_state.system_logs = []
        
        # 显示日志内容
        log_container = st.empty()
        log_text = "\n".join(st.session_state.system_logs)
        log_container.code(log_text)
        st.markdown('</div>', unsafe_allow_html=True)

def get_base64_logo():
    """获取base64编码的logo"""
    import base64
    from pathlib import Path
    
    logo_path = Path(__file__).parent / "logo.jpg"
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def main():
    """主函数"""
    # 加载自定义CSS
    st.markdown(load_css(), unsafe_allow_html=True)
    
    # 确保在任何其他操作之前初始化状态
    init_session_state()
    
    if not st.session_state.token:
        if st.session_state.show_register:
            register_page()
        else:
            login_page()
    else:
        main_page()

if __name__ == "__main__":
    main() 