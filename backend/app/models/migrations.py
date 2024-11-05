from .database import Base, engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migrations():
    """运行数据库迁移"""
    try:
        # 创建所有表
        logger.info("开始创建数据库表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功!")
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        raise

if __name__ == "__main__":
    run_migrations() 