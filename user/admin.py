import streamlit as st
import sqlite3
from datetime import datetime
from user.user_process import UserManager
from user.logger import add_log
from bill.bill import BillManager

def show_admin_panel():
    """显示管理员面板"""
    if st.session_state.get('user_role') != 'admin':
        st.error("无权限访问此页面")
        return
    
    st.title("用户管理面板")
    
    user_mgr = UserManager()
    bill_mgr = BillManager()
    conn = user_mgr.get_db_connection()
    c = conn.cursor()
    
    # 获取所有用户信息
    c.execute('''
        SELECT user_id, username, email, phone, org_name, role, is_active, 
               created_at, last_login, total_chars, total_cost,
               daily_chars_limit, used_chars_today, points
        FROM users
        ORDER BY created_at DESC
    ''')
    users = c.fetchall()
    conn.close()
    
    # 显示用户列表
    st.markdown("### 用户列表")
    for user in users:
        with st.expander(f"用户: {user[1]} ({user[0]})"):
            # 基本信息和使用统计
            col1, col2 = st.columns(2)
            with col1:
                st.write("基本信息:")
                st.write(f"- 邮箱: {user[2] or '未设置'}")
                st.write(f"- 电话: {user[3] or '未设置'}")
                st.write(f"- 组织: {user[4] or '未设置'}")
                st.write(f"- 角色: {user[5]}")
                st.write(f"- 状态: {'活跃' if user[6] else '禁用'}")
            
            with col2:
                st.write("使用统计:")
                st.write(f"- 创建时间: {user[7]}")
                st.write(f"- 最后登录: {user[8] or '从未登录'}")
                st.write(f"- 总字符数: {user[9]:,}")
                st.write(f"- 总消费: ¥{user[10]:.4f}")
                st.write(f"- 每日字符限制: {user[11]:,}")
                st.write(f"- 今日已用字符: {user[12]:,}")
                st.write(f"- 当前积分: {user[13]:,}")
            
            # 用户管理功能
            st.markdown("#### 用户管理")
            col3, col4, col5 = st.columns(3)
            
            # 账户状态管理
            with col3:
                if st.button(f"{'禁用' if user[6] else '启用'} 用户", key=f"toggle_{user[0]}"):
                    conn = user_mgr.get_db_connection()
                    c = conn.cursor()
                    new_status = 0 if user[6] else 1
                    c.execute('UPDATE users SET is_active = ? WHERE user_id = ?', 
                            (new_status, user[0]))
                    conn.commit()
                    conn.close()
                    add_log("info", f"用户 {user[1]} 状态已更新为 {'活跃' if new_status else '禁用'}")
                    st.rerun()
            
            # 密码重置
            with col4:
                if st.button("重置密码", key=f"reset_{user[0]}"):
                    conn = user_mgr.get_db_connection()
                    c = conn.cursor()
                    new_password = "Amazon123"  # 默认密码
                    hashed_password = user_mgr.hash_password(new_password)
                    c.execute('UPDATE users SET password = ? WHERE user_id = ?', 
                            (hashed_password, user[0]))
                    conn.commit()
                    conn.close()
                    add_log("info", f"用户 {user[1]} 密码已重置")
                    st.success(f"密码已重置为: {new_password}")
            
            # 字符限制管理
            with col5:
                new_limit = st.number_input(
                    "每日字符限制", 
                    min_value=0, 
                    value=user[11],
                    key=f"limit_{user[0]}"
                )
                if st.button("更新限制", key=f"update_limit_{user[0]}"):
                    conn = user_mgr.get_db_connection()
                    c = conn.cursor()
                    c.execute('UPDATE users SET daily_chars_limit = ? WHERE user_id = ?', 
                            (new_limit, user[0]))
                    conn.commit()
                    conn.close()
                    add_log("info", f"用户 {user[1]} 每日字符限制已更新为 {new_limit}")
                    st.success("每日字符限制已更新")
                    st.rerun()
            
            # 积分管理
            st.markdown("#### 积分管理")
            points_amount = st.number_input(
                "调整积分数量", 
                value=100,
                step=100,
                key=f"points_{user[0]}"
            )
            points_type = st.selectbox(
                "操作类型",
                ["奖励", "扣除"],
                key=f"points_type_{user[0]}"
            )
            points_reason = st.text_input(
                "操作原因",
                key=f"points_reason_{user[0]}"
            )
            
            if st.button("执行积分操作", key=f"update_points_{user[0]}"):
                if points_reason:
                    if points_type == "奖励":
                        success = bill_mgr.add_points(
                            user[0], 
                            points_amount,
                            'admin',
                            f"管理员奖励: {points_reason}"
                        )
                    else:
                        success = bill_mgr.deduct_points(
                            user[0],
                            points_amount,
                            'admin',
                            f"管理员扣除: {points_reason}"
                        )
                    
                    if success:
                        st.success(f"积分{'奖励' if points_type == '奖励' else '扣除'}成功")
                        add_log("info", f"管理员{points_type}用户 {user[1]} {points_amount} 积分")
                        st.rerun()
                    else:
                        st.error("操作失败")
                else:
                    st.error("请输入操作原因")