import schedule
import time
from datetime import datetime
from db.backup_db import backup_database
from modules.utils import add_log

def auto_backup():
    """执行自动备份"""
    try:
        if backup_database(reason="auto"):
            add_log("info", "自动备份成功")
        else:
            add_log("error", "自动备份失败")
    except Exception as e:
        add_log("error", f"自动备份出错: {str(e)}")

def start_scheduler():
    """启动调度器"""
    # 每小时整点执行备份
    schedule.every().hour.at(":00").do(auto_backup)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次 