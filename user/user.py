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
from user.user_process import show_login_page, show_admin_panel, show_user_profile

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

def main():
    try:
        # Load configurations
        config = load_config()
        templates = load_templates()
        
        st.set_page_config(
            page_title=templates["page_title"],
            layout="wide"
        )
        
        # 初始化session state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False

        if 'user' not in st.session_state:
            st.session_state.user = None

        # 侧边栏
        with st.sidebar:
            if st.session_state.authenticated:
                st.write(f"当前用户：{st.session_state.user}")
                if st.button("个人信息"):
                    st.session_state.current_page = 'profile'
                if st.button("退出登录"):
                    st.session_state.user = None
                    st.session_state.authenticated = False
                    st.rerun()
            else:
                st.write("请登录")

        # 主要内容
        if not st.session_state.authenticated:
            show_login_page()
        else:
            if st.session_state.get('current_page') == 'profile':
                show_user_profile()
            else:
                # 这里是你的主要应用内容
                st.title("PRFAQ Pro")
                # ... 其他应用代码 ...
        
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)
        st.error("请检查配置文件是否正确，或联系管理员")

if __name__ == "__main__":
    main()