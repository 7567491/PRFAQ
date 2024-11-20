"""
AWS Marketplace 用户分析模块
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.utils import add_log
import sqlite3
import traceback

def get_mp_user_stats():
    """获取MP用户统计信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        
        add_log("info", "开始获取MP用户统计信息")
        
        # 先获取aws_customers表的基本统计
        c.execute("""
            SELECT 
                COUNT(*) as total_customers,
                SUM(CASE WHEN subscription_status = 1 THEN 1 ELSE 0 END) as active_subscriptions,
                COUNT(DISTINCT user_id) as linked_users
            FROM aws_customers
        """)
        customers_stats = c.fetchone()
        total_customers, active_subscriptions, linked_users = customers_stats
        add_log("info", f"AWS客户总数: {total_customers}, 活跃订阅: {active_subscriptions}, 关联用户: {linked_users}")
        
        # 获取订阅统计
        c.execute("""
            SELECT 
                subscription_status,
                COUNT(*) as count
            FROM aws_customers
            GROUP BY subscription_status
        """)
        subscription_stats = {
            '已订阅' if status == 1 else '未订阅': count 
            for status, count in c.fetchall()
        }
        add_log("info", f"订阅状态统计: {subscription_stats}")
        
        # 获取AWS MP用户的消费统计
        c.execute("""
            SELECT 
                SUM(u.total_cost) as total_cost,
                SUM(u.total_chars) as total_chars,
                COUNT(DISTINCT CASE WHEN u.is_active = 1 THEN u.user_id END) as active_users
            FROM users u
            JOIN aws_customers ac ON u.user_id = ac.user_id
        """)
        usage_stats = c.fetchone()
        total_cost, total_chars, active_users = usage_stats
        add_log("info", f"消费统计 - 总成本: {total_cost}, 总字符: {total_chars}, 活跃用户: {active_users}")
        
        conn.close()
        
        return {
            'total_users': total_customers,
            'active_users': active_users or 0,
            'subscription_stats': subscription_stats,
            'total_cost': total_cost or 0,
            'total_chars': total_chars or 0,
            'active_subscriptions': active_subscriptions or 0
        }
    except Exception as e:
        error_msg = f"获取MP用户统计失败: {str(e)}\n{traceback.format_exc()}"
        add_log("error", error_msg)
        raise

def get_subscription_trends(days: int = 30):
    """获取订阅趋势数据"""
    try:
        add_log("info", f"开始获取订阅趋势数据, 时间范围: {days}天")
        conn = sqlite3.connect('db/users.db')
        
        # 使用aws_subscriptions表的实际数据
        query = f"""
            WITH RECURSIVE dates(date) AS (
                SELECT date('now', '-{days} days')
                UNION ALL
                SELECT date(date, '+1 day')
                FROM dates
                WHERE date < date('now')
            )
            SELECT 
                dates.date,
                COUNT(DISTINCT ac.aws_customer_id) as active_customers,
                COUNT(DISTINCT s.id) as active_subscriptions
            FROM dates
            LEFT JOIN aws_customers ac ON ac.subscription_status = 1
            LEFT JOIN aws_subscriptions s ON s.aws_customer_id = ac.aws_customer_id
                AND date(s.valid_from) <= dates.date 
                AND (s.valid_to IS NULL OR date(s.valid_to) >= dates.date)
            GROUP BY dates.date
            ORDER BY dates.date
        """
        add_log("info", f"执行订阅趋势查询: {query}")
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        df['date'] = pd.to_datetime(df['date'])
        add_log("info", f"获取到 {len(df)} 条订阅趋势数据")
        return df
    except Exception as e:
        error_msg = f"获取订阅趋势失败: {str(e)}\n{traceback.format_exc()}"
        add_log("error", error_msg)
        raise

def get_notification_analysis():
    """获取通知分析数据"""
    try:
        add_log("info", "开始获取通知分析数据")
        conn = sqlite3.connect('db/users.db')
        
        # 通知类型分布
        type_query = """
            SELECT 
                notification_type,
                COUNT(*) as count,
                SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count,
                COUNT(DISTINCT aws_customer_id) as unique_customers
            FROM aws_notifications
            GROUP BY notification_type
            ORDER BY count DESC
        """
        add_log("info", f"执行通知类型查询: {type_query}")
        type_df = pd.read_sql_query(type_query, conn)
        
        # 通知处理时间分析
        time_query = """
            SELECT 
                notification_type,
                COUNT(*) as total_notifications,
                SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_count,
                AVG(CASE 
                    WHEN processed = 1 AND processed_at IS NOT NULL 
                    THEN CAST(
                        (JULIANDAY(processed_at) - JULIANDAY(created_at)) * 24 * 60 
                        AS INTEGER)
                    END) as avg_process_minutes
            FROM aws_notifications
            GROUP BY notification_type
            HAVING processed_count > 0
        """
        add_log("info", f"执行处理时间查询: {time_query}")
        time_df = pd.read_sql_query(time_query, conn)
        
        conn.close()
        add_log("info", f"获取到 {len(type_df)} 种通知类型, {len(time_df)} 条处理时间记录")
        return type_df, time_df
    except Exception as e:
        error_msg = f"获取通知分析失败: {str(e)}\n{traceback.format_exc()}"
        add_log("error", error_msg)
        raise

