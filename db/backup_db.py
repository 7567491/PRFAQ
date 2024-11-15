"""数据库备份模块"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3

def get_backup_info(db_path: str) -> dict:
    """获取数据库信息
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        包含用户数等信息的字典
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取用户数
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # 获取其他统计信息
        cursor.execute("SELECT COUNT(*) FROM bills")
        bill_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history")
        history_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "user_count": user_count,
            "bill_count": bill_count,
            "history_count": history_count
        }
    except Exception as e:
        return {
            "user_count": 0,
            "bill_count": 0,
            "history_count": 0,
            "error": str(e)
        }

def backup_database(reason: str = "manual", operator: str = "system") -> bool:
    """备份数据库
    
    Args:
        reason: 备份原因 (manual/auto/upgrade)
        operator: 操作者
        
    Returns:
        是否成功
    """
    try:
        # 确保备份目录存在
        backup_root = Path("db/backup")
        backup_root.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (backup_root / "auto").mkdir(exist_ok=True)
        (backup_root / "manual").mkdir(exist_ok=True)
        (backup_root / "upgrade").mkdir(exist_ok=True)
        
        # 确定备份文件名和路径
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{timestamp}_{reason}.db"
        backup_dir = backup_root / reason
        backup_path = backup_dir / backup_name
        
        # 复制数据库文件
        shutil.copy2('db/users.db', backup_path)
        
        # 获取数据库信息
        db_info = get_backup_info(str(backup_path))
        
        # 更新备份记录
        backup_json = backup_root / "db.json"
        if backup_json.exists():
            with open(backup_json, 'r', encoding='utf-8') as f:
                backups = json.load(f)
        else:
            backups = []
            
        # 添加新的备份记录
        backups.append({
            "filename": backup_name,
            "path": str(backup_path),
            "timestamp": timestamp,
            "datetime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "reason": reason,
            "operator": operator,
            "user_count": db_info["user_count"],
            "bill_count": db_info["bill_count"],
            "history_count": db_info["history_count"],
            "file_size": os.path.getsize(backup_path)
        })
        
        # 保存备份记录
        with open(backup_json, 'w', encoding='utf-8') as f:
            json.dump(backups, f, ensure_ascii=False, indent=2)
            
        return True
        
    except Exception as e:
        print(f"备份失败: {str(e)}")
        return False 