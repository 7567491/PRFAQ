import streamlit as st
import json
from pathlib import Path
from modules.api import APIClient
from modules.utils import (
    load_config, 
    load_templates, 
    load_history, 
    save_history, 
    load_letters,
    add_log
)
from modules.pr_generator import PRGenerator
from modules.faq_generator import FAQGenerator
from modules.faq_in import InternalFAQGenerator
from modules.mlp_generator import MLPGenerator
from datetime import datetime
import pandas as pd
from modules.all_in_one_generator import AllInOneGenerator
from modules.aar_generator import AARGenerator

def clear_main_content():
    """Clear all content in the main area except core sentence and logs"""
    preserved_keys = [
        'current_section', 
        'logs', 
        'product_core_sentence',
        'user',  # 保留用户信息
        'authenticated',  # 保留认证状态
        'saved_username',  # 保留保存的用户名
        'saved_password',  # 保留保存的密码
        'aar_context',  # 保留AAR的context
        'aar_form_data',  # 保留AAR的表单数据
        'aar_generation_started',  # 保留AAR的生成状态
        'aar_data_fact'  # 保留data_fact数据
    ]
    for key in list(st.session_state.keys()):
        if key not in preserved_keys:
            del st.session_state[key]

def show_customer_faq():
    # 创建API客户端实例
    config = load_config()
    api_client = APIClient(config)
    
    # 创建FAQ生成器并传入api_client
    faq_generator = FAQGenerator(api_client)
    faq_generator.generate_customer_faq()

