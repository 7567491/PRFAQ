import streamlit as st
from datetime import datetime
import os
import sqlite3
from db.db_read import read_database
from db.db_restore import show_restore_interface
from db.db_table import show_table_info
from db.db_overview import show_db_overview
from db.db_status import show_db_status
from db.db_clear import show_clear_interface
from user.logger import add_log
import pandas as pd
from pathlib import Path

def show_db_admin():
    """显示数据库管理界面"""
    if st.session_state.get('user_role') != 'admin':
        st.error("无权限访问此页面")
        return
    
    st.title("数据库管理")
    
    # 添加新的数据清理选项卡
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👀 数据库一览",
        "📊 数据库结构",
        "♻️ 恢复",
        "📋 表结构",
        "🧹 数据清理"
    ])
    
    with tab1:
        show_db_overview()
    
    with tab2:
        show_db_status()
    
    with tab3:
        show_restore_interface()
    
    with tab4:
        show_table_info()
        
    with tab5:
        show_clear_interface()