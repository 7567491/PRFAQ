import streamlit as st
import sqlite3
from datetime import datetime
from user.user_process import UserManager
from user.logger import add_log

def show_user_history():
    """显示用户历史记录"""
    st.title("历史记录查看")
    
    # 获取当前用户信息
    user_mgr = UserManager()
    user_info = user_mgr.get_user_info(st.session_state.user)
    
    if not user_info:
        st.error("获取用户信息失败")
        return
    
    # 连接数据库
    conn = user_mgr.get_db_connection()
    c = conn.cursor()
    
    try:
        # 获取用户的历史记录
        c.execute('''
            SELECT timestamp, type, content
            FROM history
            WHERE user_id = ?
            ORDER BY timestamp DESC
        ''', (user_info['user_id'],))
        
        records = c.fetchall()
        
        if not records:
            st.info("暂无历史记录")
            return
        
        # 按类型分组显示历史记录
        record_types = set(record[1] for record in records)
        
        # 创建类型过滤器
        selected_type = st.selectbox(
            "选择记录类型",
            ["全部"] + list(record_types)
        )
        
        # 显示历史记录
        for record in records:
            timestamp, type_, content = record
            
            # 根据选择的类型过滤
            if selected_type != "全部" and type_ != selected_type:
                continue
            
            with st.expander(f"{type_} - {timestamp}"):
                st.markdown(content)
                
                # 添加复制按钮
                if st.button("复制内容", key=f"copy_{timestamp}"):
                    st.write("内容已复制到剪贴板")
                    st.session_state['clipboard'] = content
        
    except Exception as e:
        st.error(f"读取历史记录失败: {str(e)}")
        add_log("error", f"读取历史记录失败: {str(e)}")
    finally:
        conn.close() 