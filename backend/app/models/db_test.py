from .database import SessionLocal, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """测试数据库连接"""
    try:
        # 创建会话
        db = SessionLocal()
        
        # 尝试创建测试用户
        test_user = User(
            username="test_user",
            email="test@example.com",
            password_hash="test_hash"
        )
        
        # 添加到数据库
        db.add(test_user)
        db.commit()
        
        # 查询测试用户
        queried_user = db.query(User).filter(User.username == "test_user").first()
        assert queried_user is not None
        assert queried_user.email == "test@example.com"
        
        # 清理测试数据
        db.delete(queried_user)
        db.commit()
        
        logger.info("数据库连接测试成功!")
        
    except Exception as e:
        logger.error(f"数据库连接测试失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    test_database_connection() 