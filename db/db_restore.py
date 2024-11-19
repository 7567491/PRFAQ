import streamlit as st
import json
from pathlib import Path
import shutil
from datetime import datetime
import humanize
from modules.logger import add_log
import sqlite3
import boto3
import os
from botocore.exceptions import ClientError
import pytz

class DatabaseBackup:
    def __init__(self):
        self.s3_bucket = 'prfaq'
        self.s3_prefix = 'backup/'
        self.backup_dir = Path("db/backup")
        self.db_file = Path('db/users.db')
        
        # 确保本地备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化S3客户端
        self.s3 = boto3.client('s3')
        
    def _get_db_stats(self):
        """获取数据库统计信息"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            stats = {}
            for table in ['users', 'bills', 'history']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            
            conn.close()
            return stats
        except Exception as e:
            add_log("error", f"获取数据库统计信息失败: {str(e)}")
            return {'users': 0, 'bills': 0, 'history': 0}

    def backup_database(self, reason: str = "manual", operator: str = "system") -> bool:
        """备份数据库到本地和S3"""
        try:
            # 获取北京时间作为备份文件名
            tz = pytz.timezone('Asia/Shanghai')
            timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
            backup_file = f"users_{timestamp}_{reason}.db"
            local_backup_path = self.backup_dir / backup_file
            
            # 复制数据库文件到本地
            shutil.copy2(self.db_file, local_backup_path)
            
            # 上传到S3
            s3_key = f"{self.s3_prefix}{backup_file}"
            self.s3.upload_file(
                str(local_backup_path),
                self.s3_bucket,
                s3_key
            )
            
            # 获取数据库统计信息
            stats = self._get_db_stats()
            
            # 创建备份记录
            backup_record = {
                'datetime': datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S'),
                'filename': backup_file,
                'reason': reason,
                'operator': operator,
                'file_size': os.path.getsize(local_backup_path),
                'user_count': stats.get('users', 0),
                'bill_count': stats.get('bills', 0),
                'history_count': stats.get('history', 0),
                's3_path': f"s3://{self.s3_bucket}/{s3_key}"
            }
            
            # 更新备份记录文件
            self._update_backup_records(backup_record)
            
            add_log("info", f"数据库已备份到S3: {backup_file}")
            return True
            
        except Exception as e:
            add_log("error", f"数据库备份失败: {str(e)}")
            return False

    def restore_database(self, backup_file: str) -> bool:
        """从S3恢复数据库"""
        try:
            # 先备份当前数据库
            self.backup_database(
                reason="restore_backup",
                operator=st.session_state.get('user', 'system')
            )
            
            # 从S3下载备份文件
            local_backup_path = self.backup_dir / backup_file
            s3_key = f"{self.s3_prefix}{backup_file}"
            
            try:
                self.s3.download_file(
                    self.s3_bucket,
                    s3_key,
                    str(local_backup_path)
                )
            except ClientError as e:
                error_msg = f"从S3下载备份失败: {str(e)}"
                add_log("error", error_msg)
                return False
            
            # 强制关闭所有数据库连接
            import gc
            gc.collect()  # 强制垃圾回收
            
            # 关闭所有可能的数据库连接
            try:
                import sqlite3
                for obj in gc.get_objects():
                    if isinstance(obj, sqlite3.Connection):
                        try:
                            obj.close()
                        except:
                            pass
            except:
                pass
            
            # 等待文件系统释放
            import time
            time.sleep(1)
            
            # 尝试删除现有数据库文件
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    if self.db_file.exists():
                        os.remove(self.db_file)
                        add_log("info", f"已删除现有数据库文件 (尝试 {attempt + 1})")
                        break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        error_msg = f"删除现有数据库文件失败: {str(e)}"
                        add_log("error", error_msg)
                        return False
                    time.sleep(1)  # 等待一秒后重试
            
            # 复制新的数据库文件
            try:
                shutil.copy2(local_backup_path, self.db_file)
                add_log("info", f"数据库已从S3恢复: {backup_file}")
                
                # 验证新数据库是否可用
                try:
                    test_conn = sqlite3.connect(self.db_file)
                    test_conn.execute("SELECT 1")
                    test_conn.close()
                    add_log("info", "新数据库文件验证成功")
                    
                    # 清除 Streamlit 会话状态
                    for key in list(st.session_state.keys()):
                        if key not in ['user', 'authenticated', 'user_role']:
                            del st.session_state[key]
                    
                    return True
                    
                except Exception as e:
                    error_msg = f"新数据库文件验证失败: {str(e)}"
                    add_log("error", error_msg)
                    return False
                
            except Exception as e:
                error_msg = f"复制新数据库文件失败: {str(e)}"
                add_log("error", error_msg)
                return False
            
        except Exception as e:
            add_log("error", f"数据库恢复失败: {str(e)}")
            return False

    def list_backups(self):
        """获取S3上的备份列表"""
        try:
            response = self.s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.s3_prefix
            )
            
            backups = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.db'):
                        filename = obj['Key'].split('/')[-1]
                        backups.append({
                            'filename': filename,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            's3_path': f"s3://{self.s3_bucket}/{obj['Key']}"
                        })
            
            return backups
            
        except Exception as e:
            add_log("error", f"获取S3备份列表失败: {str(e)}")
            return []

    def _update_backup_records(self, backup_record):
        """更新备份记录文件"""
        try:
            backup_json = self.backup_dir / "db.json"
            backups = []
            
            if backup_json.exists():
                with open(backup_json, 'r', encoding='utf-8') as f:
                    backups = json.load(f)
            
            backups.append(backup_record)
            
            with open(backup_json, 'w', encoding='utf-8') as f:
                json.dump(backups, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            add_log("error", f"更新备份记录失败: {str(e)}")

def show_restore_interface():
    """显示数据库恢复界面"""
    st.markdown("### 数据库管理")
    
    db_backup = DatabaseBackup()
    
    # 创建备份按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📦 创建备份", use_container_width=True):
            if db_backup.backup_database(
                reason="manual",
                operator=st.session_state.get('user', 'system')
            ):
                st.success("数据库已备份到S3！")
                st.rerun()
            else:
                st.error("数据库备份失败，请查看日志")
    
    st.markdown("---")
    st.markdown("### S3备份列表")
    
    # 获取S3备份列表
    backups = db_backup.list_backups()
    
    if not backups:
        st.warning("S3中没有可用的备份")
        return
        
    # 显示备份列表
    backup_data = []
    for backup in backups:
        # 解析文件名中的信息
        filename = backup['filename']
        parts = filename.split('_')
        reason = parts[2].replace('.db', '') if len(parts) > 2 else 'unknown'
        
        # 转换为人类可读格式
        file_size = humanize.naturalsize(backup['size'])
        relative_time = humanize.naturaltime(datetime.now(pytz.UTC) - backup['last_modified'].replace(tzinfo=pytz.UTC))
        
        backup_data.append({
            '备份时间': backup['last_modified'].strftime('%Y-%m-%d %H:%M:%S'),
            '相对时间': relative_time,
            '备份原因': reason,
            '文件大小': file_size,
            'S3路径': backup['s3_path'],
            '文件名': filename
        })
    
    st.dataframe(
        backup_data,
        hide_index=True,
        use_container_width=True
    )
    
    # 选择要恢复的备份
    st.markdown("### 恢复备份")
    selected_backup = st.selectbox(
        "选择要恢复的备份：",
        options=[b['filename'] for b in backups],
        format_func=lambda x: f"{[b for b in backups if b['filename'] == x][0]['last_modified'].strftime('%Y-%m-%d %H:%M:%S')} - {x}"
    )
    
    if st.button("🔄 恢复选中的备份", use_container_width=True, type="primary"):
        confirm = st.warning("⚠️ 确定要恢复此备份吗？这将覆盖当前的数据库！")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 确认恢复", use_container_width=True):
                success = db_backup.restore_database(selected_backup)
                if success:
                    st.success("数据库已从S3恢复！系统将在3秒后自动重启...")
                    
                    # 创建重启标记文件
                    with open("restart.flag", "w") as f:
                        f.write("1")
                    
                    # 使用 JavaScript 强制刷新页面
                    st.markdown(
                        """
                        <script>
                            setTimeout(function() {
                                window.location.href = window.location.href.split('?')[0];
                            }, 3000);
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.error("数据库恢复失败，请查看日志")
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.rerun()

# 在文件末尾添加兼容函数
def restore_database(backup_file: str) -> bool:
    """
    兼容性函数，用于支持旧的调用方式
    """
    db_backup = DatabaseBackup()
    return db_backup.restore_database(backup_file)

def backup_database(reason: str = "manual", operator: str = "system") -> bool:
    """
    兼容性函数，用于支持旧的调用方式
    """
    db_backup = DatabaseBackup()
    return db_backup.backup_database(reason, operator)

# 更新导出列表
__all__ = ['DatabaseBackup', 'show_restore_interface', 'restore_database', 'backup_database'] 