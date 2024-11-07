import streamlit as st
import os
import shutil
from datetime import datetime
import sqlite3
from user.logger import add_log

def get_backup_files():
    """获取所有备份文件"""
    backup_dir = 'db/backups'
    if not os.path.exists(backup_dir):
        return []
    return sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')], reverse=True)

def restore_database(backup_file: str):
    """从备份文件恢复数据库"""
    try:
        # 备份当前数据库
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = 'db/backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 从备份恢复
        backup_path = os.path.join(backup_dir, backup_file)
        shutil.copy2(backup_path, 'db/users.db')
        
        add_log("info", f"数据库已从备份恢复: {backup_file}")
        return True, "数据库恢复成功"
    except Exception as e:
        error_msg = f"数据库恢复失败: {str(e)}"
        add_log("error", error_msg)
        return False, error_msg

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库恢复")
    
    backup_files = get_backup_files()
    if not backup_files:
        st.info("没有找到备份文件")
        return
    
    selected_backup = st.selectbox(
        "选择要恢复的备份文件",
        backup_files
    )
    
    if st.button("恢复选中的备份", use_container_width=True):
        confirm = st.checkbox("确认要恢复数据库吗？这将覆盖当前的数据库")
        if confirm:
            success, message = restore_database(selected_backup)
            if success:
                st.success(message)
            else:
                st.error(message) 