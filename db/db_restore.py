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
        backup_file = f"users_{timestamp}_{reason}.db"
        backup_path = backup_root / backup_file
        
        # 确保源数据库文件存在
        source_db = Path('db/users.db')
        if not source_db.exists():
            add_log("error", "源数据库文件不存在")
            return False
            
        # 复制数据库文件
        try:
            shutil.copy2(source_db, backup_path)
            add_log("info", f"数据库文件已复制到: {backup_path}")
        except Exception as e:
            add_log("error", f"复制数据库文件失败: {str(e)}")
            return False
        
        # 获取数据库统计信息
        try:
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            # 获取各表的记录数
            stats = {}
            for table in ['users', 'bills', 'history']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            add_log("error", f"获取数据库统计信息失败: {str(e)}")
            stats = {'users': 0, 'bills': 0, 'history': 0}
        
        # 获取文件大小
        file_size = backup_path.stat().st_size
        
        # 更新备份记录
        backup_json = backup_root / "db.json"
        backups = []
        if backup_json.exists():
            try:
                with open(backup_json, 'r', encoding='utf-8') as f:
                    backups = json.load(f)
            except Exception as e:
                add_log("error", f"读取备份记录失败: {str(e)}")
                backups = []
        
        # 添加新的备份记录
        backup_record = {
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'filename': backup_file,
            'path': str(backup_path),
            'reason': reason,
            'operator': operator,
            'file_size': file_size,
            'user_count': stats.get('users', 0),
            'bill_count': stats.get('bills', 0),
            'history_count': stats.get('history', 0)
        }
        
        backups.append(backup_record)
        
        # 保存备份记录
        try:
            with open(backup_json, 'w', encoding='utf-8') as f:
                json.dump(backups, f, ensure_ascii=False, indent=2)
        except Exception as e:
            add_log("error", f"保存备份记录失败: {str(e)}")
            # 即使保存记录失败，备份本身是成功的
        
        add_log("info", f"数据库备份成功: {backup_file}")
        return True
        
    except Exception as e:
        add_log("error", f"数据库备份失败: {str(e)}")
        return False

def restore_database(backup_file: str) -> bool:
    """从备份文件恢复数据库"""
    try:
        # 验证备份文件
        backup_root = Path("db/backup")
        backup_path = backup_root / backup_file
        
        if not backup_path.exists():
            error_msg = f"备份文件不存在: {backup_file}"
            add_log("error", error_msg)
            st.error(error_msg)
            return False
            
        # 确保数据库���件存在
        db_file = Path('db/users.db')
        if not db_file.exists():
            add_log("error", "当前数据库文件不存在")
            return False
            
        # 先备份当前数据库
        backup_result = backup_database(
            reason="restore_backup",
            operator=st.session_state.get('user', 'system')
        )
        
        if not backup_result:
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
        add_log("error", error_msg, include_trace=True)
        st.error(error_msg)
        return False

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库管理")
    
    # 添加创建备份的按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📦 创建备份", use_container_width=True):
            if backup_database(
                reason="manual",
                operator=st.session_state.get('user', 'system')
            ):
                st.success("数据库备份成功！")
                st.rerun()  # 刷新界面以显示新的备份
            else:
                st.error("数据库备份失败，请查看日志")
    
    st.markdown("---")
    st.markdown("### 可用备份")
    
    # 读取备份记录
    backup_root = Path("db/backup")
    backup_json = backup_root / "db.json"
    
    if not backup_json.exists():
        st.warning("未找到备份记录")
        return
        
    try:
        with open(backup_json, 'r', encoding='utf-8') as f:
            backups = json.load(f)
            
        # 验证备份文件是否实际存在
        valid_backups = []
        for backup in backups:
            backup_path = backup_root / backup['filename']
            if backup_path.exists():
                valid_backups.append(backup)
            else:
                add_log("warning", f"备份记录中的文件不存在: {backup['filename']}")
        
        if not valid_backups:
            st.warning("没有可用的备份文件")
            return
            
        # 使用实际存在的备份创建显示数据
        backup_data = []
        for backup in valid_backups:
            # 转换文件大小为人类可读格式
            file_size = humanize.naturalsize(backup['file_size'])
            
            # 转换时间为相对时间
            dt = datetime.strptime(backup['datetime'], '%Y-%m-%d %H:%M:%S')
            relative_time = humanize.naturaltime(datetime.now() - dt)
            
            # 获取备份原因的显示文本
            reason_text = {
                'manual': '手动备份',
                'auto': '自动备份',
                'upgrade': '升级备份',
                'restore_backup': '恢复前备份'
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
        st.markdown("### 恢复备份")
        selected_backup = st.selectbox(
            "选择要恢复的备份：",
            options=[b['filename'] for b in valid_backups],
            format_func=lambda x: f"{[b for b in valid_backups if b['filename'] == x][0]['datetime']} - "
                                f"{[b for b in valid_backups if b['filename'] == x][0]['reason']} - "
                                f"用户数: {[b for b in valid_backups if b['filename'] == x][0]['user_count']}"
        )
        
        # 添加确认对话框
        if st.button("🔄 恢复选中的备份", use_container_width=True, type="primary"):
            confirm = st.warning("⚠️ 确定要恢复此备份吗？这将覆盖当前的数据库！")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 确认恢复", use_container_width=True):
                    # 再次验证文件存在
                    backup_path = backup_root / selected_backup
                    if not backup_path.exists():
                        st.error(f"备份文件不存在: {selected_backup}")
                        add_log("error", f"备份文件不存在: {selected_backup}")
                        return
                        
                    if restore_database(selected_backup):
                        st.success("数据库恢复成功！")
                        st.rerun()
                    else:
                        st.error("数据库恢复失败，请查看日志")
            with col2:
                if st.button("❌ 取消", use_container_width=True):
                    st.rerun()
                
    except Exception as e:
        error_msg = f"显示恢复界面时出错: {str(e)}"
        st.error(error_msg)
        add_log("error", error_msg, include_trace=True)

# 导出需要的函数
__all__ = ['restore_database', 'backup_database', 'show_restore_interface'] 