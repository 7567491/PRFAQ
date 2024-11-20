import streamlit as st
from datetime import datetime
import os
import sqlite3
from db.read_db import read_database
from db.db_restore import show_restore_interface
from db.db_table import show_table_info
from user.logger import add_log
import pandas as pd
from pathlib import Path

def get_db_connection():
    """获取数据库连接"""
    try:
        # 确保数据库目录存在
        db_dir = Path("db")
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
            
        # 连接到数据库
        conn = sqlite3.connect('db/app.db')
        conn.row_factory = sqlite3.Row  # 设置行工厂，使结果可以通过列名访问
        return conn
    except Exception as e:
        add_log("error", f"数据库连接失败: {str(e)}")
        st.error(f"数据库连接失败: {str(e)}")
        return None

def show_db_admin():
    """显示数据库管理界面"""
    if st.session_state.get('user_role') != 'admin':
        st.error("无权限访问此页面")
        return
    
    st.title("数据库管理")
    
    # 使用选项卡来组织不同功能
    tab1, tab2, tab3 = st.tabs([
        "📊 数据库状态",
        "♻️ 恢复",
        "📋 表结构"
    ])
    
    with tab1:
        st.markdown("### 数据库查看")
        if st.button("刷新数据库信息", use_container_width=True):
            try:
                if os.path.exists('db/users.db'):
                    # 获取数据库信息
                    db_info = read_database()
                    
                    # 显示表结构
                    st.markdown("#### 表结构")
                    st.code(db_info['schema'])
                    
                    # 显示用户数据（隐藏敏感信息）
                    st.markdown("#### 用户数据")
                    users_df = db_info['users'].copy()
                    if 'password' in users_df.columns:
                        users_df['password'] = '******'  # 隐藏密码
                    st.dataframe(users_df)
                    
                    # 显示数据库统计
                    st.markdown("#### 数据库统计")
                    
                    # 账单统计
                    st.markdown("##### 账单记录")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总账单数", f"{db_info['bills_stats']['total_count']:,}")
                    with col2:
                        st.metric("总输入字符", f"{db_info['bills_stats']['total_input']:,}")
                    with col3:
                        st.metric("总输出字符", f"{db_info['bills_stats']['total_output']:,}")
                    with col4:
                        st.metric("使用天数", f"{db_info['bills_stats']['unique_days']:,}")
                    
                    # 历史记录统计
                    st.markdown("##### 历史记录")
                    col5, col6, col7, col8 = st.columns(4)
                    with col5:
                        st.metric("总记录数", f"{db_info['history_stats']['total_count']:,}")
                    with col6:
                        st.metric("记录类型数", f"{db_info['history_stats']['unique_types']:,}")
                    with col7:
                        st.metric("活跃用户数", f"{db_info['history_stats']['unique_users']:,}")
                    with col8:
                        st.metric("记录天数", f"{db_info['history_stats']['unique_days']:,}")
                    
                    # 积分统计
                    st.markdown("##### 积分统计")
                    col9, col10, col11, col12 = st.columns(4)
                    with col9:
                        st.metric("总交易数", f"{db_info['points_stats']['total_transactions']:,}")
                    with col10:
                        st.metric("总奖励积分", f"{db_info['points_stats']['total_rewards']:,}")
                    with col11:
                        st.metric("总消费积分", f"{db_info['points_stats']['total_consumed']:,}")
                    with col12:
                        st.metric("活跃用户数", f"{db_info['points_stats']['unique_users']:,}")
                    
                    add_log("info", "查看数据库信息")
                else:
                    st.error("数据文件不存在")
                    add_log("error", "尝试查看时发现数据库文件不存在")
            except Exception as e:
                error_msg = f"查看数据库失败: {str(e)}"
                st.error(error_msg)
                add_log("error", error_msg)
    
    with tab2:
        show_restore_interface()
    
    with tab3:
        show_table_info()