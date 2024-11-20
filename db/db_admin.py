import streamlit as st
from datetime import datetime
import os
import sqlite3
from db.backup_db import backup_database
from db.db_init import init_database
from db.read_db import read_database
from db.db_restore import show_restore_interface
from db.migrate_data import show_migrate_interface
from db.db_table import show_table_info
from db.db_upgrade import upgrade_database
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 数据库状态",
        "🔧 初始化",
        "💾 备份",
        "♻️ 恢复",
        "📥 数据迁移",
        "📋 表结构",
        "⚡ 数据库升级"
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
        st.markdown("### 数据库初始化")
        st.warning("⚠️ 初始化操作会影响数据库结构，请谨慎操作！")
        
        # 检查数据库是否存在
        db_exists = os.path.exists('db/users.db')
        
        if db_exists:
            st.info("数据库文件已存在")
            confirm = st.checkbox("确定要重新初始化吗？这将删除所有现有数据！")
            if confirm:
                if st.button("确认重新初始化", use_container_width=True):
                    try:
                        # 先备份现有数据库
                        add_log("info", "开始备份现有数据库...")
                        if backup_database():
                            add_log("info", "现有数据库备份成功")
                            # 删除现有数据库
                            os.remove('db/users.db')
                            add_log("info", "已删除现有数据库")
                            # 执行初始化
                            if init_database():
                                st.success("数据库重新初始化成功！")
                                st.rerun()  # 刷新页面
                            else:
                                st.error("数据库初始化失败，请查看日志")
                        else:
                            st.error("数据库备份失败，初始化已取消")
                    except Exception as e:
                        error_msg = f"数据库初始化失败: {str(e)}"
                        st.error(error_msg)
                        add_log("error", error_msg)
        else:
            st.info("数据库文件不存在，需要初始化")
            if st.button("初始化数据库", use_container_width=True):
                try:
                    if init_database():
                        st.success("数据库初始化成功！")
                        st.rerun()  # 刷新页面
                    else:
                        st.error("数据库初始化失败，请查看日志")
                except Exception as e:
                    error_msg = f"数据库初始化失败: {str(e)}"
                    st.error(error_msg)
                    add_log("error", error_msg)
    
    with tab3:
        st.markdown("### 数据库备份")
        if st.button("创建备份", use_container_width=True):
            if backup_database():
                st.success("数据库备份成功")
                st.rerun()
            else:
                st.error("数据库备份失败")
    
    with tab4:
        show_restore_interface()
    
    with tab5:
        show_migrate_interface()
    
    with tab6:
        show_table_info()
    
    with tab7:
        st.markdown("### 数据库升级")
        st.warning("⚠️ 升级前请确保已备份数据库！")
        
        if st.button("开始升级", use_container_width=True):
            with st.spinner("正在升级数据库..."):
                results = upgrade_database()
                
                if results['success']:
                    st.success(results['message'])
                else:
                    st.error(results['message'])
                
                # 显示详细信息
                st.markdown("#### 升级详情")
                for detail in results['details']:
                    st.text(f"• {detail}")