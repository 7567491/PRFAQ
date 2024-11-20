import streamlit as st
import pandas as pd
import sqlite3
from modules.utils import add_log

def get_user_stats():
    """获取用户统计信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        
        # 总用户数
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        
        # 活跃用户数
        c.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = c.fetchone()[0]
        
        # 今日新增用户
        c.execute("""
            SELECT COUNT(*) FROM users 
            WHERE date(created_at) = date('now')
        """)
        new_users_today = c.fetchone()[0]
        
        # 总消费金额
        c.execute("SELECT SUM(total_cost) FROM users")
        total_cost = c.fetchone()[0] or 0
        
        # 总字符使用量
        c.execute("SELECT SUM(total_chars) FROM users")
        total_chars = c.fetchone()[0] or 0
        
        # 用户角色分布
        c.execute("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
        """)
        role_dist = dict(c.fetchall())
        
        conn.close()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'new_users_today': new_users_today,
            'total_cost': total_cost,
            'total_chars': total_chars,
            'role_dist': role_dist
        }
    except Exception as e:
        add_log("error", f"获取用户统计信息失败: {str(e)}")
        raise

def get_recent_users(limit: int = 5):
    """获取最近注册的用户"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            SELECT user_id, username, email, role, created_at, 
                   total_chars, total_cost, points
            FROM users
            ORDER BY created_at DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        # 重命名列
        df.columns = ['用户ID', '用户名', '邮箱', '角色', '注册时间', 
                     '总字符数', '总消费(元)', '积分']
        
        # 格式化金额
        df['总消费(元)'] = df['总消费(元)'].map(lambda x: f"{x:.2f}")
        
        return df
    except Exception as e:
        add_log("error", f"获取最近用户失败: {str(e)}")
        raise

def get_top_users(limit: int = 5):
    """获取消费排行榜"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            SELECT user_id, username, total_chars, total_cost, points
            FROM users
            ORDER BY total_cost DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        
        # 重命名列
        df.columns = ['用户ID', '用户名', '总字符数', '总消费(元)', '积分']
        
        # 格式化金额
        df['总消费(元)'] = df['总消费(元)'].map(lambda x: f"{x:.2f}")
        
        return df
    except Exception as e:
        add_log("error", f"获取用户排行榜失败: {str(e)}")
        raise

def show_user_overview():
    """显示用户概览界面"""
    try:
        # 获取统计数据
        stats = get_user_stats()
        
        # 显示关键指标
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总用户数", f"{stats['total_users']:,}")
            st.metric("活跃用户", f"{stats['active_users']:,}")
        with col2:
            st.metric("今日新增", f"{stats['new_users_today']:,}")
            st.metric("总字符量", f"{stats['total_chars']:,}")
        with col3:
            st.metric("总消费金额", f"{stats['total_cost']:.2f} 元")
            
        # 显示用户角色分布
        st.markdown("### 用户角色分布")
        role_df = pd.DataFrame([
            {"角色": role, "数量": count}
            for role, count in stats['role_dist'].items()
        ])
        st.dataframe(role_df, use_container_width=True)
        
        # 显示最近注册用户
        st.markdown("### 最近注册用户")
        recent_users = get_recent_users()
        st.dataframe(recent_users, use_container_width=True)
        
        # 显示用户消费排行
        st.markdown("### 用户消费排行")
        top_users = get_top_users()
        st.dataframe(top_users, use_container_width=True)
        
        add_log("info", "用户概览加载成功")
        
    except Exception as e:
        error_msg = f"加载用户概览失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg) 