from datetime import datetime

def add_log(message: str, st_session):
    """添加系统日志"""
    if 'system_logs' not in st_session:
        st_session.system_logs = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    st_session.system_logs.append(f"[{timestamp}] {message}")
    # 保持最新的20条日志
    if len(st_session.system_logs) > 20:
        st_session.system_logs.pop(0) 