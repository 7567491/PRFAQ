import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from db.db_admin import get_db_connection
from modules.utils import add_log

def analyze_users():
    """分析用户数据并生成可视化报表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取基础用户数据
        cursor.execute("""
            SELECT u.user_id, u.username, u.role, u.created_at, u.last_login,
                   COUNT(DISTINCT h.id) as history_count,
                   COALESCE(SUM(b.points_change), 0) as total_points
            FROM users u
            LEFT JOIN history h ON u.user_id = h.user_id
            LEFT JOIN bill b ON u.user_id = b.user_id
            GROUP BY u.user_id, u.username, u.role, u.created_at, u.last_login
        """)
        
        users_data = cursor.fetchall()
        
        # 转换为DataFrame
        df = pd.DataFrame(users_data, columns=[
            'user_id', 'username', 'role', 'created_at', 'last_login',
            'history_count', 'total_points'
        ])
        
        # 数据清洗和转换
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['last_login'] = pd.to_datetime(df['last_login'])
        df['days_since_creation'] = (datetime.now() - df['created_at']).dt.days
        df['days_since_last_login'] = (datetime.now() - df['last_login']).dt.days
        
        # 显示基础统计信息
        st.subheader("用户基础统计")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总用户数", len(df))
        with col2:
            st.metric("活跃用户数", len(df[df['days_since_last_login'] <= 7]))
        with col3:
            st.metric("总积分消耗", f"{int(df['total_points'].sum()):,}")
        with col4:
            st.metric("平均每用户操作次数", f"{df['history_count'].mean():.1f}")
        
        # 用户角色分布
        st.subheader("用户角色分布")
        role_counts = df['role'].value_counts()
        fig_roles = px.pie(values=role_counts.values, 
                          names=role_counts.index,
                          title="用户角色分布")
        st.plotly_chart(fig_roles)
        
        # 用户增长趋势
        st.subheader("用户增长趋势")
        df_growth = df.groupby(df['created_at'].dt.date).size().reset_index()
        df_growth.columns = ['date', 'new_users']
        df_growth['cumulative_users'] = df_growth['new_users'].cumsum()
        
        fig_growth = px.line(df_growth, 
                           x='date', 
                           y='cumulative_users',
                           title="用户累计增长趋势")
        st.plotly_chart(fig_growth)
        
        # 用户活跃度分析
        st.subheader("用户活跃度分析")
        activity_bins = [0, 7, 30, 90, float('inf')]
        activity_labels = ['最近7天', '最近30天', '最近90天', '90天以上']
        df['activity_group'] = pd.cut(df['days_since_last_login'], 
                                    bins=activity_bins, 
                                    labels=activity_labels)
        
        activity_counts = df['activity_group'].value_counts()
        fig_activity = px.bar(x=activity_counts.index, 
                            y=activity_counts.values,
                            title="用户活跃度分布")
        st.plotly_chart(fig_activity)
        
        # 用户操作频率分析
        st.subheader("用户操作频率分析")
        fig_usage = px.histogram(df, 
                               x='history_count',
                               title="用户操作次数分布",
                               nbins=20)
        st.plotly_chart(fig_usage)
        
        # 积分消耗分析
        st.subheader("积分消耗分析")
        fig_points = px.box(df, 
                          y='total_points',
                          title="用户积分消耗分布")
        st.plotly_chart(fig_points)
        
        # 详细数据表格
        st.subheader("用户详细数据")
        st.dataframe(df[[
            'username', 'role', 'history_count', 'total_points',
            'days_since_creation', 'days_since_last_login'
        ]].sort_values('history_count', ascending=False))
        
        add_log("info", "用户分析报表生成成功")
        
    except Exception as e:
        st.error(f"生成用户分析报表时出错: {str(e)}")
        add_log("error", f"生成用户分析报表失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

def show_user_analysis():
    """显示用户分析面板"""
    st.title("用户数据分析")
    
    st.markdown("""
    此面板提供了详细的用户数据分析，包括：
    - 用户基础统计
    - 用户角色分布
    - 用户增长趋势
    - 用户活跃度分析
    - 用户操作频率分析
    - 积分消耗分析
    """)
    
    if st.button("生成分析报表"):
        analyze_users() 