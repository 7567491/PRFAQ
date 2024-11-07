import schedule
import time
from datetime import datetime
import sqlite3
import logging
import os

logging.basicConfig(
    filename='db/scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def reset_daily_usage():
    """每日重置用户字符使用量"""
    try:
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        
        # 重置所有用户的每日使用量
        c.execute('''
            UPDATE users 
            SET used_chars_today = 0 
            WHERE used_chars_today > 0
        ''')
        
        updated_count = c.rowcount
        conn.commit()
        conn.close()
        
        logging.info(f"已重置 {updated_count} 个用户的每日使用量")
        return True
    except Exception as e:
        logging.error(f"重置每日使用量时出错: {str(e)}")
        return False

def run_scheduler():
    """运行定时任务"""
    # 设置每天凌晨重置
    schedule.every().day.at("00:00").do(reset_daily_usage)
    
    logging.info("定时任务启动")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logging.error(f"定时任务执行出错: {str(e)}")
            time.sleep(60)  # 出错后等待一分钟再继续

if __name__ == "__main__":
    # 确保日志目录存在
    if not os.path.exists('db'):
        os.makedirs('db')
    
    logging.info("定时任务服务启动")
    run_scheduler() 