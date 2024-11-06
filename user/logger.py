import streamlit as st
from datetime import datetime

def add_log(level: str, message: str):
    """添加日志"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    log_entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    }
    
    st.session_state.logs.append(log_entry)
    
    # Keep only latest 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

def display_logs():
    """显示日志"""
    st.markdown("### 系统日志")
    for log in st.session_state.logs:
        color = "#000000"  # 默认黑色
        if log['level'] == 'info':
            color = "#0000FF"  # 蓝色
        elif log['level'] == 'error':
            color = "#FF0000"  # 红色
        elif log['level'] == 'warning':
            color = "#FFA500"  # 橙色
        
        st.markdown(f'<span style="color: {color};">[{log["timestamp"]}] {log["message"]}</span>', 
                   unsafe_allow_html=True) 