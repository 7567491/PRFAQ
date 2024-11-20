import sqlite3
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from db.db_table import get_table_info
import logging
from modules.utils import add_log

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManagement:
    def __init__(self, db_path: str = 'db/users.db'):
        self.db_path = db_path
        try:
            # 获取users表的结构信息
            self.table_info = get_table_info('users')
            if not self.table_info:
                logger.error("无法获取users表结构信息")
                add_log("error", "无法获取users表结构信息")
                raise ValueError("表结构信息为空")
                
            self.columns = [col['name'] for col in self.table_info]
            logger.info(f"成功获取到表结构，列信息: {self.columns}")
        except Exception as e:
            logger.error(f"初始化UserManagement失败: {str(e)}")
            add_log("error", f"初始化UserManagement失败: {str(e)}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.db_path)
            logger.info(f"成功连接到数据库: {self.db_path}")
            return conn
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            add_log("error", f"数据库连接失败: {str(e)}")
            raise
    
    def get_all_users(self) -> List[Dict]:
        """获取所有用户列表"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            query = """
                SELECT user_id, username, email, phone, org_name, role, 
                       is_active, created_at, last_login, total_chars, 
                       total_cost, daily_chars_limit, used_chars_today, points
                FROM users
                ORDER BY created_at DESC
            """
            logger.info(f"执行查询: {query}")
            
            c.execute(query)
            users = []
            for row in c.fetchall():
                users.append({
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'org_name': row[4],
                    'role': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'last_login': row[8],
                    'total_chars': row[9],
                    'total_cost': row[10],
                    'daily_chars_limit': row[11],
                    'used_chars_today': row[12],
                    'points': row[13]
                })
            
            logger.info(f"成功获取到 {len(users)} 条用户记录")
            return users
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}\nSQL: {query}")
            add_log("error", f"获取用户列表失败: {str(e)}")
            raise
        finally:
            conn.close()
    
    def update_user_status(self, user_id: str, status: str) -> bool:
        """更新用户状态"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            query = """
                UPDATE users
                SET is_active = ?
                WHERE user_id = ?
            """
            status_value = 1 if status == 'active' else 0
            logger.info(f"执行状态更新: user_id={user_id}, is_active={status_value}")
            c.execute(query, (status_value, user_id))
            conn.commit()
            logger.info("状态更新成功")
            add_log("info", f"用户 {user_id} 状态更新为 {status}")
            return True
        except Exception as e:
            error_msg = f"更新用户状态失败: {str(e)}"
            logger.error(error_msg)
            add_log("error", error_msg)
            st.error(error_msg)
            return False
        finally:
            conn.close()
    
    def update_user_role(self, user_id: str, role: str) -> bool:
        """更新用户角色"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            query = """
                UPDATE users
                SET role = ?
                WHERE user_id = ?
            """
            logger.info(f"执行角色更新: user_id={user_id}, role={role}")
            c.execute(query, (role, user_id))
            conn.commit()
            logger.info("角色更新成功")
            add_log("info", f"用户 {user_id} 角色更新为 {role}")
            return True
        except Exception as e:
            error_msg = f"更新用户角色失败: {str(e)}"
            logger.error(error_msg)
            add_log("error", error_msg)
            st.error(error_msg)
            return False
        finally:
            conn.close()

def show_user_management():
    """显示用户管理界面"""
    st.markdown("### 用户管理")
    
    try:
        user_mgmt = UserManagement()
        logger.info("UserManagement初始化成功")
        
        # 获取所有用户
        users = user_mgmt.get_all_users()
        
        if not users:
            logger.warning("没有找到任何用户记录")
            st.warning("没有找到任何用户")
            return
        
        # 显示用户列表
        df = pd.DataFrame(users)
        # 获取中文列名映射
        column_names = {
            'user_id': '用户ID',
            'username': '用户名',
            'email': '邮箱',
            'phone': '电话',
            'org_name': '组织名称',
            'role': '角色',
            'is_active': '状态',
            'created_at': '创建时间',
            'last_login': '最后登录',
            'total_chars': '总字符数',
            'total_cost': '总消费(元)',
            'daily_chars_limit': '日限额',
            'used_chars_today': '今日已用',
            'points': '积分'
        }
        # 只重命名存在的列
        rename_cols = {col: column_names.get(col, col) for col in df.columns}
        df.columns = [rename_cols[col] for col in df.columns]
        
        # 转换is_active为更友好的显示
        if 'is_active' in df.columns:
            df['状态'] = df['状态'].map({1: '活跃', 0: '禁用'})
            
        # 格式化金额显示
        if 'total_cost' in df.columns:
            df['总消费(元)'] = df['总消费(元)'].map(lambda x: f"{x:.2f}")
            
        st.dataframe(df, use_container_width=True)
        
        # 用户管理操作
        st.markdown("#### 用户操作")
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input("用户ID（状态）")
            new_status = st.selectbox("新状态", ['active', 'inactive'])
            if st.button("更新状态"):
                if user_mgmt.update_user_status(user_id, new_status):
                    st.success("状态更新成功")
                    st.rerun()
        
        with col2:
            role_user_id = st.text_input("用户ID（角色）")
            new_role = st.selectbox("新角色", ['user', 'admin'])
            if st.button("更新角色"):
                if user_mgmt.update_user_role(role_user_id, new_role):
                    st.success("角色更新成功")
                    st.rerun()
            
    except Exception as e:
        error_msg = f"用户管理界面加载失败: {str(e)}"
        logger.error(error_msg)
        add_log("error", error_msg)
        st.error(error_msg) 