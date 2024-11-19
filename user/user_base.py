import sqlite3
import hashlib
from datetime import datetime
from modules.logger import add_log

class UserManager:
    def __init__(self):
        self.db_path = 'db/users.db'
    
    def get_db_connection(self):
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            add_log("error", f"数据库连接失败: {str(e)}")
            return None
    
    def list_users(self):
        """获取所有用户列表"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            # 按照现有的数据库结构获取用户信息
            cursor.execute("""
                SELECT user_id, username, email, phone, org_name, role, 
                       is_active, created_at, last_login, total_chars,
                       total_cost, daily_chars_limit, used_chars_today, points
                FROM users
                ORDER BY created_at DESC
            """)
            
            columns = [description[0] for description in cursor.description]
            users = []
            
            for row in cursor.fetchall():
                user_dict = dict(zip(columns, row))
                # 转换布尔值
                user_dict['is_active'] = bool(user_dict['is_active'])
                users.append(user_dict)
            
            conn.close()
            return users
            
        except Exception as e:
            error_msg = f"获取用户列表失败: {str(e)}"
            add_log("error", error_msg)
            return []
    
    def get_user_role(self, username):
        """获取用户角色"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return 'user'
                
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT role FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return result[0]
            return 'user'  # 默认角色
            
        except Exception as e:
            add_log("error", f"获取用户角色失败: {str(e)}")
            return 'user'
    
    def verify_user(self, username, password):
        """验证用户登录"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT password, is_active FROM users WHERE username = ?",
                (username,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False
                
            stored_password, is_active = result
            
            # 检查用户是否被禁用
            if not is_active:
                return False
            
            # 验证密码
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if hashed_password == stored_password:
                return True
                
            return False
            
        except Exception as e:
            add_log("error", f"验证用户失败: {str(e)}")
            return False
        finally:
            if 'conn' in locals():
                conn.close()
    
    def get_user_info(self, username):
        """获取用户详细信息"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return None
                
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, email, phone, org_name, role,
                       is_active, created_at, last_login, total_chars,
                       total_cost, daily_chars_limit, used_chars_today, points
                FROM users WHERE username = ?
            """, (username,))
            
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                user_info = dict(zip(columns, result))
                user_info['is_active'] = bool(user_info['is_active'])
                return user_info
            return None
            
        except Exception as e:
            add_log("error", f"获取用户信息失败: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()
    
    def update_last_login(self, username):
        """更新用户最后登录时间"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE username = ?",
                (current_time, username)
            )
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            add_log("error", f"更新最后登录时间失败: {str(e)}")
            return False
    
    def create_user(self, username, password, user_data=None, role='user'):
        """创建新用户"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False, "数据库连接失败"
            
            cursor = conn.cursor()
            
            # 检查用户名是否已存在
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "用户名已存在"
            
            # 生成用户ID (简单格式：user_当前时间戳)
            user_id = f"user_{int(datetime.now().timestamp())}"
            
            # 创建新用户，初始积分设为20000
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            # 准备用户数据
            user_data = user_data or {}
            
            cursor.execute("""
                INSERT INTO users (
                    user_id, username, password, email, phone, org_name,
                    role, is_active, created_at, last_login,
                    total_chars, total_cost, daily_chars_limit,
                    used_chars_today, points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, 0, 0.0, 100000, 0, 20000)
            """, (
                user_id,
                username,
                hashed_password,
                user_data.get('email', ''),
                user_data.get('phone', ''),
                user_data.get('org_name', ''),
                role,
                current_time,
                current_time
            ))
            
            conn.commit()
            conn.close()
            
            add_log("info", f"创建新用户成功: {username}")
            return True, "用户创建成功"
            
        except Exception as e:
            error_msg = f"创建用户失败: {str(e)}"
            add_log("error", error_msg)
            return False, error_msg