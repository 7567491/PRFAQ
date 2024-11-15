import streamlit as st
import json
from pathlib import Path
import shutil
from datetime import datetime
import humanize
from modules.utils import add_log

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库恢复")
    
    # 读取备份记录
    backup_root = Path("db/backup")
    backup_json = backup_root / "db.json"
    
    if not backup_json.exists():
        st.warning("未找到备份记录")
        return
        
    try:
        with open(backup_json, 'r', encoding='utf-8') as f:
            backups = json.load(f)
    except Exception as e:
        st.error(f"读取备份记录失败: {str(e)}")
        return
    
    # 显示备份列表
    st.markdown("#### 可用备份")
    
    # 创建备份信息表格
    backup_data = []
    for backup in backups:
        # 转换文件大小为人类可读格式
        file_size = humanize.naturalsize(backup['file_size'])
        
        # 转换时间为相对时间
        dt = datetime.strptime(backup['datetime'], '%Y-%m-%d %H:%M:%S')
        relative_time = humanize.naturaltime(datetime.now() - dt)
        
        # 获取备份原因的显示文本
        reason_text = {
            'manual': '手动备份',
            'auto': '自动备份',
            'upgrade': '升级备份'
        }.get(backup['reason'], backup['reason'])
        
        backup_data.append({
            '备份时间': backup['datetime'],
            '相对时间': relative_time,
            '备份原因': reason_text,
            '操作者': backup['operator'],
            '用户数': backup['user_count'],
            '账单数': backup['bill_count'],
            '历史记录数': backup['history_count'],
            '文件大小': file_size,
            '文件名': backup['filename']
        })
    
    # 显示备份列表
    st.dataframe(
        backup_data,
        column_config={
            '备份时间': st.column_config.TextColumn('备份时间', width='medium'),
            '相对时间': st.column_config.TextColumn('距今', width='small'),
            '备份原因': st.column_config.TextColumn('原因', width='small'),
            '操作者': st.column_config.TextColumn('操作者', width='small'),
            '用户数': st.column_config.NumberColumn('用户数', width='small'),
            '账单数': st.column_config.NumberColumn('账单数', width='small'),
            '历史记录数': st.column_config.NumberColumn('历史记录', width='small'),
            '文件大小': st.column_config.TextColumn('大小', width='small'),
            '文件名': st.column_config.TextColumn('文件名', width='large')
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 选择要恢复的备份
    selected_backup = st.selectbox(
        "选择要恢复的备份：",
        options=[b['filename'] for b in backups],
        format_func=lambda x: f"{[b for b in backups if b['filename'] == x][0]['datetime']} - "
                            f"{[b for b in backups if b['filename'] == x][0]['reason']} - "
                            f"用户数: {[b for b in backups if b['filename'] == x][0]['user_count']}"
    )
    
    if st.button("恢复选中的备份", use_container_width=True):
        try:
            # 先备份当前数据库
            if backup_database(reason="restore_backup", operator=st.session_state.user):
                # 获取选中的备份文件路径
                backup_path = [b['path'] for b in backups if b['filename'] == selected_backup][0]
                
                # 恢复数据库
                shutil.copy2(backup_path, 'db/users.db')
                st.success("数据库恢复成功！")
                add_log("info", f"从备份 {selected_backup} 恢复数据库成功")
                
                # 刷新页面
                st.rerun()
            else:
                st.error("备份当前数据库失败，恢复操作已取消")
        except Exception as e:
            st.error(f"恢复数据库失败: {str(e)}")
            add_log("error", f"恢复数据库失败: {str(e)}") 