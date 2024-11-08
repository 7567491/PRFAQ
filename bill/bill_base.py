import sqlite3
from datetime import datetime
import pytz
import pandas as pd
from user.user_base import UserManager
from user.logger import add_log

# 定义时区
TIMEZONE = pytz.timezone('Asia/Shanghai')

class BillManager:
    def __init__(self):
        self.user_mgr = UserManager()
        self.COST_PER_CHAR = 0.0001  # 每字符0.0001元人民币
    
    def get_current_time(self) -> str:
        """获取当前东八区时间"""
        return datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')
    
    def safe_execute(self, conn, query, params=None):
        """安全执行SQL查询"""
        try:
            c = conn.cursor()
            if params:
                c.execute(query, params)
            else:
                c.execute(query)
            return c
        except sqlite3.Error as e:
            add_log("error", f"数据库执行错误: {str(e)}\nQuery: {query}\nParams: {params}")
            raise
    
    def get_user_points(self, user_id: str) -> int:
        """获取用户当前积分"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        try:
            c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
            result = c.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()
    
    def add_points(self, user_id: str, amount: int, type: str, description: str) -> bool:
        """添加积分"""
        if not isinstance(amount, int) or amount <= 0:
            add_log("error", f"无效的积分数量: {amount}")
            return False
            
        conn = None
        try:
            conn = self.user_mgr.get_db_connection()
            current_points = self.get_user_points(user_id)
            
            # 更新用户积分
            self.safe_execute(
                conn,
                'UPDATE users SET points = points + ? WHERE user_id = ?',
                (amount, user_id)
            )
            
            # 记录交易
            self.safe_execute(
                conn,
                '''INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance,
                    description, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    user_id,
                    self.get_current_time(),
                    type,
                    amount,
                    current_points + amount,
                    description,
                    None
                )
            )
            
            conn.commit()
            add_log("info", f"用户 {user_id} 增加 {amount} 积分")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            add_log("error", f"添加积分失败: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def deduct_points(self, user_id: str, amount: int, type: str, description: str) -> bool:
        """扣除积分"""
        if not isinstance(amount, int) or amount <= 0:
            add_log("error", f"无效的扣除积分数量: {amount}")
            return False
            
        conn = None
        try:
            conn = self.user_mgr.get_db_connection()
            current_points = self.get_user_points(user_id)
            
            if current_points < amount:
                add_log("warning", f"用户 {user_id} 积分不足: 当前{current_points}, 需要{amount}")
                return False
            
            # 更新用户积分
            self.safe_execute(
                conn,
                'UPDATE users SET points = points - ? WHERE user_id = ?',
                (amount, user_id)
            )
            
            # 记录交易
            self.safe_execute(
                conn,
                '''INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance,
                    description, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    user_id,
                    self.get_current_time(),
                    type,
                    -amount,
                    current_points - amount,
                    description,
                    None
                )
            )
            
            conn.commit()
            add_log("info", f"用户 {user_id} 扣除 {amount} 积分")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            add_log("error", f"扣除积分失败: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_user_total_usage(self, user_id: str) -> dict:
        """获取用户的总使用量统计"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 获取账单统计
            c.execute('''
                SELECT 
                    SUM(input_letters + output_letters) as total_chars,
                    SUM(total_cost) as total_cost,
                    SUM(points_cost) as total_points_cost
                FROM bills
                WHERE user_id = ?
            ''', (user_id,))
            
            bill_stats = c.fetchone()
            
            # 获取当前积分
            c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
            current_points = c.fetchone()[0]
            
            return {
                'total_chars': bill_stats[0] or 0,
                'total_cost': bill_stats[1] or 0.0,
                'total_points_cost': bill_stats[2] or 0,
                'current_points': current_points
            }
            
        except Exception as e:
            add_log("error", f"获取用户使用统计失败: {str(e)}")
            return {
                'total_chars': 0,
                'total_cost': 0.0,
                'total_points_cost': 0,
                'current_points': 0
            }
        finally:
            conn.close()
    
    def get_points_history(self, user_id: str) -> pd.DataFrame:
        """获取用户的积分历史记录"""
        conn = self.user_mgr.get_db_connection()
        
        try:
            # 使用pandas直接从数据库读取数据
            query = '''
                SELECT 
                    timestamp,
                    type,
                    amount,
                    balance,
                    description
                FROM point_transactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            
            df = pd.read_sql_query(
                query,
                conn,
                params=(user_id,),
                parse_dates=['timestamp']
            )
            
            return df
            
        except Exception as e:
            add_log("error", f"获取积分历史记录失败: {str(e)}")
            return pd.DataFrame()  # 返回空DataFrame
        finally:
            conn.close()
    
    def get_user_bills(self, user_id: str) -> list:
        """获取用户的所有账单记录"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
                SELECT 
                    timestamp,
                    api_name,
                    operation,
                    input_letters,
                    output_letters,
                    (input_letters + output_letters) as total_letters,
                    points_cost
                FROM bills
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (user_id,))
            
            return c.fetchall()
            
        except Exception as e:
            add_log("error", f"获取用户账单记录失败: {str(e)}")
            return []
        finally:
            conn.close()
    
    def add_bill_record(self, user_id: str, api_name: str, operation: str,
                       input_letters: int, output_letters: int) -> bool:
        """添加账单记录"""
        total_cost = (input_letters + output_letters) * self.COST_PER_CHAR
        points_cost = input_letters + output_letters  # 1字符=1积分
        
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 检查用户积分是否足够
            current_points = self.get_user_points(user_id)
            
            if current_points < points_cost:
                add_log("error", f"用户 {user_id} 积分不足，需要 {points_cost} 积分")
                return False
            
            # 添加账单记录
            c.execute('''
            INSERT INTO bills (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost, points_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                api_name,
                operation,
                input_letters,
                output_letters,
                total_cost,
                points_cost
            ))
            
            # 更新用户使用统计和积分
            c.execute('''
            UPDATE users 
            SET total_chars = total_chars + ?,
                total_cost = total_cost + ?,
                used_chars_today = used_chars_today + ?,
                points = points - ?
            WHERE user_id = ?
            ''', (
                input_letters + output_letters,
                total_cost,
                input_letters + output_letters,
                points_cost,
                user_id
            ))
            
            # 添加积分交易记录
            c.execute('''
            INSERT INTO point_transactions (
                user_id, timestamp, type, amount, balance,
                description, operation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'consume',
                -points_cost,
                current_points - points_cost,
                f'使用{operation}消费',
                None
            ))
            
            conn.commit()
            add_log("info", f"用户 {user_id} 使用 {operation} 消费 {points_cost} 积分")
            return True
            
        except Exception as e:
            conn.rollback()
            add_log("error", f"记录账单失败: {str(e)}")
            return False
        finally:
            conn.close()