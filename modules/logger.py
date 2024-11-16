import streamlit as st
from datetime import datetime
import traceback

def add_log(level: str, message: str, include_trace: bool = False):
    """Add a log entry to the session state logs.
    
    Args:
        level: Log level ('info', 'warning', 'error', etc.)
        message: Log message
        include_trace: Whether to include stack trace for errors (default: False)
    """
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    
    # 如果是错误且需要堆栈跟踪
    if include_trace and level == 'error':
        log_entry['trace'] = traceback.format_exc()
        # 同时打印到控制台以便调试
        print(f"[{timestamp}] {level.upper()}: {message}")
        print(traceback.format_exc())
    else:
        # 普通日志只打印消息
        print(f"[{timestamp}] {level.upper()}: {message}")
    
    st.session_state.logs.append(log_entry)
    
    # 打印到控制台以便调试
    print(f"[{timestamp}] {level.upper()}: {message}")
    if include_trace and level == 'error':
        print(traceback.format_exc()) 