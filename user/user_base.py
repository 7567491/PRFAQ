import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, Dict, Any
from user.logger import add_log
from db.db_upgrade import upgrade_database

class UserManager:
    def __init__(self):
        self.db_path = 'db/users.db'
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            # 使用绝对路径
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'users.db')
            conn = sqlite3.connect(db_path)
            
            # 检查是否需要升级数据库
            try:
                # 尝试访问 points 列，如果不存在会抛出异常
                c = conn.cursor()
                c.execute("SELECT points FROM users LIMIT 1")
            except sqlite3.OperationalError:
                # 如果 points 列不存在，执行数据库升级
                conn.close()  # 先关闭当前连接
                upgrade_database()  # 执行升级
                conn = sqlite3.connect(db_path)  # 重新连接
            
            return conn
        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            raise
    
    def hash_password(self, password: str) -> str:
        """密码加密"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_user(self, username: str, password: str) -> bool:
        """验证用户登录"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            hashed_input = self.hash_password(password)
            # 同时检查用户是否活跃
            c.execute('''
                SELECT username, password, is_active 
                FROM users 
                WHERE username = ?
            ''', (username,))
            result = c.fetchone()
            
            if result and result[1] == hashed_input:
                if result[2] == 1:  # 检查是否活跃
                    return True
                else:
                    print("账户已被禁用")
                    return False
            return False
        finally:
            conn.close()
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT user_id, username, email, phone, org_name, role, is_active,
                       created_at, last_login, total_chars, total_cost,
                       daily_chars_limit, used_chars_today, points
                FROM users WHERE username = ?
            ''', (username,))
            
            result = c.fetchone()
            
            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'email': result[2],
                    'phone': result[3],
                    'org_name': result[4],
                    'role': result[5],
                    'is_active': bool(result[6]),
                    'created_at': result[7],
                    'last_login': result[8],
                    'total_chars': result[9],
                    'total_cost': result[10],
                    'daily_chars_limit': result[11],
                    'used_chars_today': result[12],
                    'points': result[13]
                }
        except sqlite3.Error as e:
            add_log("error", f"获取用户信息失败: {str(e)}")
        finally:
            conn.close()
        
        return None 
    
    def update_last_login(self, username: str):
        """更新最后登录时间"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE users 
                SET last_login = ? 
                WHERE username = ?
            ''', (datetime.now().isoformat(), username))
            
            conn.commit()
            add_log("info", f"更新用户 {username} 最后登录时间")
            return True
        except Exception as e:
            conn.rollback()
            add_log("error", f"更新最后登录时间失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def update_usage_stats(self, username: str, chars: int = 0, cost: float = 0.0):
        """更新用户使用统计"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                UPDATE users 
                SET total_chars = total_chars + ?,
                    total_cost = total_cost + ?,
                    used_chars_today = used_chars_today + ?
                WHERE username = ?
            ''', (chars, cost, chars, username))
            
            conn.commit()
            add_log("info", f"更新用户 {username} 使用统计")
            return True
        except Exception as e:
            conn.rollback()
            add_log("error", f"更新使用统计失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def check_daily_limit(self, username: str) -> bool:
        """检查用户是否达到每日字符使用限制"""
        conn = self.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT daily_chars_limit, used_chars_today 
                FROM users WHERE username = ?
            ''', (username,))
            
            result = c.fetchone()
            if result:
                daily_limit, used_today = result
                return used_today < daily_limit
            return False
        except Exception as e:
            add_log("error", f"检查每日限制失败: {str(e)}")
            return False
        finally:
            conn.close()