import schedule
import time
from user.user_process import reset_daily_usage
from datetime import datetime
import logging

logging.basicConfig(
    filename='db/scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def daily_reset():
    """每日重置任务"""
    try:
        reset_daily_usage()
        logging.info("每日使用量已重置")
    except Exception as e:
        logging.error(f"重置每日使用量时出错: {str(e)}")

def run_scheduler():
    """运行定时任务"""
    # 设置每天凌晨重置
    schedule.every().day.at("00:00").do(daily_reset)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    logging.info("定时任务启动")
    run_scheduler() 