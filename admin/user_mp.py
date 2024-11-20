import streamlit as st
import pandas as pd
import sqlite3
from modules.utils import add_log
from datetime import datetime

def get_mp_users():
    """获取AWS Marketplace用户列表"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            SELECT 
                ac.aws_customer_id,
                ac.customer_identifier,
                ac.aws_account_id,
                ac.product_code,
                ac.subscription_status,
                ac.created_at,
                ac.updated_at,
                u.username,
                u.email,
                u.org_name
            FROM aws_customers ac
            LEFT JOIN users u ON ac.user_id = u.user_id
            ORDER BY ac.created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 重命名列
        df.columns = [
            'AWS客户ID', '客户标识符', 'AWS账户ID', '产品代码', 
            '订阅状态', '创建时间', '更新时间', '用户名', '邮箱', '组织名称'
        ]
        
        # 转换订阅状态
        df['订阅状态'] = df['订阅状态'].map({1: '已订阅', 0: '未订阅'})
        
        return df
    except Exception as e:
        add_log("error", f"获取AWS MP用户列表失败: {str(e)}")
        raise

def get_mp_subscriptions():
    """获取订阅信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            SELECT 
                s.id as subscription_id,
                ac.customer_identifier,
                s.entitlement_value,
                s.dimension_name,
                s.valid_from,
                s.valid_to,
                s.created_at
            FROM aws_subscriptions s
            JOIN aws_customers ac ON s.aws_customer_id = ac.aws_customer_id
            ORDER BY s.created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 重命名列
        df.columns = [
            '订阅ID', '客户标识符', '授权值', '维度名称',
            '生效时间', '到期时间', '创建时间'
        ]
        
        return df
    except Exception as e:
        add_log("error", f"获取订阅信息失败: {str(e)}")
        raise

def get_mp_notifications():
    """获取通知记录"""
    try:
        conn = sqlite3.connect('db/users.db')
        query = """
            SELECT 
                n.id as notification_id,
                ac.customer_identifier,
                n.notification_type,
                n.message,
                n.processed,
                n.created_at,
                n.processed_at
            FROM aws_notifications n
            JOIN aws_customers ac ON n.aws_customer_id = ac.aws_customer_id
            ORDER BY n.created_at DESC
            LIMIT 100
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # 重命名列
        df.columns = [
            '通知ID', '客户标识符', '通知类型', '消息内容',
            '处理状态', '创建时间', '处理时间'
        ]
        
        # 转换处理状态
        df['处理状态'] = df['处理状态'].map({1: '已处理', 0: '未处理'})
        
        return df
    except Exception as e:
        add_log("error", f"获取通知记录失败: {str(e)}")
        raise

def show_mp_users():
    """显示AWS MP用户管理界面"""
    try:
        st.markdown("### AWS Marketplace用户管理")
        
        # 创建三个标签页
        tab1, tab2, tab3 = st.tabs(["用户列表", "订阅信息", "通知记录"])
        
        with tab1:
            st.markdown("#### AWS MP用户列表")
            mp_users = get_mp_users()
            if not mp_users.empty:
                st.dataframe(mp_users, use_container_width=True)
            else:
                st.info("暂无AWS MP用户数据")
        
        with tab2:
            st.markdown("#### 订阅信息")
            subscriptions = get_mp_subscriptions()
            if not subscriptions.empty:
                st.dataframe(subscriptions, use_container_width=True)
            else:
                st.info("暂无订阅信息")
                
            # 订阅统计
            if not subscriptions.empty:
                st.markdown("#### 订阅统计")
                col1, col2 = st.columns(2)
                with col1:
                    # 有效订阅数
                    valid_subs = subscriptions[
                        (subscriptions['到期时间'].isna()) | 
                        (pd.to_datetime(subscriptions['到期时间']) > datetime.now())
                    ]
                    st.metric("有效订阅数", len(valid_subs))
                with col2:
                    # 总订阅数
                    st.metric("历史总订阅数", len(subscriptions))
        
        with tab3:
            st.markdown("#### 通知记录")
            notifications = get_mp_notifications()
            if not notifications.empty:
                # 显示通知类型统计
                notification_stats = notifications['通知类型'].value_counts()
                st.markdown("#### 通知类型统计")
                st.bar_chart(notification_stats)
                
                # 显示通知列表
                st.markdown("#### 最近100条通知")
                st.dataframe(notifications, use_container_width=True)
            else:
                st.info("暂无通知记录")
        
        add_log("info", "AWS MP用户页面加载成功")
        
    except Exception as e:
        error_msg = f"加载AWS MP用户页面失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg) 