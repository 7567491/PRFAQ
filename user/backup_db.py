import shutil
from datetime import datetime
import os

def backup_database():
    """备份数据库"""
    # 创建备份目录
    backup_dir = 'user/backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{backup_dir}/users_{timestamp}.db'
    
    # 复制数据库文件
    try:
        shutil.copy2('user/users.db', backup_path)
        print(f"数据库已备份到: {backup_path}")
    except Exception as e:
        print(f"备份失败: {str(e)}")

if __name__ == "__main__":
    backup_database() 