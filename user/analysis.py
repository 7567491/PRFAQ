import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
from user.user_base import UserManager
from bill.bill import BillManager
import numpy as np

class UserAnalytics:
    def __init__(self):
        self.db_path = 'db/users.db'
        self.user_mgr = UserManager()
        self.bill_mgr = BillManager()
        
    def get_user_growth_data(self):
        """获取用户增长数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT DATE(created_at) as date, COUNT(*) as new_users
                FROM users
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn)
            
            # 计算累计用户数
            df['total_users'] = df['new_users'].cumsum()
            
            conn.close()
            return df
        except Exception as e:
            st.error(f"获取用户增长数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_user_activity_data(self, days=30):
        """获取用户活跃度数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 获取最近n天的登录数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = pd.read_sql_query("""
                SELECT DATE(last_login) as date, COUNT(DISTINCT username) as active_users
                FROM users
                WHERE DATE(last_login) >= DATE(?)
                GROUP BY DATE(last_login)
                ORDER BY date
            """, conn, params=(start_date.strftime('%Y-%m-%d'),))
            
            conn.close()
            return df
        except Exception as e:
            st.error(f"获取用户活跃度数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_feature_usage_data(self):
        """获取功能使用情况数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT type as feature, COUNT(*) as usage_count
                FROM history
                GROUP BY type
                ORDER BY usage_count DESC
            """, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"获取功能使用数据失败: {str(e)}")
            return pd.DataFrame()
            
    def get_user_retention_data(self):
        """获取用户留存数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 获取用户首次使用日期和最后使用日期
            df = pd.read_sql_query("""
                SELECT 
                    username,
                    DATE(created_at) as first_use,
                    DATE(last_login) as last_use
                FROM users
                WHERE last_login IS NOT NULL
            """, conn)
            
            # 计算使用天数
            df['days_retained'] = (pd.to_datetime(df['last_use']) - 
                                 pd.to_datetime(df['first_use'])).dt.days
            
            conn.close()
            return df
        except Exception as e:
            st.error(f"获取用户留存数据失败: {str(e)}")
            return pd.DataFrame()

def show_user_analytics():
    """显示用户分析界面"""
    st.title("用户分析面板")
    
    analytics = UserAnalytics()
    
    # 创建四个关键指标卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_users = len(analytics.user_mgr.list_users())
        st.metric("总用户数", f"{total_users:,}")
        
    with col2:
        active_users = len(analytics.get_user_activity_data(days=7))
        st.metric("近7天活跃用户", f"{active_users:,}")
        
    with col3:
        retention_data = analytics.get_user_retention_data()
        avg_retention = retention_data['days_retained'].mean()
        st.metric("平均使用天数", f"{avg_retention:.1f}")
        
    with col4:
        feature_data = analytics.get_feature_usage_data()
        total_usage = feature_data['usage_count'].sum()
        st.metric("总使用次数", f"{total_usage:,}")
    
    # 用户增长趋势
    st.subheader("用户增长趋势")
    growth_data = analytics.get_user_growth_data()
    if not growth_data.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=growth_data['date'],
            y=growth_data['total_users'],
            name='累计用户数',
            line=dict(color='#1f77b4')
        ))
        fig.add_trace(go.Bar(
            x=growth_data['date'],
            y=growth_data['new_users'],
            name='新增用户数',
            marker_color='#2ca02c'
        ))
        fig.update_layout(
            title='用户增长趋势',
            xaxis_title='日期',
            yaxis_title='用户数',
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 功能使用分布
    st.subheader("功能使用分布")
    feature_data = analytics.get_feature_usage_data()
    if not feature_data.empty:
        fig = px.pie(
            feature_data,
            values='usage_count',
            names='feature',
            title='功能使用分布'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 用户活跃度热力图
    st.subheader("用户活跃度分析")
    activity_data = analytics.get_user_activity_data()
    if not activity_data.empty:
        fig = px.line(
            activity_data,
            x='date',
            y='active_users',
            title='每日活跃用户数'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 用户留存分析
    st.subheader("用户留存分析")
    retention_data = analytics.get_user_retention_data()
    if not retention_data.empty:
        retention_bins = [0, 1, 7, 30, 90, float('inf')]
        retention_labels = ['1天', '2-7天', '8-30天', '31-90天', '90天以上']
        retention_data['retention_group'] = pd.cut(
            retention_data['days_retained'],
            bins=retention_bins,
            labels=retention_labels,
            right=False
        )
        retention_summary = retention_data['retention_group'].value_counts()
        
        fig = px.bar(
            x=retention_summary.index,
            y=retention_summary.values,
            title='用户留存分布',
            labels={'x': '使用时长', 'y': '用户数'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 用户行为分析
    st.subheader("用户行为分析")
    col1, col2 = st.columns(2)
    
    with col1:
        # 每日平均使用时长
        conn = sqlite3.connect(analytics.db_path)
        usage_data = pd.read_sql_query("""
            SELECT DATE(timestamp) as date,
                   COUNT(*) as action_count
            FROM history
            GROUP BY DATE(timestamp)
            ORDER BY date
        """, conn)
        
        if not usage_data.empty:
            fig = px.line(
                usage_data,
                x='date',
                y='action_count',
                title='每日系统使用频次'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 用户积分分布
        users = analytics.user_mgr.list_users()
        points_data = []
        for user in users:
            points = analytics.bill_mgr.get_user_points(user['user_id'])
            points_data.append({
                'username': user['username'],
                'points': points
            })
        
        points_df = pd.DataFrame(points_data)
        if not points_df.empty:
            fig = px.histogram(
                points_df,
                x='points',
                title='用户积分分布',
                nbins=20
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 系统使用时间分布
    st.subheader("系统使用时间分布")
    conn = sqlite3.connect(analytics.db_path)
    time_data = pd.read_sql_query("""
        SELECT strftime('%H', timestamp) as hour,
               COUNT(*) as action_count
        FROM history
        GROUP BY hour
        ORDER BY hour
    """, conn)
    
    if not time_data.empty:
        fig = px.bar(
            time_data,
            x='hour',
            y='action_count',
            title='系统使用时间分布',
            labels={'hour': '小时', 'action_count': '操作次数'}
        )
        st.plotly_chart(fig, use_container_width=True) 