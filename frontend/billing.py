import streamlit as st
import requests
from datetime import datetime
import pandas as pd

def show_billing():
    """显示账单页面"""
    st.header("账单与配额")
    
    # 创建标签页
    tab1, tab2 = st.tabs(["使用统计", "使用历史"])
    
    with tab1:
        show_usage_stats()
    with tab2:
        show_usage_history()

def show_usage_stats():
    """显示使用统计"""
    try:
        # 获取使用统计
        response = requests.get(
            f"{st.session_state.API_URL}/billing/usage",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        
        if response.status_code == 200:
            stats = response.json()
            
            # 显示统计信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "总输入字符",
                    f"{stats['total_input_chars']:,}"
                )
            
            with col2:
                st.metric(
                    "总输出字符",
                    f"{stats['total_output_chars']:,}"
                )
            
            with col3:
                st.metric(
                    "总费用(USD)",
                    f"${stats['total_cost_usd']:.4f}"
                )
            
            # 显示配额信息
            st.info(f"剩余配额: {stats['remaining_quota']:,} 字符")
            
            # 添加配额按钮
            if st.button("购买配额"):
                st.session_state.show_add_quota = True
                st.rerun()
                
        else:
            st.error(response.json()["detail"])
            
    except Exception as e:
        st.error(f"获取使用统计失败: {str(e)}")

def show_usage_history():
    """显示使用历史"""
    try:
        # 获取使用历史
        response = requests.get(
            f"{st.session_state.API_URL}/billing/history",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        
        if response.status_code == 200:
            history = response.json()
            
            # 转换为DataFrame
            df = pd.DataFrame(history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # 显示数据表格
            st.dataframe(
                df[[
                    'timestamp',
                    'api_name',
                    'input_chars',
                    'output_chars',
                    'cost_usd'
                ]].style.format({
                    'cost_usd': '${:.4f}',
                    'input_chars': '{:,}',
                    'output_chars': '{:,}'
                }),
                use_container_width=True
            )
            
        else:
            st.error(response.json()["detail"])
            
    except Exception as e:
        st.error(f"获取使用历史失败: {str(e)}")

def add_quota_dialog():
    """添加配额对话框"""
    st.subheader("购买配额")
    
    with st.form("add_quota_form"):
        amount = st.number_input(
            "购买数量(字符)",
            min_value=1000,
            step=1000,
            value=10000
        )
        
        # 显示预估费用
        estimated_cost = amount * 0.000002  # $0.002 per 1K chars
        st.info(f"预估费用: ${estimated_cost:.4f}")
        
        submitted = st.form_submit_button("确认购买")
        
        if submitted:
            try:
                response = requests.post(
                    f"{st.session_state.API_URL}/billing/add-quota",
                    headers={"Authorization": f"Bearer {st.session_state.token}"},
                    json={"amount": amount}
                )
                
                if response.status_code == 200:
                    st.success("配额购买成功!")
                    st.session_state.show_add_quota = False
                    st.rerun()
                else:
                    st.error(response.json()["detail"])
                    
            except Exception as e:
                st.error(f"购买配额失败: {str(e)}") 