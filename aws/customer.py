"""
AWS Marketplace Customer Authentication Module
"""
import streamlit as st
from typing import Dict, Any
from modules.utils import add_log
from .customer_manager import CustomerManager
from .fakecustomer import show_simulation_panel

def show_customer_panel():
    """Display customer authentication panel"""
    st.title("AWS Marketplace 客户验证")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs([
        "Token验证",
        "客户管理",
        "测试模拟"
    ])
    
    # 初始化客户管理器
    try:
        customer_mgr = CustomerManager()
    except Exception as e:
        st.error(f"初始化客户管理器失败: {str(e)}")
        return
        
    # Tab 1: Token验证
    with tab1:
        st.header("客户Token验证")
        st.markdown("""
        此功能用于验证AWS Marketplace客户的注册Token。
        
        处理流程：
        1. 接收客户Token
        2. 验证Token格式
        3. 调用AWS API解析客户信息
        4. 存储客户数据
        """)
        
        token = st.text_input("输入注册Token", type="password")
        
        if st.button("验证Token", key="verify_token"):
            if not token:
                st.error("请输入Token")
                return
                
            try:
                with st.spinner("正在验证Token..."):
                    # 验证Token
                    if not customer_mgr.validate_token(token):
                        st.error("Token格式无效")
                        return
                        
                    # 解析客户信息
                    customer_info = customer_mgr.resolve_customer(token)
                    
                    # 显示客户信息
                    st.success("Token验证成功!")
                    st.json(customer_info)
                    
            except Exception as e:
                st.error(f"Token验证失败: {str(e)}")
                
    # Tab 2: 客户管理
    with tab2:
        st.header("客户信息管理")
        st.markdown("""
        管理AWS Marketplace客户信息：
        - 查看客户信息
        - 更新客户状态
        - 管理订阅关系
        """)
        
        # 模拟用户ID输入
        user_id = st.number_input("输入用户ID", min_value=1, value=1)
        
        if st.button("查询客户信息", key="query_customer"):
            customer_info = customer_mgr.get_customer_info(user_id)
            if customer_info:
                st.success("找到客户信息")
                st.json(customer_info)
            else:
                st.warning("未找到客户信息")
                
    # Tab 3: 测试模拟
    with tab3:
        show_simulation_panel() 