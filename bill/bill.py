import streamlit as st
import pandas as pd
from datetime import datetime
from user.user_process import UserManager
from user.logger import add_log

# 尝试导入 plotly，如果不可用则不使用图表功能
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    add_log("warning", "Plotly 未安装，将使用基本图表功能")

class BillManager:
    def __init__(self):
        self.user_mgr = UserManager()
        self.COST_PER_CHAR = 0.0001  # 每字符0.0001元人民币
    
    def init_bill_table(self):
        """初始化账单表"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            api_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            input_letters INTEGER NOT NULL,
            output_letters INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            points_cost INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
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
        if amount <= 0:
            return False
            
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 获取当前积分
            current_points = self.get_user_points(user_id)
            
            # 更新用户积分
            c.execute('''
                UPDATE users 
                SET points = points + ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            
            # 记录交易
            c.execute('''
                INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance,
                    description, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                type,
                amount,
                current_points + amount,
                description,
                None
            ))
            
            conn.commit()
            add_log("info", f"用户 {user_id} 增加 {amount} 积分")
            return True
            
        except Exception as e:
            conn.rollback()
            add_log("error", f"添加积分失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def deduct_points(self, user_id: str, amount: int, type: str, description: str) -> bool:
        """扣除积分"""
        if amount <= 0:
            return False
            
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 获取当前积分
            current_points = self.get_user_points(user_id)
            
            # 检查积分是否足够
            if current_points < amount:
                return False
            
            # 更新用户积分
            c.execute('''
                UPDATE users 
                SET points = points - ? 
                WHERE user_id = ?
            ''', (amount, user_id))
            
            # 记录交易
            c.execute('''
                INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance,
                    description, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                type,
                -amount,
                current_points - amount,
                description,
                None
            ))
            
            conn.commit()
            add_log("info", f"用户 {user_id} 扣除 {amount} 积分")
            return True
            
        except Exception as e:
            conn.rollback()
            add_log("error", f"扣除积分失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_points_history(self, user_id: str) -> pd.DataFrame:
        """获取积分历史记录"""
        conn = self.user_mgr.get_db_connection()
        try:
            query = '''
                SELECT timestamp, type, amount, balance, description
                FROM point_transactions
                WHERE user_id = ?
                ORDER BY timestamp DESC
            '''
            return pd.read_sql_query(query, conn, params=(user_id,))
        finally:
            conn.close()
    
    def add_bill_record(self, user_id: str, api_name: str, operation: str,
                       input_letters: int, output_letters: int):
        """添加账单记录"""
        total_cost = (input_letters + output_letters) * self.COST_PER_CHAR
        points_cost = input_letters + output_letters  # 1字符=1积分
        
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 检查用户积分是否足够
            current_points = self.get_user_points(user_id)
            
            if current_points < points_cost:
                raise Exception("积分不足")
            
            # 添加账单记录
            c.execute('''
            INSERT INTO bills (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost, points_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
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
                datetime.now().isoformat(),
                'consume',
                -points_cost,
                current_points - points_cost,
                f'使用{operation}消费',
                None
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"记录账单失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_user_bills(self, user_id: str):
        """获取用户的所有账单记录"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
            SELECT timestamp, api_name, operation, input_letters, output_letters,
                   total_cost, points_cost
            FROM bills
            WHERE user_id = ?
            ORDER BY timestamp DESC
            ''', (user_id,))
            
            records = c.fetchall()
            return records
            
        finally:
            conn.close()
    
    def get_user_total_usage(self, user_id: str):
        """获取用户的总使用量"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            c.execute('''
            SELECT 
                SUM(input_letters + output_letters) as total_chars,
                SUM(total_cost) as total_cost,
                SUM(points_cost) as total_points,
                (SELECT points FROM users WHERE user_id = ?) as current_points
            FROM bills
            WHERE user_id = ?
            ''', (user_id, user_id))
            
            result = c.fetchone()
            
            return {
                'total_chars': result[0] or 0,
                'total_cost': result[1] or 0.0,
                'total_points_cost': result[2] or 0,
                'current_points': result[3] or 0
            }
            
        finally:
            conn.close()

def show_bill_detail():
    """显示账单明细页面"""
    st.markdown("### 账单明细")
    
    # 获取当前用户信息
    user_mgr = UserManager()
    user_info = user_mgr.get_user_info(st.session_state.user)
    
    if not user_info:
        st.error("获取用户信息失败")
        return
    
    # 创建账单管理器实例
    bill_mgr = BillManager()
    
    # 获取用户总使用量
    total = bill_mgr.get_user_total_usage(user_info['user_id'])
    
    # 显示总账单
    st.markdown("#### 账户概览")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前积分", f"{total['current_points']:,}")
    with col2:
        st.metric("总消费积分", f"{total['total_points_cost']:,}")
    with col3:
        st.metric("总字符数", f"{total['total_chars']:,}")
    
    # 获取积分历史记录
    history_df = bill_mgr.get_points_history(user_info['user_id'])
    
    if not history_df.empty:
        # 添加积分趋势图
        st.markdown("#### 积分趋势")
        try:
            if HAS_PLOTLY:
                # 使用 plotly 绘制更美观的图表
                fig = px.line(history_df, 
                            x='timestamp', 
                            y='balance',
                            title='积分余额变化趋势')
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 使用 streamlit 的基本图表功能
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                st.line_chart(
                    history_df.set_index('timestamp')['balance'],
                    use_container_width=True
                )
        except Exception as e:
            # 如果绘图出错，记录日志并使用基本图表
            add_log("error", f"绘制积分趋势图失败: {str(e)}")
            st.line_chart(
                history_df.set_index('timestamp')['balance'],
                use_container_width=True
            )
    
    # 获取账单记录
    records = bill_mgr.get_user_bills(user_info['user_id'])
    
    # 显示账单记录
    st.markdown("#### 消费记录")
    if records:
        # 创建DataFrame
        df = pd.DataFrame(records, columns=[
            '时间', 'API名称', '操作类型',
            '输入字符数', '输出字符数', '费用(元)', '消费积分'
        ])
        
        # 格式化显示
        st.dataframe(
            df.style.format({
                '费用(元)': '{:.4f}',
                '消费积分': '{:,}'
            }),
            use_container_width=True,
            height=400
        )
    else:
        st.info("暂无账单记录")