def show_login_page():
    """显示登录页面"""
    st.title("PRFAQ Pro 登录")
    
    # 检查是否有保存的登录信息
    if 'saved_username' in st.session_state and 'saved_password' in st.session_state:
        username = st.session_state.saved_username
        password = st.session_state.saved_password
        # 自动登录
        st.session_state.user = username
        st.session_state.authenticated = True
        add_log("info", f"用户 {username} 自动登录成功")
        st.rerun()
        return
    
    with st.form("login_form"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        remember = st.checkbox("记住登录状态", value=True)
        submitted = st.form_submit_button("登录")
        
        if submitted:
            if username and password:  # 简单的非空验证
                st.session_state.user = username
                st.session_state.authenticated = True
                
                # 如果选择记住登录状态，保存登录信息
                if remember:
                    st.session_state.saved_username = username
                    st.session_state.saved_password = password
                
                add_log("info", f"用户 {username} 登录成功")
                st.rerun()
            else:
                st.error("请输入用户名和密码")

def main():
    try:
        # Load configurations
        config = load_config()
        templates = load_templates()
        
        st.set_page_config(
            page_title=templates["page_title"],
            layout="wide"
        )
        
        # 添加自定义CSS
        st.markdown("""
            <style>
            /* 自定义按钮样式 */
            .stButton > button {
                border: 2px solid #FFB700; /* 黄色边框 */
                background-color: transparent; /* 无填充 */
                color: white; /* 文字颜色保持白色 */
                padding: 0.5rem 1rem; /* 按钮内边距 */
                font-weight: bold; /* 加粗文字 */
                transition: background-color 0.3s ease; /* 背景色过渡 */
            }
            .stButton > button:hover {
                background-color: #FFF5CC; /* 悬停时的背景色 */
                color: black; /* 悬停时文字颜色变为黑色 */
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 检查是否已登录
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            show_login_page()
            return
        
        # Initialize session state
        if 'current_section' not in st.session_state:
            st.session_state.current_section = 'pr'
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        
        # Create main content and log columns
        main_col, log_col = st.columns([5, 1])
        
        with st.sidebar:
            # 添加logo（带错误处理）
            try:
                st.image("assets/logo.jpg")
            except Exception as e:
                st.warning("Logo图片未找到")
                add_log("warning", "Logo图片未找到，请确保assets/logo.jpg存在")
            
            st.title(f"PRFAQ Pro - {st.session_state.user}")  # 显示当前用户
            
            # Navigation buttons
            st.header("主要功能")
            
            # 主要功能按钮
            if st.button("📰 虚拟新闻稿", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'pr'
                add_log("info", "切换到虚拟新闻稿模式")
            
            if st.button("📊 复盘六步法", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'aar'
                add_log("info", "切换到复盘六步法模式")
            
            # 功能模块按钮
            st.header("功能模块")
            
            if st.button("❓ 客户 FAQ", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'faq'
                add_log("info", "切换到客户FAQ模式")
            
            if st.button("📋 内部 FAQ", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'internal_faq'
                add_log("info", "切换到内部FAQ模式")
            
            if st.button("🚀 MLP开发", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'mlp'
                add_log("info", "切换到MLP开发模式")
            
            if st.button("✨ PRFAQ一键生成", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'all_in_one'
                add_log("info", "切换到PRFAQ一键生成模式")
            
            # 系统功能按钮
            st.header("系统功能")
            
            if st.button("🧪 账单测试", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'bill_test'
                add_log("info", "切换到账单测试模式")
            
            if st.button("💰 账单", use_container_width=True):
                clear_main_content()
                st.session_state.show_bill_detail = True
                add_log("info", "查看账单明细")
            
            # 退出登录按钮
            if st.button("🚪 退出登录", use_container_width=True):
                # 先添加日志
                add_log("info", f"用户 {st.session_state.user} 退出登录")
                
                # 清除所有session state
                st.session_state.clear()
                
                # 重新运行应用
                st.rerun()
            
            # History section
            st.header("历史记录")
            history = load_history()
            for idx, item in enumerate(reversed(history)):
                if st.button(
                    f"#{len(history)-idx} {item['timestamp'][:16]}",
                    key=f"history_{idx}",
                    help="点击查看详情",
                    use_container_width=True
                ):
                    # 清空主屏幕内容
                    clear_main_content()
                    # 设置当前部分为历史记录
                    st.session_state.current_section = 'history'
                    # 保存选中的历史记录
                    st.session_state.selected_history = item
                    st.session_state.show_history_detail = True
                    add_log("info", f"查看历史记录 #{len(history)-idx}")
        
        # Main content area
        with main_col:
            if hasattr(st.session_state, 'show_bill_detail') and st.session_state.show_bill_detail:
                st.markdown("### 账单明细")
                letters_data = load_letters()  # 加载字符统计数据
                
                # 显示总账单
                total = letters_data["total"]
                st.markdown("#### 总消费")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总消费(人民币)", f"{total['cost_rmb']:.6f} 元")
                with col2:
                    st.metric("总输入字符数", f"{total['input_letters']:,}")
                with col3:
                    st.metric("总输出字符数", f"{total['output_letters']:,}")
                
                st.markdown("#### 消费记录")
                # 创账单明细表格
                records_df = pd.DataFrame(letters_data["records"])
                if not records_df.empty:
                    records_df['timestamp'] = pd.to_datetime(records_df['timestamp'])
                    records_df = records_df.sort_values('timestamp', ascending=False)
                    
                    # 格式化显示的列
                    st.dataframe(
                        records_df[[
                            'timestamp', 'api_name', 'operation',
                            'input_letters', 'output_letters',
                            'total_cost_rmb', 'total_cost_usd'
                        ]].style.format({
                            'total_cost_rmb': '{:.6f}',
                            'total_cost_usd': '{:.6f}'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("暂无账单记录")
            
            elif st.session_state.current_section == 'history' and hasattr(st.session_state, 'show_history_detail') and st.session_state.show_history_detail:
                st.markdown(f"### 生成记录 - {st.session_state.selected_history['timestamp']}")
                st.markdown(st.session_state.selected_history['content'])
            
            elif st.session_state.current_section == 'all_in_one':
                # 创建API客户端实例
                api_client = APIClient(config)
                all_in_one_generator = AllInOneGenerator(api_client)
                all_in_one_generator.render()
            elif st.session_state.current_section == 'pr':
                # 创API客户端实例
                api_client = APIClient(config)
                pr_generator = PRGenerator(api_client)
                pr_generator.render()
            elif st.session_state.current_section == 'faq':
                # 创建API客户端实例
                api_client = APIClient(config)
                faq_generator = FAQGenerator(api_client)
                faq_generator.generate_customer_faq()
            elif st.session_state.current_section == 'internal_faq':
                # 创建API客户端实例
                api_client = APIClient(config)
                faq_generator = InternalFAQGenerator(api_client)
                faq_generator.generate_internal_faq()
            elif st.session_state.current_section == 'bill_test':
                st.markdown("### 账单测试")
                
                # 创建一个聊天历史容器
                chat_container = st.container()
                
                # 创建输入框和发送按钮
                with st.form("chat_form", clear_on_submit=True):
                    user_input = st.text_area("请输入您的问题:", height=100)
                    submitted = st.form_submit_button("发送")
                
                # 初始化聊天历史
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []
                
                # 处理用户输入
                if submitted and user_input:
                    # 添加用户消息到历史
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    # 创建API客户端
                    api_client = APIClient(config)
                    
                    # 创建一个空白占位符用于显示AI回复
                    response_placeholder = st.empty()
                    content = ""
                    
                    # 流式生成回复
                    for chunk in api_client.generate_content_stream(user_input):
                        content += chunk
                        response_placeholder.markdown(content)
                    
                    # 添加AI回复到历史
                    st.session_state.chat_history.append({"role": "assistant", "content": content})
                
                # 在聊天容器中显示历史消息
                with chat_container:
                    for message in st.session_state.chat_history:
                        if message["role"] == "user":
                            st.markdown(f"**👤 您:** {message['content']}")
                        else:
                            st.markdown(f"**🤖 AI:** {message['content']}")
                            st.markdown("---")
            elif st.session_state.current_section == 'mlp':
                # 创建API客户端实例
                api_client = APIClient(config)
                mlp_generator = MLPGenerator(api_client)
                mlp_generator.generate_mlp()
            elif st.session_state.current_section == 'aar':
                # 创建API客户端实例
                api_client = APIClient(config)
                aar_generator = AARGenerator(api_client)
                aar_generator.render()
            else:
                st.info(f"{templates['sections'][st.session_state.current_section]['title']}能正在开发中...")
            
            # Log panel
            with log_col:
                st.markdown("### 系统日志")
                
                # 直接显示日志内容,不使用容器
                for log in st.session_state.logs:
                    # 根据日志类型选择不同的CSS类
                    if log['level'] == 'error':
                        color = "#FF0000"  # 错误信息用红色
                    elif log['level'] == 'user':
                        color = "#FFB700"  # 用户操作用黄色
                    elif log['level'] == 'warning':
                        color = "#FFFF00"  # 警告信息用亮黄色
                    else:
                        color = "#00FF00"  # 程序步骤用绿色
                        
                    st.markdown(f'<span style="color: {color};">[{log["timestamp"]}] {log["message"]}</span>', 
                              unsafe_allow_html=True)
                
                # Add clear logs button
                if st.button("清除日志", key="clear_logs"):
                    st.session_state.logs = []
                    add_log("info", "日志已清除")
        
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)
        st.error("请检查配置文件是否正确，或联系管理员")

if __name__ == "__main__":
    main()