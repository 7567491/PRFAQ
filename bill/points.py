import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from user.user_process import UserManager
from user.logger import add_log

class PointsManager:
    def __init__(self):
        self.user_mgr = UserManager()
    
    def get_user_points(self, user_id: str) -> dict:
        """获取用户积分信息"""
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        try:
            # 获取用户当前积分和总消费
            c.execute('''
                SELECT points, 
                       (SELECT SUM(points_cost) FROM bills WHERE user_id = users.user_id) as total_consumed,
                       (SELECT COUNT(*) FROM point_transactions WHERE user_id = users.user_id) as transaction_count
                FROM users 
                WHERE user_id = ?
            ''', (user_id,))
            result = c.fetchone()
            
            return {
                'current_points': result[0] or 0,
                'total_consumed': result[1] or 0,
                'transaction_count': result[2] or 0
            }
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
    
    def add_points(self, user_id: str, amount: int, type: str, description: str) -> bool:
        """添加积分"""
        if amount <= 0:
            return False
        
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 获取当前积分
            c.execute('SELECT points FROM users WHERE user_id = ?', (user_id,))
            current_points = c.fetchone()[0]
            
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
    
    def show_points_dashboard(self, user_id: str):
        """显示积分统计面板"""
        # 获取积分信息
        points_info = self.get_user_points(user_id)
        
        # 显示积分概览
        st.markdown("#### 积分概览")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("当前积分", f"{points_info['current_points']:,}")
        with col2:
            st.metric("已消费积分", f"{points_info['total_consumed']:,}")
        with col3:
            st.metric("交易次数", f"{points_info['transaction_count']:,}")
        
        # 获取历史记录
        history_df = self.get_points_history(user_id)
        
        if not history_df.empty:
            # 添加积分趋势图
            st.markdown("#### 积分趋势")
            fig = px.line(history_df, 
                         x='timestamp', 
                         y='balance',
                         title='积分余额变化趋势')
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示交易记录
            st.markdown("#### 积分明细")
            
            # 格式化显示
            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
            history_df['timestamp'] = history_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 根据类型设置不同颜色
            def color_amount(val):
                color = 'green' if val > 0 else 'red'
                return f'color: {color}'
            
            st.dataframe(
                history_df.style.applymap(color_amount, subset=['amount']),
                use_container_width=True
            )
        else:
            st.info("暂无积分记录")

def show_points_detail():
    """显示积分明细页面"""
    st.title("积分明细")
    
    # 获取当前用户信息
    user_mgr = UserManager()
    user_info = user_mgr.get_user_info(st.session_state.user)
    
    if not user_info:
        st.error("获取用户信息失败")
        return
    
    # 创建积分管理器实例
    points_mgr = PointsManager()
    
    # 显示积分统计面板
    points_mgr.show_points_dashboard(user_info['user_id']) 