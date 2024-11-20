import streamlit as st
from pathlib import Path
import shutil
from datetime import datetime
import humanize
from user.logger import add_log
import sqlite3
import re
from typing import Dict, List, Optional
from functools import lru_cache
import time

def create_backup(reason: str = "manual", operator: str = "system") -> bool:
    """创建数据库备份"""
    try:
        # 创建备份目录
        backup_root = Path("db/backup")
        backup_root.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"users_{timestamp}_{reason}.db"
        backup_path = backup_root / backup_file
        
        # 确保源数据库文件存在并复制
        source_db = Path('db/users.db')
        if not source_db.exists():
            add_log("error", "源数据库文件不存在")
            return False
            
        shutil.copy2(source_db, backup_path)
        add_log("info", f"数据库备份成功: {backup_file}")
        return True
            
    except Exception as e:
        add_log("error", f"创建数据库备份失败: {str(e)}")
        return False

@lru_cache(maxsize=32)
def get_db_stats(db_path: str, cache_time: float) -> Optional[Dict]:
    """获取数据库统计信息（带缓存）"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        stats = {}
        for table in ['users', 'bills', 'history']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                stats[table] = 0
                
        return stats
    except Exception as e:
        add_log("error", f"获取数据库统计失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_backup_files() -> List[Dict]:
    """获取所有备份文件信息"""
    backup_root = Path("db/backup")
    if not backup_root.exists():
        return []
        
    backup_files = []
    file_pattern = re.compile(r'users_(\d{8}_\d{6})_(\w+)\.db')
    
    # 获取当前时间戳用于缓存
    cache_timestamp = time.time()
    
    for file_path in backup_root.glob("*.db"):
        try:
            match = file_pattern.match(file_path.name)
            if not match:
                continue
                
            timestamp_str, reason = match.groups()
            
            # 解析备份时间
            backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            
            # 获取文件信息
            file_stat = file_path.stat()
            file_size = file_stat.st_size
            
            # 获取数据库统计信息（使用缓存）
            stats = get_db_stats(str(file_path), cache_timestamp)
            
            # 转换原因代码为显示文本
            reason_text = {
                'manual': '手动备份',
                'auto': '自动备份',
                'restore_backup': '恢复前备份'
            }.get(reason, reason)
            
            backup_files.append({
                'filename': file_path.name,
                'datetime': backup_time.strftime('%Y-%m-%d %H:%M:%S'),
                'relative_time': humanize.naturaltime(datetime.now() - backup_time),
                'reason': reason_text,
                'file_size': humanize.naturalsize(file_size),
                'raw_size': file_size,
                'user_count': stats.get('users', 0) if stats else 0,
                'bill_count': stats.get('bills', 0) if stats else 0,
                'history_count': stats.get('history', 0) if stats else 0
            })
            
        except Exception as e:
            add_log("error", f"处理备份文件 {file_path.name} 失败: {str(e)}")
            continue
    
    # 按时间倒序排序
    return sorted(backup_files, key=lambda x: x['datetime'], reverse=True)

def restore_database(backup_file: str) -> bool:
    """从备份文件恢复数据库"""
    try:
        backup_root = Path("db/backup")
        backup_path = backup_root / backup_file
        
        if not backup_path.exists():
            error_msg = f"备份文件不存在: {backup_file}"
            add_log("error", error_msg)
            st.error(error_msg)
            return False
            
        # 确保当前数据库文件存在
        db_file = Path('db/users.db')
        if not db_file.exists():
            add_log("error", "当前数据库文件不存在")
            return False
            
        # 先创建恢复前备份
        if not create_backup(reason="restore_backup", operator=st.session_state.get('user', 'system')):
            error_msg = "恢复前备份失败"
            add_log("error", error_msg)
            st.error(error_msg)
            return False
            
        # 恢复数据库
        try:
            shutil.copy2(backup_path, db_file)
            success_msg = f"数据库已从备份 {backup_file} 恢复"
            add_log("info", success_msg)
            st.success(success_msg)
            return True
        except Exception as e:
            error_msg = f"复制备份文件失败: {str(e)}"
            add_log("error", error_msg)
            st.error(error_msg)
            return False
        
    except Exception as e:
        error_msg = f"数据库恢复失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)
        return False

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库管理")
    
    # 添加创建备份的按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📦 创建备份", use_container_width=True):
            if create_backup(
                reason="manual",
                operator=st.session_state.get('user', 'system')
            ):
                st.success("数据库备份成功！")
                st.rerun()
            else:
                st.error("数据库备份失败，请查看日志")
    
    # 获取备份文件列表（直接使用文件系统扫描结果）
    backups = get_backup_files()
    
    if not backups:
        st.warning("未找到可用的备份文件")
        return
        
    st.markdown("---")
    st.markdown("### 可用备份")
    
    # 显示备份列表
    backup_data = [{
        '备份时间': b['datetime'],
        '距今': b['relative_time'],
        '备份原因': b['reason'],
        '用户数': b['user_count'],
        '账单数': b['bill_count'],
        '历史记录数': b['history_count'],
        '文件大小': b['file_size'],
        '文件名': b['filename']
    } for b in backups]
    
    st.dataframe(
        backup_data,
        column_config={
            '备份时间': st.column_config.TextColumn('备份时间', width='medium'),
            '距今': st.column_config.TextColumn('距今', width='small'),
            '备份原因': st.column_config.TextColumn('原因', width='small'),
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
    st.markdown("### 恢复备份")
    selected_backup = st.selectbox(
        "选择要恢复的备份：",
        options=[b['filename'] for b in backups],
        format_func=lambda x: f"{[b for b in backups if b['filename'] == x][0]['datetime']} - "
                            f"{[b for b in backups if b['filename'] == x][0]['reason']} - "
                            f"用户数: {[b for b in backups if b['filename'] == x][0]['user_count']}"
    )
    
    # 添加确认对话框
    if st.button("🔄 恢复选中的备份", use_container_width=True, type="primary"):
        confirm = st.warning("⚠️ 确定要恢复此备份吗？这将覆盖当前的数据库！")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认恢复", use_container_width=True):
                if restore_database(selected_backup):
                    st.success("数据库恢复成功！")
                    st.rerun()
                else:
                    st.error("数据库恢复失败，请查看日志")
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.rerun()

# 导出需要的函数
__all__ = ['restore_database', 'create_backup', 'show_restore_interface'] 