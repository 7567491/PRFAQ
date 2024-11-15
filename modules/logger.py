import streamlit as st
from datetime import datetime
import traceback

def add_log(level: str, message: str, include_trace=False):
    """Add a log entry to the session state logs with optional stack trace."""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    
    if include_trace and level == 'error':
        log_entry['trace'] = traceback.format_exc()
    
    st.session_state.logs.append(log_entry)
    
    # 打印到控制台以便调试
    print(f"[{timestamp}] {level.upper()}: {message}")
    if include_trace and level == 'error':
        print(traceback.format_exc()) 