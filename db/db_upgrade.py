import sqlite3
from datetime import datetime
import traceback
from user.logger import add_log

def upgrade_database():
    """升级数据库结构"""
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 检查history表中是否已存在test_results列
        cursor.execute("PRAGMA table_info(history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        details = []
        
        if 'test_results' not in columns:
            print("开始添加test_results列...")
            # 添加test_results列到history表
            cursor.execute('''
                ALTER TABLE history 
                ADD COLUMN test_results TEXT
            ''')
            details.append("添加test_results列到history表")
            print("test_results列添加成功")
            add_log("info", "数据库升级：添加test_results列到history表")
        
        # 检查history表中是否已存在input_text和output_text列
        if 'input_text' not in columns:
            cursor.execute('''
                ALTER TABLE history 
                ADD COLUMN input_text TEXT
            ''')
            details.append("添加input_text列到history表")
            
        if 'output_text' not in columns:
            cursor.execute('''
                ALTER TABLE history 
                ADD COLUMN output_text TEXT
            ''')
            details.append("添加output_text列到history表")
        
        # 提交更改
        conn.commit()
        print("数据库升级完成")
        add_log("info", "数据库升级成功完成")
        
        return {
            'success': True,
            'message': "数据库升级成功",
            'details': details
        }
        
    except sqlite3.Error as e:
        error_msg = f"数据库升级失败: {str(e)}\n"
        error_msg += traceback.format_exc()
        print(error_msg)
        add_log("error", error_msg)
        return {
            'success': False,
            'message': f"数据库升级失败: {str(e)}",
            'details': [error_msg]
        }
        
    except Exception as e:
        error_msg = f"数据库升级时发生未预期的错误: {str(e)}\n"
        error_msg += traceback.format_exc()
        print(error_msg)
        add_log("error", error_msg)
        return {
            'success': False,
            'message': f"数据库升级失败: {str(e)}",
            'details': [error_msg]
        }
        
    finally:
        if 'conn' in locals():
            conn.close()

def check_and_upgrade():
    """检查并执行数据库升级"""
    try:
        print("检查数据库是否需要升级...")
        
        # 连接数据库
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 检查history表结构
        cursor.execute("PRAGMA table_info(history)")
        columns = [column[1] for column in cursor.fetchall()]
        
        needs_upgrade = (
            'test_results' not in columns or 
            'input_text' not in columns or 
            'output_text' not in columns
        )
        
        if needs_upgrade:
            print("数据库需要升级")
            result = upgrade_database()
            return result['success']
        else:
            print("数据库已是最新版本")
            return True
            
    except Exception as e:
        error_msg = f"检查数据库版本时发生错误: {str(e)}"
        print(error_msg)
        add_log("error", error_msg)
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_and_upgrade()