import streamlit as st
import pandas as pd
from datetime import datetime
from user.user_process import UserManager
from user.logger import add_log

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
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_bill_record(self, user_id: str, api_name: str, operation: str,
                       input_letters: int, output_letters: int):
        """添加账单记录"""
        total_cost = (input_letters + output_letters) * self.COST_PER_CHAR
        
        conn = self.user_mgr.get_db_connection()
        c = conn.cursor()
        
        try:
            # 添加账单记录
            c.execute('''
            INSERT INTO bills (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                datetime.now().isoformat(),
                api_name,
                operation,
                input_letters,
                output_letters,
                total_cost
            ))
            
            # 更新用户使用统计
            c.execute('''
            UPDATE users 
            SET total_chars = total_chars + ?,
                total_cost = total_cost + ?,
                used_chars_today = used_chars_today + ?
            WHERE user_id = ?
            ''', (
                input_letters + output_letters,
                total_cost,
                input_letters + output_letters,
                user_id
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
                   total_cost
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
            SELECT SUM(input_letters + output_letters) as total_chars,
                   SUM(total_cost) as total_cost
            FROM bills
            WHERE user_id = ?
            ''', (user_id,))
            
            result = c.fetchone()
            
            return {
                'total_chars': result[0] or 0,
                'total_cost': result[1] or 0.0
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
    st.markdown("#### 总消费")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("总消费", f"¥{total['total_cost']:.4f}")
    with col2:
        st.metric("总字符数", f"{total['total_chars']:,}")
    
    # 获取账单记录
    records = bill_mgr.get_user_bills(user_info['user_id'])
    
    # 显示账单记录
    st.markdown("#### 消费记录")
    if records:
        # 创建DataFrame
        df = pd.DataFrame(records, columns=[
            '时间', 'API名称', '操作类型',
            '输入字符数', '输出字符数', '费用(元)'
        ])
        
        # 格式化显示
        st.dataframe(
            df.style.format({
                '费用(元)': '{:.4f}'
            }),
            use_container_width=True
        )
    else:
        st.info("暂无账单记录")