import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from user.user_base import UserManager
from user.logger import add_log
from bill.bill_base import BillManager

# 定义时区
TIMEZONE = pytz.timezone('Asia/Shanghai')

def format_datetime(dt):
    """格式化日期时间，确保使用正确的时区"""
    try:
        if isinstance(dt, str):
            # 尝试解析字符串日期
            dt = pd.to_datetime(dt, format='mixed', errors='coerce')
        if pd.isna(dt):
            return None
        
        # 如果时间没有时区信息，假定为UTC并转换到东八区
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt).astimezone(TIMEZONE)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        add_log("error", f"日期格式化失败: {str(e)}")
        return None

def show_bill_detail():
    """显示账单明细页面"""
    try:
        st.markdown("### 账单明细")
        
        # 获取当前用户信息
        user_mgr = UserManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        
        if not user_info:
            st.error("获取用户信息失败")
            return
        
        # 创建账单管理器实例
        bill_mgr = BillManager()
        
        try:
            # 获取用户总使用量
            total = bill_mgr.get_user_total_usage(user_info['user_id'])
            
            # 显示总账单
            st.markdown("#### 账户概览")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("当前积分", f"{total.get('current_points', 0):,}")
            with col2:
                st.metric("总消费积分", f"{total.get('total_points_cost', 0):,}")
            with col3:
                st.metric("总字符数", f"{total.get('total_chars', 0):,}")
        except Exception as e:
            add_log("error", f"显示账户概览失败: {str(e)}")
            st.error("显示账户概览时出错")
        
        try:
            # 获取积分历史记录
            history_df = bill_mgr.get_points_history(user_info['user_id'])
            
            if not history_df.empty:
                # 添加积分趋势图
                st.markdown("#### 积分趋势")
                try:
                    # 确保时间列格式正确
                    history_df['timestamp'] = pd.to_datetime(
                        history_df['timestamp'], 
                        format='mixed', 
                        errors='coerce'
                    ).apply(lambda x: x.tz_localize(pytz.UTC).tz_convert(TIMEZONE) if x.tzinfo is None else x)
                    
                    # 移除无效的时间记录
                    history_df = history_df.dropna(subset=['timestamp'])
                    
                    if len(history_df) > 0:
                        try:
                            import plotly.express as px
                            fig = px.line(
                                history_df, 
                                x='timestamp', 
                                y='balance',
                                title='积分余额变化趋势'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except ImportError:
                            st.line_chart(
                                history_df.set_index('timestamp')['balance'],
                                use_container_width=True
                            )
                    else:
                        st.info("暂无有效的积分历史数据")
                except Exception as e:
                    add_log("error", f"绘制积分趋势图失败: {str(e)}")
                    st.error("绘制积分趋势图时出错")
        except Exception as e:
            add_log("error", f"获取积分历史记录失败: {str(e)}")
            st.error("获取积分历史记录时出错")

        # 获取账单记录
        try:
            records = bill_mgr.get_user_bills(user_info['user_id'])
            
            if records:
                try:
                    # 创建基础DataFrame
                    df = pd.DataFrame(records, columns=[
                        '时间', 'API名称', '操作类型',
                        '输入字符数', '输出字符数', '总字符数', '消费积分'
                    ])
                    
                    # 确保数值列为数值类型
                    numeric_columns = ['输入字符数', '输出字符数', '总字符数', '消费积分']
                    for col in numeric_columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        # 将 NaN 值替换为 0
                        df[col] = df[col].fillna(0)
                    
                    try:
                        # 计算积分余额
                        points_df = bill_mgr.get_points_history(user_info['user_id'])
                        if not points_df.empty:
                            # 将时间列转换为相同格式以便匹配
                            try:
                                points_df['timestamp'] = pd.to_datetime(
                                    points_df['timestamp'],
                                    format='mixed',
                                    errors='coerce'
                                )
                                df['时间'] = pd.to_datetime(
                                    df['时间'],
                                    format='mixed',
                                    errors='coerce'
                                )
                                
                                # 移除无效的时间记录
                                points_df = points_df.dropna(subset=['timestamp'])
                                df = df.dropna(subset=['时间'])
                                
                                if not df.empty and not points_df.empty:
                                    # 为每条消费记录找到对应的积分余额
                                    df['积分余额'] = df.apply(
                                        lambda row: points_df[
                                            points_df['timestamp'] <= row['时间']
                                        ]['balance'].iloc[0]
                                        if not points_df[
                                            points_df['timestamp'] <= row['时间']
                                        ].empty
                                        else None,
                                        axis=1
                                    )
                                    # 将 NaN 值替换为 0
                                    df['积分余额'] = df['积分余额'].fillna(0)
                            except Exception as e:
                                add_log("error", f"处理时间列时出错: {str(e)}")
                                df['积分余额'] = 0
                    except Exception as e:
                        add_log("error", f"计算积分余额时出错: {str(e)}")
                        df['积分余额'] = 0
                    
                    # 格式化显示前的最终检查
                    try:
                        # 确保所有数值列都是数值类型
                        for col in ['输入字符数', '输出字符数', '总字符数', '消费积分', '积分余额']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                        
                        # 格式化显示
                        formatted_df = df.style.format({
                            '输入字符数': '{:,.0f}',
                            '输出字符数': '{:,.0f}',
                            '总字符数': '{:,.0f}',
                            '消费积分': '{:,.0f}',
                            '积分余额': '{:,.0f}'
                        })
                        
                        st.dataframe(
                            formatted_df,
                            use_container_width=True,
                            height=400
                        )
                        
                        # 显示消费统计
                        st.markdown("##### 消费统计")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            total_cost = df['消费积分'].sum()
                            st.metric("总消费积分", f"{total_cost:,.0f}")
                        with col2:
                            total_input = df['输入字符数'].sum()
                            st.metric("总输入字符", f"{total_input:,.0f}")
                        with col3:
                            total_output = df['输出字符数'].sum()
                            st.metric("总输出字符", f"{total_output:,.0f}")
                            
                    except Exception as e:
                        add_log("error", f"格式化显示数据时出错: {str(e)}")
                        st.error("显示数据时出错，请查看日志")
                        # 使用基本显示方式
                        st.dataframe(df)
                        
                except Exception as e:
                    add_log("error", f"处理消费记录数据时出错: {str(e)}")
                    st.error("处理消费记录数据时出错")
                    # 显示原始数据
                    st.write(records)
            else:
                st.info("暂无消费记录")
                
        except Exception as e:
            add_log("error", f"获取消费记录时出错: {str(e)}")
            st.error("获取消费记录时出错，请稍后重试")

        # 显示积分获取历史
        st.markdown("#### 积分获取历史")
        if not history_df.empty:
            # 创建一个新的DataFrame只显示积分增加的记录
            rewards_df = history_df[history_df['amount'] > 0].copy()
            
            if not rewards_df.empty:
                try:
                    # 统一处理时间格式
                    rewards_df['timestamp'] = pd.to_datetime(
                        rewards_df['timestamp'], 
                        format='mixed',  # 使用混合格式解析
                        errors='coerce'  # 错误时返回 NaT
                    ).dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # 移除任何因解析失败产生的 NaT 行
                    rewards_df = rewards_df.dropna(subset=['timestamp'])
                    
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
                except Exception as e:
                    add_log("error", f"处理积分获取历史数据时出错: {str(e)}")
                    st.info("处理积分获取历史数据时出错，请检查日志")
            else:
                st.info("暂无积分获取记录")
        else:
            st.info("暂无积分记录")
    except Exception as e:
        add_log("error", f"显示账单明细页面时出错: {str(e)}")
        st.error("显示账单明细页面时出错")