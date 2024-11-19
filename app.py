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
from bill.bill import BillManager, show_bill_detail
from user.logger import display_logs
from db.db_admin import show_db_admin
from user.user_history import show_user_history
from db.db_upgrade import check_and_upgrade
import sys
import traceback
from aws import show_aws_mp_panel

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
        # 检查并升级数据库
        upgrade_result = check_and_upgrade()
        if not upgrade_result:
            st.error("数据库升级失败，请检查日志")
            add_log("error", "数据库升级失败，程序无法继续运行")
            return
        
        # Load configurations
        config = None
        templates = None
        try:
            config = load_config()
            if not config:
                st.error("配置文件加载失败：config 为空")
                add_log("error", "配置文件加载失败：config 为空")
                return
                
            templates = load_templates()
            if not templates:
                st.error("模板文��加载失败：templates 为空")
                add_log("error", "模板文件加载失败：templates 为空")
                return
                
        except Exception as e:
            st.error(f"加载配置文件失败: {str(e)}")
            add_log("error", f"加载配置文件失败: {str(e)}")
            return
            
        # 设置页面配置
        try:
            st.set_page_config(
                page_title="六页纸AI",
                layout="wide"
            )
        except Exception as e:
            st.error(f"设置页面配置失败: {str(e)}")
            add_log("error", f"设置页面配置失败: {str(e)}")
            return
        
        # 检查用户是否已登录
        if not check_auth():
            return
            
        # Initialize session state
        if 'current_section' not in st.session_state:
            st.session_state.current_section = 'pr'
        if 'logs' not in st.session_state:
            st.session_state.logs = []
            
        # 创建侧边栏
        render_sidebar()
        
        # 根据用户色决定布局
        if st.session_state.user_role == 'admin':
            # 管理员显示日志，使用 5:1 的布局
            main_col, log_col = st.columns([5, 1])
            
            # 主内容区域
            with main_col:
                render_main_content(config, templates)
            
            # 日志面板
            with log_col:
                display_logs()
                # Add clear logs button
                if st.button("清除日志", key="clear_logs"):
                    st.session_state.logs = []
                    add_log("info", "日志已清除")
        else:
            # 普通用户不显示日志，直接渲染主内容
            render_main_content(config, templates)
        
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)
        st.error("请检查配置文件是否正确，或联系管理员")

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # 添加自定义CSS样式
        st.markdown("""
        <style>
            /* 所有侧边栏按钮的基础样式 */
            .stButton > button {
                width: 100%;
                color: white !important;
                border: 2px solid #ffd700 !important;
                background-color: transparent !important;
                margin: 5px 0;
                transition: all 0.3s ease;
            }
            
            /* 鼠标悬停效��� */
            .stButton > button:hover {
                color: black !important;
                background-color: #ffd700 !important;
                border-color: #ffd700 !important;
            }
            
            /* 确保激活状态也保持相同样式 */
            .stButton > button:active, .stButton > button:focus {
                color: white !important;
                background-color: transparent !important;
                border-color: #ffd700 !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # 添加logo（带错误处理）
        try:
            st.image("assets/logo.png")
        except Exception as e:
            st.warning("Logo图片未找到")
            add_log("warning", "Logo图片未找到，请确保assets/logo.png存在")
        
        st.title(f"助你高效 - {st.session_state.user}")
        
        # 显示用户积分
        user_mgr = UserManager()
        bill_mgr = BillManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        if user_info:
            points_info = bill_mgr.get_user_points(user_info['user_id'])
            st.metric("当前积分", f"{points_info:,}")
        
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
            
            if st.button("☁️ AWS集成", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'aws_mp'
                add_log("info", "进入AWS集成面板")
        
        # 主要功能按钮
        st.header("主要功能")
        
        if st.button("🎯 领导力测评", use_container_width=True):
            clear_main_content()
            st.session_state.current_section = 'career_test'
            add_log("info", "进入领导力测评")

        if st.button("📰 逆向工作法", use_container_width=True):
            clear_main_content()
            st.session_state.current_section = 'pr'
            add_log("info", "切换到逆向工作法模式")
        
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
        
        if st.button("💰 积分明细", use_container_width=True):
            clear_main_content()
            st.session_state.current_section = 'bill'
            add_log("info", "查看积分明细")
        
        # 退出登录按钮
        if st.button("🚪 退出登录", use_container_width=True):
            handle_logout()

def render_main_content(config, templates):
    """渲染主要内容区域"""
    if st.session_state.current_section == 'admin':
        show_admin_panel()
    elif st.session_state.current_section == 'db_admin':
        show_db_admin()
    elif st.session_state.current_section == 'aws_mp':
        show_aws_mp_panel()
    elif st.session_state.current_section == 'chat_test':
        api_client = APIClient(config)
        show_chat_interface(api_client)
    elif st.session_state.current_section == 'history':
        show_user_history()
    elif st.session_state.current_section == 'bill':
        show_bill_detail()
    elif st.session_state.current_section == 'all_in_one':
        api_client = APIClient(config)
        all_in_one_generator = AllInOneGenerator(api_client)
        all_in_one_generator.render()
    elif st.session_state.current_section == 'pr':
        st.markdown("""
        逆向工作法是一种从结果反推过程的创新思维方法。通过先设想理想的最终成果，再逐步分析实现这个结果所需的步骤和条件，帮助我们更清晰地规划项目路径。本模块将帮助您运用这种方法，通过编写未来新闻稿的形式，明确项目目标和关键成功要素。您只需要输入产品的核心理念，系统就会协助您生成完整的项目愿景说明，包括目标受众、价值主张、功能特性等关键内容。
        """)
        api_client = APIClient(config)
        pr_generator = PRGenerator(api_client)
        pr_generator.render()
    elif st.session_state.current_section == 'faq':
        api_client = APIClient(config)
        faq_generator = FAQGenerator(api_client)
        faq_generator.generate_customer_faq()
    elif st.session_state.current_section == 'internal_faq':
        api_client = APIClient(config)
        faq_generator = InternalFAQGenerator(api_client)
        faq_generator.generate_internal_faq()
    elif st.session_state.current_section == 'mlp':
        api_client = APIClient(config)
        mlp_generator = MLPGenerator(api_client)
        mlp_generator.generate_mlp()
    elif st.session_state.current_section == 'aar':
        st.markdown("""
        复盘六步法源于军事领域的"事后复盘"（After Action Review），后被广泛应用于企业管理实践中。它通过六个系统化步骤：设定复盘目标、回顾行动过程、对比预期结果、分析差距原因、总结经验教训、形成复盘文档，帮助团队从实践中提炼经验，持续改进。本模块将引导您完整地执行这六个步骤，通过AI辅助分析，帮助您更深入地思考项目经验，形成可复用的经验总结文档。
        """)
        api_client = APIClient(config)
        aar_generator = AARGenerator(api_client)
        aar_generator.render()
    elif st.session_state.current_section == 'career_test':
        try:
            add_log("info", "开始加载领导力测评模块...")
            
            # 检查必要的目录和文件
            test_dir = Path("test")
            if not test_dir.exists():
                raise FileNotFoundError("test目录不存在")
            add_log("info", f"test目录存在: {test_dir.absolute()}")
            
            # 检查数据目录
            data_dir = test_dir / "data"
            if not data_dir.exists():
                raise FileNotFoundError("test/data目录不存在")
            add_log("info", f"data目录存在: {data_dir.absolute()}")
            
            # 尝试导入模块
            add_log("info", "尝试导入CareerTest类...")
            try:
                from test.test import CareerTest
                add_log("info", "成功导入CareerTest类")
            except ImportError as e:
                if "docx" in str(e):
                    st.error("""
                    缺少必要的依赖包：python-docx
                    
                    请联系管理员安装所需依赖。
                    """)
                    add_log("error", "缺少必要的依赖包：python-docx")
                    return
                raise
            
            # 初始化测试模块
            career_test = CareerTest()
            add_log("info", "成功初始化CareerTest实例")
            
            # 渲染测试界面
            result = career_test.render()
            
            # 如果测试完成并有结果，保存到历史记
            if result and 'final_result' in st.session_state:
                try:
                    save_history(
                        st.session_state.user,
                        'leadership_test',
                        st.session_state.final_result
                    )
                    add_log("info", "领导力测评结果已保存到历史记录")
                except Exception as e:
                    add_log("error", f"保存领导力测评结果失败: {str(e)}")
            
        except ImportError as e:
            error_msg = f"导入模块失败: {str(e)}\n"
            error_msg += f"Python路径: {sys.path}\n"
            error_msg += f"当前目录: {Path.cwd()}"
            st.error(error_msg)
            add_log("error", error_msg)
        except Exception as e:
            error_msg = f"加载领导力测评模块失败: {str(e)}\n"
            error_msg += f"错误类型: {type(e).__name__}\n"
            error_msg += f"错误位置: {traceback.format_exc()}"
            st.error(error_msg)
            add_log("error", error_msg)
    else:
        st.info(f"{templates['sections'][st.session_state.current_section]['title']}能正在开发中...")

if __name__ == "__main__":
    main()