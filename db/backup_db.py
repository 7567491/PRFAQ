import shutil
from datetime import datetime
import os
import sqlite3
from user.logger import add_log

def verify_database(db_path: str) -> bool:
    """验证数据库完整性"""
    try:
        if not os.path.exists(db_path):
            add_log("info", "数据库文件不存在，跳过验证")
            return True  # 如果文件不存在，也返回True，因为这是首次初始化的情况
            
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 检查必要的表是否存在
        required_tables = ['users', 'bills', 'history']
        for table in required_tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not c.fetchone():
                add_log("warning", f"数据库中缺少 {table} 表")
                return False
        
        conn.close()
        return True
    except Exception as e:
        add_log("error", f"验证数据库时出错: {str(e)}")
        return False

def backup_database() -> bool:
    """备份数据库"""
    try:
        # 创建备份目录
        backup_dir = 'db/backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 检查源数据库是否存在
        if not os.path.exists('db/users.db'):
            add_log("info", "数据库文件不存在，跳过备份")
            return True
        
        # 生成备份文件名并复制
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'{backup_dir}/users_{timestamp}.db'
        shutil.copy2('db/users.db', backup_path)
        
        add_log("info", f"数据库已备份: {backup_path}")
        return True
        
    except Exception as e:
        add_log("error", f"备份失败: {str(e)}")
        return False

if __name__ == "__main__":
    backup_database() 