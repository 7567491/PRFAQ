import streamlit as st
from modules.utils import add_log
from admin.overview import show_user_overview
from admin.analysis import show_user_analysis
from admin.user_mp import show_mp_users
from admin.user_management import show_user_management
from admin.analysis_mp import show_mp_analysis

def show_admin_panel():
    """显示管理员控制面板"""
    st.title("管理员控制面板")
    
    try:
        # 创建五个标签页
        tabs = st.tabs(["用户管理", "用户概览", "用户分析", "AWS MP用户", "MP分析"])
        
        # 用户管理标签页
        with tabs[0]:
            add_log("info", "加载用户管理页面")
            show_user_management()
            
        # 用户概览标签页
        with tabs[1]:
            add_log("info", "加载用户概览页面")
            show_user_overview()
            
        # 用户分析标签页
        with tabs[2]:
            add_log("info", "加载用户分析页面")
            show_user_analysis()
            
        # AWS MP用户标签页
        with tabs[3]:
            add_log("info", "加载AWS MP用户页面")
            show_mp_users()
            
        # MP分析标签页
        with tabs[4]:
            add_log("info", "加载MP分析页面")
            show_mp_analysis()
            
    except Exception as e:
        error_msg = f"管理面板加载失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg) 