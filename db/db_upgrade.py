import sqlite3
import os
from datetime import datetime
from pathlib import Path

def get_db_version(conn):
    """获取数据库当前版本"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM db_version ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 0
    except sqlite3.OperationalError:
        # 如果db_version表不存在，创建它
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS db_version (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL,
            description TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        return 0

def create_aws_tables(conn):
    """创建AWS相关的表结构"""
    cursor = conn.cursor()
    
    # AWS客户关联表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aws_customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        customer_identifier TEXT NOT NULL,
        aws_account_id TEXT NOT NULL,
        product_code TEXT NOT NULL,
        subscription_status INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE (customer_identifier)
    )
    """)

    # AWS订阅历史表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aws_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aws_customer_id INTEGER NOT NULL,
        entitlement_value INTEGER NOT NULL,
        dimension_name TEXT NOT NULL,
        valid_from TIMESTAMP NOT NULL,
        valid_to TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (aws_customer_id) REFERENCES aws_customers(id)
    )
    """)

    # AWS通知记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS aws_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aws_customer_id INTEGER NOT NULL,
        notification_type TEXT NOT NULL,
        message TEXT NOT NULL,
        processed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP,
        FOREIGN KEY (aws_customer_id) REFERENCES aws_customers(id)
    )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_customers_user_id ON aws_customers(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_customers_customer_id ON aws_customers(customer_identifier)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_subscriptions_customer_id ON aws_subscriptions(aws_customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_notifications_customer_id ON aws_notifications(aws_customer_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_notifications_processed ON aws_notifications(processed)")

def verify_aws_tables(conn):
    """验证AWS相关表是否创建成功"""
    cursor = conn.cursor()
    tables = ['aws_customers', 'aws_subscriptions', 'aws_notifications']
    
    for table in tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cursor.fetchone():
            return False
    return True

def rollback_aws_tables(conn):
    """回滚AWS相关表结构"""
    cursor = conn.cursor()
    
    # 删除索引
    indexes = [
        'idx_aws_customers_user_id',
        'idx_aws_customers_customer_id',
        'idx_aws_subscriptions_customer_id',
        'idx_aws_notifications_customer_id',
        'idx_aws_notifications_processed'
    ]
    
    for index in indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index}")
        except sqlite3.Error as e:
            print(f"删除索引 {index} 失败: {e}")
    
    # 删除表
    tables = ['aws_notifications', 'aws_subscriptions', 'aws_customers']
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        except sqlite3.Error as e:
            print(f"删除表 {table} 失败: {e}")

def check_and_upgrade():
    """检查并升级数据库"""
    try:
        db_path = Path("db/users.db")
        if not db_path.exists():
            print("数据库文件不存在")
            return False

        conn = sqlite3.connect(db_path)
        current_version = get_db_version(conn)
        
        # 定义升级步骤
        upgrades = {
            1: {
                "description": "添加AWS Marketplace相关表结构",
                "upgrade": create_aws_tables,
                "verify": verify_aws_tables,
                "rollback": rollback_aws_tables
            }
            # 可以在这里添加更多版本的升级步骤
        }

        # 执行升级
        for version, upgrade_info in upgrades.items():
            if version > current_version:
                print(f"\n开始执行版本 {version} 升级: {upgrade_info['description']}")
                
                try:
                    # 执行升级
                    upgrade_info["upgrade"](conn)
                    
                    # 验证升级
                    if upgrade_info["verify"](conn):
                        # 更新版本号
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO db_version (version, description) VALUES (?, ?)",
                            (version, upgrade_info["description"])
                        )
                        conn.commit()
                        print(f"版本 {version} 升级成功")
                    else:
                        print(f"版本 {version} 验证失败，执行回滚")
                        upgrade_info["rollback"](conn)
                        conn.rollback()
                        return False
                        
                except Exception as e:
                    print(f"版本 {version} 升级失败: {str(e)}")
                    print("执行回滚...")
                    upgrade_info["rollback"](conn)
                    conn.rollback()
                    return False

        conn.close()
        return True
        
    except Exception as e:
        print(f"数据库升级过程出错: {str(e)}")
        return False

def upgrade_database():
    """
    供其他模块调用的数据库升级函数
    Returns:
        bool: 升级是否成功
    """
    try:
        return check_and_upgrade()
    except Exception as e:
        print(f"数据库升级失败: {str(e)}")
        return False

if __name__ == "__main__":
    if check_and_upgrade():
        print("数据库升级完成")
    else:
        print("数据库升级失败")