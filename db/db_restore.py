import streamlit as st
import json
from pathlib import Path
import shutil
from datetime import datetime
import humanize
from modules.logger import add_log
import sqlite3

def backup_database(reason: str = "manual", operator: str = "system") -> bool:
    """备份数据库"""
    try:
        # 创建备份目录
        backup_root = Path("db/backup")
        backup_root.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"users_{timestamp}.db"
        backup_path = backup_root / backup_file
        
        # 复制数据库文件
        shutil.copy2('db/users.db', backup_path)
        
        # 获取数据库统计信息
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 获取用户数
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # 获取账单数
        cursor.execute("SELECT COUNT(*) FROM bills")
        bill_count = cursor.fetchone()[0]
        
        # 获取历史记录数
        cursor.execute("SELECT COUNT(*) FROM history")
        history_count = cursor.fetchone()[0]
        
        conn.close()
        
        # 获取文件大小
        file_size = backup_path.stat().st_size
        
        # 更新备份记录
        backup_json = backup_root / "db.json"
        backups = []
        if backup_json.exists():
            with open(backup_json, 'r', encoding='utf-8') as f:
                backups = json.load(f)
        
        # 添加新的备份记录
        backups.append({
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': backup_file,
            'path': str(backup_path),
            'reason': reason,
            'operator': operator,
            'file_size': file_size,
            'user_count': user_count,
            'bill_count': bill_count,
            'history_count': history_count
        })
        
        # 保存备份记录
        with open(backup_json, 'w', encoding='utf-8') as f:
            json.dump(backups, f, ensure_ascii=False, indent=2)
        
        add_log("info", f"数据库备份成功: {backup_file}")
        return True
        
    except Exception as e:
        add_log("error", f"数据库备份失败: {str(e)}")
        return False

def restore_database(backup_file: str) -> bool:
    """从备份文件恢复数据库"""
    try:
        # 验证备份文件
        backup_path = Path("db/backup") / backup_file
        if not backup_path.exists():
            add_log("error", f"备份文件不存在: {backup_file}")
            return False
            
        # 先备份当前数据库
        if not backup_database(reason="restore_backup", operator=st.session_state.get('user', 'system')):
            add_log("error", "恢复前备份失败")
            return False
            
        # 恢复数据库
        shutil.copy2(backup_path, 'db/users.db')
        add_log("info", f"数据库已从备份 {backup_file} 恢复")
        return True
        
    except Exception as e:
        add_log("error", f"数据库恢复失败: {str(e)}")
        return False

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
        if restore_database(selected_backup):
            st.success("数据库恢复成功！")
            st.rerun()
        else:
            st.error("数据库恢复失败，请查看日志")

# 导出需要的函数
__all__ = ['restore_database', 'backup_database', 'show_restore_interface'] 