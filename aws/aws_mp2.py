"""
AWS Marketplace Integration Panel - Additional Features
"""
import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime
from modules.utils import add_log
import os
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple
from .aws_mp import show_aws_panel as show_basic_panel

def show_aws_mp_panel():
    """显示AWS Marketplace集成面板"""
    
    # 创建所有标签页
    tab_basic, tab_mp, tab_customer = st.tabs([
        "基础功能", 
        "Marketplace集成",
        "客户验证"
    ])
    
    # Tab 1: 基础功能(原有功能)
    with tab_basic:
        show_basic_panel()
    
    # Tab 2: Marketplace集成(新功能)
    with tab_mp:
        st.title("AWS Marketplace 集成测试")
        
        # 创建子标签页
        mp_tab1, mp_tab2, mp_tab3, mp_tab4 = st.tabs([
            "连接测试",
            "数据同步",
            "报表导出",
            "配置信息"
        ])
        
        # 验证AWS凭证
        creds = get_aws_credentials()
        if not creds:
            st.error("⚠️ AWS凭证配置无效，请检查环境变量设置")
            show_env_check()
            return
            
        # MP Tab 1: 连接测试
        with mp_tab1:
            show_connection_test(creds)
            
        # MP Tab 2: 数据同步
        with mp_tab2:
            show_data_sync(creds)
            
        # MP Tab 3: 报表导出
        with mp_tab3:
            show_report_generation(creds)
            
        # MP Tab 4: 配置信息
        with mp_tab4:
            show_config_info(creds)
    
    # Tab 3: 客户验证(新功能)
    with tab_customer:
        from .customer import show_customer_panel
        show_customer_panel()

def show_env_check():
    """显示环境变量检查结果"""
    st.subheader("环境变量检查")
    env_vars = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION'),
        'AWS_MARKETPLACE_ID': os.getenv('AWS_MARKETPLACE_ID'),
        'AWS_SELLER_ID': os.getenv('AWS_SELLER_ID')
    }
    
    for key, value in env_vars.items():
        if value:
            if key == 'AWS_SECRET_ACCESS_KEY':
                st.success(f"✅ {key}: ***已设置***")
            else:
                st.success(f"✅ {key}: {value}")
        else:
            st.error(f"❌ {key}: 未设置")
    
    st.info("需要在 .env 文件中配置以下环境变量：")
    st.code("""
    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key
    AWS_DEFAULT_REGION=cn-northwest-1
    AWS_MARKETPLACE_ID=your_marketplace_id
    AWS_SELLER_ID=your_seller_id
    """)
    
    # 显示.env文件检查
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        st.success(f"✅ .env文件存在: {env_path}")
        try:
            mode = oct(os.stat(env_path).st_mode)[-3:]
            st.info(f"文件权限: {mode}")
        except Exception as e:
            st.error(f"无法读取文件权限: {str(e)}")
    else:
        st.error(f"❌ .env文件不存在: {env_path}")
    
    st.info(f"当前工作目录: {os.getcwd()}")

def show_connection_test(creds: Dict[str, str]):
    """显示连接测试界面"""
    st.header("AWS 连接测试")
    st.markdown("""
    此功能用于测试与AWS的连接是否正常。它会：
    1. 验证AWS凭证配置
    2. 测试S3服务连接
    3. 测试Marketplace服务连接
    """)
    
    if st.button("测试连接", key="mp_test_conn"):
        with st.spinner("正在测试连接..."):
            success, message = test_aws_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
                st.error("如需详细错误信息，请查看日志")

def show_data_sync(creds: Dict[str, str]):
    """显示数据同步界面"""
    st.header("数据同步")
    st.markdown("""
    此功能用于同步AWS Marketplace的数据：
    - 商品数据：同步产品列表、价格等信息
    - 订单数据：同步订单状态、支付信息等
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("同步商品数据", key="mp_sync_prod"):
            with st.spinner("正在同步商品数据..."):
                success, message = sync_product_data()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                    st.error("如需详细错误信息，请查看日志")
                    
    with col2:
        if st.button("同步订单数据", key="mp_sync_order"):
            with st.spinner("正在同步订单数据..."):
                success, message = sync_order_data()
                if success:
                    st.success(message)
                else:
                    st.error(message)
                    st.error("如需详细错误信息，请查看日志")

def show_report_generation(creds: Dict[str, str]):
    """显示报表生成界面"""
    st.header("报表导出")
    st.markdown("""
    生成各类AWS Marketplace相关报表：
    - 销售报表：销售额、单量等统计
    - 用户报表：用户数、活跃度等分析
    - 商品报表：商品表现、定价分析等
    """)
    
    report_type = st.selectbox(
        "选择报表类型",
        ["销售报表", "用户报表", "商品报表"],
        key="mp_report_type"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", datetime.now(), key="mp_start_date")
    with col2:
        end_date = st.date_input("结束日期", datetime.now(), key="mp_end_date")
        
    if st.button("生成报表", key="mp_gen_report"):
        if start_date > end_date:
            st.error("开始日期不能晚于结束日期")
        else:
            with st.spinner(f"正在生成{report_type}..."):
                success, message = generate_report(report_type, start_date, end_date)
                if success:
                    st.success(message)
                else:
                    st.error(message)
                    st.error("如需详细错误信息，请查看日志")

def show_config_info(creds: Dict[str, str]):
    """显示配置信息界面"""
    st.header("AWS配置信息")
    st.markdown("""
    当前AWS配置信息（从环境变量读取）：
    """)
    
    # 显示配置信息（隐藏敏感信息）
    st.json({
        "AWS_ACCESS_KEY_ID": f"{creds['aws_access_key'][:6]}...{creds['aws_access_key'][-4:]}",
        "AWS_SECRET_ACCESS_KEY": "***************",
        "AWS_DEFAULT_REGION": creds['aws_region'],
        "AWS_MARKETPLACE_ID": creds['marketplace_id'],
        "AWS_SELLER_ID": creds['seller_id']
    })
    
    st.info("配置信息已从环境变量加载。如需修改，请更新 .env 文件。")
    
    # 显示环境检查结果
    st.subheader("环境检查")
    
    env_checks = {
        "Python版本": f"{os.sys.version}",
        "Boto3版本": f"{boto3.__version__}",
        "工作目录": f"{os.getcwd()}",
        ".env文件": "存在" if os.path.exists(".env") else "不存在",
        "AWS凭证验证": "通过" if all(creds.values()) else "未通过"
    }
    
    for check_name, check_result in env_checks.items():
        st.text(f"{check_name}: {check_result}")

# 从原有文件导入其他必要的函数
from .aws_mp import (
    get_aws_credentials,
    test_aws_connection,
    sync_product_data,
    sync_order_data,
    generate_report
) 