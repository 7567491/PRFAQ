import os
import shutil
from datetime import datetime
import streamlit as st
from user.logger import add_log

def list_backups():
    """列出所有备份文件"""
    backup_dir = 'db/backups'
    if not os.path.exists(backup_dir):
        return []
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    return sorted(backups, reverse=True)  # 最新的备份在前

def restore_database(backup_name: str) -> bool:
    """从备份文件恢复数据库"""
    try:
        # 构建文件路径
        backup_path = os.path.join('db/backups', backup_name)
        current_db_path = 'db/users.db'
        
        # 如果当前数据库存在，先创建一个临时备份
        if os.path.exists(current_db_path):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_backup_path = os.path.join('db/backups', f'pre_restore_{timestamp}.db')
            shutil.copy2(current_db_path, temp_backup_path)
            add_log("info", f"创建恢复前的临时备份: {temp_backup_path}")
        
        # 复制备份文件到当前数据库
        shutil.copy2(backup_path, current_db_path)
        add_log("info", f"从备份 {backup_name} 恢复数据库成功")
        return True
        
    except Exception as e:
        error_msg = f"恢复数据库失败: {str(e)}"
        add_log("error", error_msg)
        return False

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库恢复")
    
    # 获取备份列表
    backups = list_backups()
    
    if not backups:
        st.info("没有找到可用的备份文件")
        return
    
    # 显示备份文件选择器
    selected_backup = st.selectbox(
        "选择要恢复的备份文件",
        backups,
        format_func=lambda x: f"{x.replace('users_', '').replace('.db', '')} 的备份"
    )
    
    # 显示警告信息
    st.warning("⚠️ 恢复数据库将覆盖当前的数据，请确保您知道自己在做什么！")
    
    # 添加确认步骤
    confirm = st.checkbox("我已了解恢复操作的风险，并已做好相应准备")
    
    if confirm:
        if st.button("开始恢复", use_container_width=True):
            # 执行恢复操作
            if restore_database(selected_backup):
                st.success(f"数据库已成功恢复到 {selected_backup}")
                st.info("请重启应用以应用更改")
            else:
                st.error("恢复操作失败，请查看日志了解详情") 