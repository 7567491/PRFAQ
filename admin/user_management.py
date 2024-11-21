import sqlite3
import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from db.db_table import get_table_info
from modules.utils import add_log

class UserManagement:
    def __init__(self, db_path: str = 'db/users.db'):
        self.db_path = db_path
        try:
            # 获取users表的结构信息
            self.table_info = get_table_info('users')
            if not self.table_info:
                add_log("error", "无法获取users表结构信息")
                raise ValueError("表结构信息为空")
                
            self.columns = [col['name'] for col in self.table_info]
        except Exception as e:
            add_log("error", f"初始化UserManagement失败: {str(e)}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
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
            return users
        except Exception as e:
            add_log("error", f"获取用户列表失败: {str(e)}")
            raise
        finally:
            conn.close()
    
    def update_user_status(self, user_id: str, status: str) -> bool:
        """更新用户状态"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            status_value = 1 if status == 'active' else 0
            c.execute("UPDATE users SET is_active = ? WHERE user_id = ?", 
                     (status_value, user_id))
            conn.commit()
            add_log("info", f"用户 {user_id} 状态更新为 {status}")
            return True
        except Exception as e:
            error_msg = f"更新用户状态失败: {str(e)}"
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
            c.execute(query, (role, user_id))
            conn.commit()
            add_log("info", f"用户 {user_id} 角色更新为 {role}")
            return True
        except Exception as e:
            error_msg = f"更新用户角色失败: {str(e)}"
            add_log("error", error_msg)
            st.error(error_msg)
            return False
        finally:
            conn.close()
    
    def get_user_related_counts(self, user_id: str) -> Dict[str, int]:
        """获取用户相关的记录数量"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            counts = {}
            
            # 检查各个表中的相关记录
            tables = {
                'bills': 'user_id',
                'history': 'user_id',
                'points': 'user_id',
                'chat_history': 'user_id',
                'aws_customers': 'user_id',
                'aws_subscriptions': 'user_id',
                'aws_usage': 'user_id'
            }
            
            for table, id_field in tables.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {id_field} = ?", (user_id,))
                    counts[table] = cursor.fetchone()[0]
                except sqlite3.OperationalError:
                    counts[table] = 0
                    
            return counts
            
        except Exception as e:
            add_log("error", f"获取用户关联记录数失败: {str(e)}")
            return {}
        finally:
            conn.close()
    
    def delete_user(self, user_id: str, username: str) -> bool:
        """删除用户及其所有相关数据"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # 验证用户是否存在
            cursor.execute("SELECT username, role FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("用户不存在")
                
            # 检查是否为系统管理员
            if user[1] == 'admin':
                raise ValueError("不能删除管理员账号")
                
            # 开始事务
            conn.execute("BEGIN TRANSACTION")
            
            # 删除各个表中的相关记录
            tables = [
                ('users', 'user_id'),
                ('bills', 'user_id'),
                ('history', 'user_id'),
                ('points', 'user_id'),
                ('chat_history', 'user_id'),
                ('aws_customers', 'user_id'),
                ('aws_subscriptions', 'user_id'),
                ('aws_usage', 'user_id')
            ]
            
            for table, id_field in tables:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE {id_field} = ?", (user_id,))
                except sqlite3.OperationalError as e:
                    add_log("debug", f"表 {table} 删除失败（可能不存在）: {str(e)}")
            
            # 提交事务
            conn.commit()
            add_log("info", f"成功删除用户 {username} (ID: {user_id}) 及其相关数据")
            return True
            
        except Exception as e:
            conn.rollback()
            error_msg = f"删除用户失败: {str(e)}"
            add_log("error", error_msg)
            return False
        finally:
            conn.close()

def show_user_management():
    """显示用户管理界面"""
    st.markdown("### 用户管理")
    
    try:
        user_mgmt = UserManagement()
        
        # 获取所有用户
        users = user_mgmt.get_all_users()
        
        if not users:
            st.warning("没有找到任何用户")
            return
            
        # 创建用户表格数据
        users_df = pd.DataFrame(users)
        
        # 转换和格式化数据
        users_df['is_active'] = users_df['is_active'].map({1: '活跃', 0: '禁用'})
        users_df['total_cost'] = users_df['total_cost'].map(lambda x: f"{x:.2f}")
        
        # 重命名列
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
        users_df = users_df.rename(columns=column_names)
        
        # 按创建时间倒序排序
        users_df = users_df.sort_values('创建时间', ascending=False)
        
        # 显示用户表格
        st.markdown("#### 用户列表")
        st.dataframe(
            users_df,
            column_config={
                '用户ID': st.column_config.TextColumn('用户ID', width='small'),
                '用户名': st.column_config.TextColumn('用户名', width='small'),
                '邮箱': st.column_config.TextColumn('邮箱', width='medium'),
                '电话': st.column_config.TextColumn('电话', width='small'),
                '组织名称': st.column_config.TextColumn('组织', width='small'),
                '角色': st.column_config.TextColumn('角色', width='small'),
                '状态': st.column_config.TextColumn('状态', width='small'),
                '创建时间': st.column_config.DatetimeColumn('创建时间', width='medium'),
                '最后登录': st.column_config.DatetimeColumn('最后登录', width='medium'),
                '总字符数': st.column_config.NumberColumn('总字符数', width='small', format="%d"),
                '总消费(元)': st.column_config.TextColumn('总消费', width='small'),
                '日限额': st.column_config.NumberColumn('日限额', width='small'),
                '今日已用': st.column_config.NumberColumn('今日用量', width='small'),
                '积分': st.column_config.NumberColumn('积分', width='small')
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("#### 用户详情")
        
        # 添加删除确认状态
        if 'delete_confirm' not in st.session_state:
            st.session_state.delete_confirm = {}
        
        # 显示用户详细信息和操作按钮
        for user in users:
            with st.container():
                # 显示用户信息
                st.markdown(f"""
                **用户名**: {user['username']}  
                **角色**: {user['role']}  
                **状态**: {'活跃' if user['is_active'] else '禁用'}  
                **创建时间**: {user['created_at']}
                """)
                
                user_id = user['user_id']
                if user['role'] != 'admin':  # 不显示管理员的删除按钮
                    if not st.session_state.delete_confirm.get(user_id):
                        if st.button("🗑️ 删除用户", key=f"del_{user_id}", type="primary"):
                            st.session_state.delete_confirm[user_id] = True
                            st.rerun()
                    else:
                        # 显示确认界面
                        st.warning("⚠️ 确认删除？此操作不可恢复！")
                        confirm_username = st.text_input(
                            "输入用户名确认删除",
                            key=f"confirm_{user_id}"
                        )
                        
                        # 获取并显示关联数据统计
                        related_counts = user_mgmt.get_user_related_counts(user_id)
                        if related_counts:
                            st.info("将删除以下关联数据：")
                            for table, count in related_counts.items():
                                if count > 0:
                                    st.text(f"- {table}: {count} 条记录")
                        
                        # 使用单层列布局
                        confirm_col1, confirm_col2 = st.columns(2)
                        with confirm_col1:
                            if st.button("确认", key=f"confirm_del_{user_id}", type="primary"):
                                if confirm_username == user['username']:
                                    if user_mgmt.delete_user(user_id, user['username']):
                                        st.success("用户删除成功")
                                        st.session_state.delete_confirm.pop(user_id)
                                        st.rerun()
                                    else:
                                        st.error("删除失败，请查看日志")
                                else:
                                    st.error("用户名不匹配")
                        with confirm_col2:
                            if st.button("取消", key=f"cancel_del_{user_id}"):
                                st.session_state.delete_confirm.pop(user_id)
                                st.rerun()
            
            st.markdown("---")
        
        # 用户管理操作
        st.markdown("#### 用户操作")
        manage_col1, manage_col2 = st.columns(2)
        
        with manage_col1:
            user_id = st.text_input("用户ID（状态）")
            new_status = st.selectbox("新状态", ['active', 'inactive'])
            if st.button("更新状态"):
                if user_mgmt.update_user_status(user_id, new_status):
                    st.success("状态更新成功")
                    st.rerun()
        
        with manage_col2:
            role_user_id = st.text_input("用户ID（角色）")
            new_role = st.selectbox("新角色", ['user', 'admin'])
            if st.button("更新角色"):
                if user_mgmt.update_user_role(role_user_id, new_role):
                    st.success("角色更新成功")
                    st.rerun()
            
    except Exception as e:
        error_msg = f"用户管理界面加载失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg) 