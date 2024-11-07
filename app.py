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
from user.admin import show_admin_panel
from user.user_process import check_auth, handle_logout, UserManager
from user.chat import show_chat_interface
from user.bill import show_bill_detail
from user.logger import display_logs
from db.db_admin import show_db_admin
from user.user_history import show_user_history

def clear_main_content():
    """Clear all content in the main area except core sentence and logs"""
    preserved_keys = [
        'current_section', 
        'logs', 
        'product_core_sentence',
        'user',  
        'authenticated',  
        'saved_username',  
        'saved_password',  
        'aar_context',  
        'aar_form_data',  
        'aar_generation_started',  
        'aar_data_fact',
        'user_role'
    ]
    for key in list(st.session_state.keys()):
        if key not in preserved_keys:
            del st.session_state[key]

def main():
    try:
        # Load configurations
        config = load_config()
        templates = load_templates()
        
        st.set_page_config(
            page_title=templates["page_title"],
            layout="wide"
        )
        
        # 检查用户是否已登录
        if not check_auth():
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
                st.image("assets/logo.png")
            except Exception as e:
                st.warning("Logo图片未找到")
                add_log("warning", "Logo图片未找到，请确保assets/logo.png存在")
            
            st.title(f"PRFAQ Pro - {st.session_state.user}")
            
            # 如果是管理员，显示管理员功能
            if st.session_state.user_role == 'admin':
                st.header("管理员功能")
                
                if st.button("👥 用户管理", use_container_width=True):
                    clear_main_content()
                    st.session_state.current_section = 'admin'
                    add_log("info", "进入用户管理面板")
                
                if st.button("🗄️ 数据库管理", use_container_width=True):
                    clear_main_content()
                    st.session_state.current_section = 'db_admin'
                    add_log("info", "进入数据库管理面板")
                
                if st.button("🧪 AI聊天测试", use_container_width=True):
                    clear_main_content()
                    st.session_state.current_section = 'chat_test'
                    add_log("info", "进入AI聊天测试")
            
            # 主要功能按钮
            st.header("主要功能")
            
            if st.button("📰 虚拟新闻稿", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'pr'
                add_log("info", "切换到虚拟新闻稿模式")
            
            if st.button("📊 复盘六步法", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'aar'
                add_log("info", "切换到复盘六步法模式")
            
            # 功能块按钮
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
            
            if st.button("📜 历史查看", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'history'
                add_log("info", "进入历史记录查看")
            
            if st.button("💰 账单", use_container_width=True):
                clear_main_content()
                st.session_state.show_bill_detail = True
                add_log("info", "查看账单明细")
            
            # 退出登录按钮
            if st.button("🚪 退出登录", use_container_width=True):
                handle_logout()
        
        # Main content area
        with main_col:
            if st.session_state.current_section == 'admin':
                show_admin_panel()
            elif st.session_state.current_section == 'db_admin':
                show_db_admin()
            elif hasattr(st.session_state, 'show_bill_detail') and st.session_state.show_bill_detail:
                show_bill_detail()
            elif st.session_state.current_section == 'bill_test':
                # 创建API客户端实例
                api_client = APIClient(config)
                show_chat_interface(api_client)
            elif st.session_state.current_section == 'history':
                show_user_history()
            elif st.session_state.current_section == 'all_in_one':
                # 创建API客户端实例
                api_client = APIClient(config)
                all_in_one_generator = AllInOneGenerator(api_client)
                all_in_one_generator.render()
            elif st.session_state.current_section == 'pr':
                # 创API客户端例
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
                display_logs()
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