def show_mp_analysis():
    """显示MP用户分析界面"""
    try:
        st.markdown("### AWS Marketplace 用户分析")
        add_log("info", "开始加载MP分析页面")
        
        # 获取统计数据
        stats = get_mp_user_stats()
        
        # 显示关键指标
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("MP客户总数", f"{stats['total_users']:,}")
            st.metric("活跃订阅数", f"{stats['active_subscriptions']:,}")
        with col2:
            st.metric("活跃用户数", f"{stats['active_users']:,}")
            active_rate = (stats['active_users'] / stats['total_users'] * 100 
                         if stats['total_users'] > 0 else 0)
            st.metric("活跃率", f"{active_rate:.1f}%")
        with col3:
            st.metric("总消费金额", f"¥{stats['total_cost']:.2f}")
            arpu = (stats['total_cost'] / stats['active_users'] 
                   if stats['active_users'] > 0 else 0)
            st.metric("ARPU", f"¥{arpu:.2f}")
        
        # 订阅状态分布
        st.markdown("### 订阅状态分布")
        subscription_df = pd.DataFrame([
            {"状态": status, "数量": count}
            for status, count in stats['subscription_stats'].items()
        ])
        if not subscription_df.empty:
            fig_subscription = px.pie(
                subscription_df, 
                values='数量', 
                names='状态',
                title='订阅状态分布'
            )
            st.plotly_chart(fig_subscription, use_container_width=True)
        
        # 订阅趋势分析
        st.markdown("### 订阅趋势分析")
        days = st.slider(
            "选择分析时间范围（天）",
            min_value=7,
            max_value=90,
            value=30,
            key="subscription_trend_days"
        )
        
        trends_df = get_subscription_trends(days)
        if not trends_df.empty:
            fig_trends = px.line(
                trends_df, 
                x='date', 
                y=['active_customers', 'active_subscriptions'],
                title='订阅趋势分析',
                labels={
                    'date': '日期',
                    'active_customers': '活跃客户数',
                    'active_subscriptions': '活跃订阅数'
                }
            )
            st.plotly_chart(fig_trends, use_container_width=True)
        
        # 通知分析
        st.markdown("### 通知分析")
        type_df, time_df = get_notification_analysis()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not type_df.empty:
                fig_types = px.pie(
                    type_df, 
                    values='count', 
                    names='notification_type',
                    title='通知类型分布'
                )
                st.plotly_chart(fig_types, use_container_width=True)
            else:
                st.info("暂无通知类型数据")
        
        with col2:
            if not type_df.empty:
                type_df['处理率'] = (type_df['processed_count'] / type_df['count'] * 100)
                fig_process = px.bar(
                    type_df,
                    x='notification_type',
                    y='处理率',
                    title='通知处理率分析',
                    labels={'notification_type': '通知类型', '处理率': '处理率(%)'}
                )
                st.plotly_chart(fig_process, use_container_width=True)
            else:
                st.info("暂无处理率数据")
        
        # 处理时间分析
        if not time_df.empty:
            st.markdown("### 通知处理时间分析")
            fig_time = px.bar(
                time_df,
                x='notification_type',
                y='avg_process_minutes',
                title='平均处理时间(分钟)',
                labels={
                    'notification_type': '通知类型',
                    'avg_process_minutes': '平均处理时间(分钟)'
                }
            )
            st.plotly_chart(fig_time, use_container_width=True)
            
            # 显示详细统计
            st.markdown("#### 通知处理详情")
            detail_df = time_df.copy()
            detail_df['处理率'] = (detail_df['processed_count'] / detail_df['total_notifications'] * 100)
            detail_df.columns = ['通知类型', '总数', '已处理', '平均处理时间(分钟)', '处理率(%)']
            st.dataframe(detail_df, use_container_width=True)
        else:
            st.info("暂无处理时间数据")
        
        add_log("info", "MP分析页面加载成功")
        
    except Exception as e:
        error_msg = f"加载MP分析页面失败: {str(e)}\n{traceback.format_exc()}"
        add_log("error", error_msg)
        st.error(error_msg) 