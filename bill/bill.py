import streamlit as st
import pandas as pd
from datetime import datetime
from user.user_base import UserManager
from user.logger import add_log
from bill.bill_base import BillManager

# 尝试导入 plotly，如果不可用则不使用图表功能
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    add_log("warning", "Plotly 未安装，将使用基本图表功能")

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
    st.markdown("#### 账户概览")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("当前积分", f"{total['current_points']:,}")
    with col2:
        st.metric("总消费积分", f"{total['total_points_cost']:,}")
    with col3:
        st.metric("总字符数", f"{total['total_chars']:,}")
    
    # 获取积分历史记录
    history_df = bill_mgr.get_points_history(user_info['user_id'])
    
    if not history_df.empty:
        # 添加积分趋势图
        st.markdown("#### 积分趋势")
        try:
            if HAS_PLOTLY:
                # 使用 plotly 绘制更美观的图表
                fig = px.line(history_df, 
                            x='timestamp', 
                            y='balance',
                            title='积分余额变化趋势')
                st.plotly_chart(fig, use_container_width=True)
            else:
                # 使用 streamlit 的基本图表功能
                history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
                st.line_chart(
                    history_df.set_index('timestamp')['balance'],
                    use_container_width=True
                )
        except Exception as e:
            # 如果绘图出错，记录日志并使用基本图表
            add_log("error", f"绘制积分趋势图失败: {str(e)}")
            st.line_chart(
                history_df.set_index('timestamp')['balance'],
                use_container_width=True
            )
    
    # 获取账单记录
    records = bill_mgr.get_user_bills(user_info['user_id'])
    
    # 显示账单记录
    st.markdown("#### 消费记录")
    if records:
        # 创建基础DataFrame
        df = pd.DataFrame(records, columns=[
            '时间', 'API名称', '操作类型',
            '输入字符数', '输出字符数', '总字符数', '消费积分'
        ])
        
        # 计算积分余额
        # 首先获取所有积分交易记录
        points_df = bill_mgr.get_points_history(user_info['user_id'])
        # 将时间列转换为相同格式以便匹配
        points_df['timestamp'] = pd.to_datetime(points_df['timestamp'])
        df['时间'] = pd.to_datetime(df['时间'])
        
        # 为每条消费记录找到对应的积分余额
        df['积分余额'] = df.apply(
            lambda row: points_df[points_df['timestamp'] <= row['时间']].iloc[0]['balance']
            if not points_df[points_df['timestamp'] <= row['时间']].empty
            else None,
            axis=1
        )
        
        # 格式化显示
        st.dataframe(
            df.style.format({
                '输入字符数': '{:,}',
                '输出字符数': '{:,}',
                '总字符数': '{:,}',
                '消费积分': '{:,}',
                '���分余额': '{:,}'
            }),
            use_container_width=True,
            height=400
        )
    else:
        st.info("暂无账单记录")
    
    # 显示积分获取历史
    st.markdown("#### 积分获取历史")
    if not history_df.empty:
        # 创建一个新的DataFrame只显示积分增加的记录
        rewards_df = history_df[history_df['amount'] > 0].copy()
        
        if not rewards_df.empty:
            # 格式化时间列
            rewards_df['timestamp'] = pd.to_datetime(rewards_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 重命名列
            rewards_df = rewards_df.rename(columns={
                'timestamp': '时间',
                'type': '类型',
                'amount': '获得积分',
                'balance': '积分余额',
                'description': '说明'
            })
            
            # 将类型转换为中文
            type_mapping = {
                'reward': '奖励',
                'daily_login': '每日登录',
                'admin': '管理员操作'
            }
            rewards_df['类型'] = rewards_df['类型'].map(type_mapping)
            
            # 格式化显示
            st.dataframe(
                rewards_df.style.format({
                    '获得积分': '{:,}',
                    '积分余额': '{:,}'
                }),
                use_container_width=True,
                height=300
            )
            
            # 显示积分获取统计
            st.markdown("##### 积分获取统计")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_rewards = rewards_df['获得积分'].sum()
                st.metric("总获得积分", f"{total_rewards:,}")
            
            with col2:
                daily_login_rewards = rewards_df[rewards_df['类型'] == '每日登录']['获得积分'].sum()
                st.metric("登录奖励积分", f"{daily_login_rewards:,}")
            
            with col3:
                other_rewards = total_rewards - daily_login_rewards
                st.metric("其他奖励积分", f"{other_rewards:,}")
        else:
            st.info("暂无积分获取记录")
    else:
        st.info("暂无积分记录")