import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime, timedelta
from modules.utils import add_log

def get_user_growth():
    """获取用户增长趋势"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            WITH RECURSIVE dates(date) AS (
                SELECT date(MIN(created_at))
                FROM users
                UNION ALL
                SELECT date(date, '+1 day')
                FROM dates
                WHERE date < date('now')
            )
            SELECT 
                dates.date as date,
                COUNT(users.user_id) as new_users,
                SUM(COUNT(users.user_id)) OVER (ORDER BY dates.date) as total_users
            FROM dates
            LEFT JOIN users ON date(users.created_at) = dates.date
            GROUP BY dates.date
            ORDER BY dates.date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        add_log("error", f"获取用户增长趋势失败: {str(e)}")
        raise

def get_usage_stats(days: int = 30):
    """获取使用情况统计"""
    try:
        conn = sqlite3.connect('db/users.db')
        
        # 获取账单数据
        query = f"""
            SELECT 
                date(timestamp) as date,
                COUNT(DISTINCT user_id) as active_users,
                SUM(input_letters + output_letters) as total_chars,
                SUM(total_cost) as daily_cost
            FROM bills
            WHERE date(timestamp) >= date('now', '-{days} days')
            GROUP BY date(timestamp)
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        add_log("error", f"获取使用情况统计失败: {str(e)}")
        raise

def get_user_distribution():
    """获取用户分布统计"""
    try:
        conn = sqlite3.connect('db/users.db')
        
        # 用户角色分布
        role_query = """
            SELECT role, COUNT(*) as count
            FROM users
            GROUP BY role
        """
        role_df = pd.read_sql_query(role_query, conn)
        
        # 用户消费区间分布
        cost_query = """
            SELECT 
                CASE 
                    WHEN total_cost = 0 THEN '未消费'
                    WHEN total_cost < 10 THEN '0-10元'
                    WHEN total_cost < 50 THEN '10-50元'
                    WHEN total_cost < 100 THEN '50-100元'
                    ELSE '100元以上'
                END as cost_range,
                COUNT(*) as count
            FROM users
            GROUP BY cost_range
            ORDER BY 
                CASE cost_range
                    WHEN '未消费' THEN 1
                    WHEN '0-10元' THEN 2
                    WHEN '10-50元' THEN 3
                    WHEN '50-100元' THEN 4
                    ELSE 5
                END
        """
        cost_df = pd.read_sql_query(cost_query, conn)
        
        # 用户积分区间分布
        points_query = """
            SELECT 
                CASE 
                    WHEN points < 100 THEN '0-100'
                    WHEN points < 500 THEN '100-500'
                    WHEN points < 1000 THEN '500-1000'
                    ELSE '1000以上'
                END as points_range,
                COUNT(*) as count
            FROM users
            GROUP BY points_range
            ORDER BY 
                CASE points_range
                    WHEN '0-100' THEN 1
                    WHEN '100-500' THEN 2
                    WHEN '500-1000' THEN 3
                    ELSE 4
                END
        """
        points_df = pd.read_sql_query(points_query, conn)
        
        conn.close()
        return role_df, cost_df, points_df
    except Exception as e:
        add_log("error", f"获取用户分布统计失败: {str(e)}")
        raise

def show_user_analysis():
    """显示用户分析界面"""
    try:
        st.markdown("### 用户增长趋势")
        
        # 用户增长趋势图
        growth_df = get_user_growth()
        fig_growth = px.line(growth_df, x='date', y=['new_users', 'total_users'],
                           labels={'date': '日期', 'value': '用户数', 'variable': '类型'},
                           title='用户增长趋势')
        fig_growth.update_layout(
            xaxis_title="日期",
            yaxis_title="用户数",
            legend_title="指标",
            hovermode='x unified'
        )
        st.plotly_chart(fig_growth, use_container_width=True)
        
        st.markdown("### 使用情况分析")
        # 时间范围选择
        days = st.slider("选择分析时间范围（天）", 7, 90, 30)
        
        usage_df = get_usage_stats(days)
        
        # 日活用户趋势
        fig_dau = px.line(usage_df, x='date', y='active_users',
                         title='日活跃用户趋势')
        fig_dau.update_layout(
            xaxis_title="日期",
            yaxis_title="活跃用户数",
            hovermode='x unified'
        )
        st.plotly_chart(fig_dau, use_container_width=True)
        
        # 字符使用量和消费金额趋势
        col1, col2 = st.columns(2)
        with col1:
            fig_chars = px.line(usage_df, x='date', y='total_chars',
                              title='字符使用量趋势')
            fig_chars.update_layout(
                xaxis_title="日期",
                yaxis_title="字符数",
                hovermode='x unified'
            )
            st.plotly_chart(fig_chars, use_container_width=True)
            
        with col2:
            fig_cost = px.line(usage_df, x='date', y='daily_cost',
                             title='日消费金额趋势')
            fig_cost.update_layout(
                xaxis_title="日期",
                yaxis_title="消费金额（元）",
                hovermode='x unified'
            )
            st.plotly_chart(fig_cost, use_container_width=True)
        
        st.markdown("### 用户分布分析")
        role_df, cost_df, points_df = get_user_distribution()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig_role = px.pie(role_df, values='count', names='role',
                            title='用户角色分布')
            st.plotly_chart(fig_role, use_container_width=True)
            
        with col2:
            fig_cost = px.pie(cost_df, values='count', names='cost_range',
                            title='用户消费区间分布')
            st.plotly_chart(fig_cost, use_container_width=True)
            
        with col3:
            fig_points = px.pie(points_df, values='count', names='points_range',
                              title='用户积分区间分布')
            st.plotly_chart(fig_points, use_container_width=True)
            
        add_log("info", "用户分析页面加载成功")
        
    except Exception as e:
        error_msg = f"加载用户分析失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)