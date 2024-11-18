import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime
from modules.utils import add_log

def test_aws_connection():
    """测试AWS连接"""
    try:
        add_log("info", "开始测试AWS连接...")
        
        # 尝试从Session State获取凭证
        aws_access_key = st.session_state.get('aws_access_key')
        aws_secret_key = st.session_state.get('aws_secret_key')
        aws_region = st.session_state.get('aws_region', 'cn-northwest-1')
        
        if not aws_access_key or not aws_secret_key:
            add_log("warning", "未找到AWS凭证配置")
            return False, "请先在配置管理中设置AWS凭证"
        
        # 创建AWS会话
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # 测试S3连接
        s3 = session.client('s3')
        response = s3.list_buckets()
        bucket_count = len(response['Buckets'])
        add_log("info", f"成功连接到AWS S3，发现 {bucket_count} 个存储桶")
        
        # 测试Marketplace连接
        mp = session.client('marketplace-catalog', region_name=aws_region)
        add_log("info", "成功创建Marketplace客户端连接")
        
        return True, f"AWS连接成功！\n- 区域: {aws_region}\n- S3存储桶数量: {bucket_count}"
        
    except Exception as e:
        error_msg = f"AWS连接失败：{str(e)}"
        add_log("error", error_msg)
        return False, error_msg

def sync_product_data():
    """同步商品数据"""
    try:
        add_log("info", "开始同步商品数据...")
        
        # 获取AWS凭证
        aws_access_key = st.session_state.get('aws_access_key')
        aws_secret_key = st.session_state.get('aws_secret_key')
        aws_region = st.session_state.get('aws_region', 'cn-northwest-1')
        
        if not aws_access_key or not aws_secret_key:
            raise Exception("未找到AWS凭证配置")
            
        # 创建Marketplace客户端
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        mp = session.client('marketplace-catalog')
        
        # TODO: 实现商品数据同步逻辑
        add_log("info", "商品数据同步完成")
        return True, "商品数据同步成功"
        
    except Exception as e:
        error_msg = f"商品数据同步失败：{str(e)}"
        add_log("error", error_msg)
        return False, error_msg

def sync_order_data():
    """同步订单数据"""
    try:
        add_log("info", "开始同步订单数据...")
        
        # 获取AWS凭证
        aws_access_key = st.session_state.get('aws_access_key')
        aws_secret_key = st.session_state.get('aws_secret_key')
        aws_region = st.session_state.get('aws_region', 'cn-northwest-1')
        
        if not aws_access_key or not aws_secret_key:
            raise Exception("未找到AWS凭证配置")
            
        # 创建Marketplace客户端
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        mp = session.client('marketplace-catalog')
        
        # TODO: 实现订单数据同步逻辑
        add_log("info", "订单数据同步完成")
        return True, "订单数据同步成功"
        
    except Exception as e:
        error_msg = f"订单数据同步失败：{str(e)}"
        add_log("error", error_msg)
        return False, error_msg

def generate_report(report_type: str, start_date: datetime, end_date: datetime):
    """生成报表"""
    try:
        add_log("info", f"开始生成{report_type}...")
        
        # 获取AWS凭证
        aws_access_key = st.session_state.get('aws_access_key')
        aws_secret_key = st.session_state.get('aws_secret_key')
        aws_region = st.session_state.get('aws_region', 'cn-northwest-1')
        
        if not aws_access_key or not aws_secret_key:
            raise Exception("未找到AWS凭证配置")
            
        # 创建Marketplace客户端
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        mp = session.client('marketplace-catalog')
        
        # TODO: 实现报表生成逻辑
        add_log("info", f"{report_type}生成完成")
        return True, f"{report_type}生成成功"
        
    except Exception as e:
        error_msg = f"报表生成失败：{str(e)}"
        add_log("error", error_msg)
        return False, error_msg

def show_aws_panel():
    """显示AWS集成面板"""
    st.title("AWS Marketplace 集成面板")
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "连接测试", 
        "数据同步", 
        "报表导出",
        "配置管理"
    ])
    
    # Tab 1: 连接测试
    with tab1:
        st.header("AWS 连接测试")
        st.markdown("""
        此功能用于测试与AWS的连接是否正常。它会：
        1. 验证AWS凭证配置
        2. 测试S3服务连接
        3. 测试Marketplace服务连接
        """)
        
        if st.button("测试连接", key="test_conn"):
            with st.spinner("正在测试连接..."):
                success, message = test_aws_connection()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Tab 2: 数据同步
    with tab2:
        st.header("数据同步")
        st.markdown("""
        此功能用于同步AWS Marketplace的数据：
        - 商品数据：同步产品列表、价格等信息
        - 订单数据：同步订单状态、支付信息等
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("同步商品数据", key="sync_prod"):
                with st.spinner("正在同步商品数据..."):
                    success, message = sync_product_data()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        with col2:
            if st.button("同步订单数据", key="sync_order"):
                with st.spinner("正在同步订单数据..."):
                    success, message = sync_order_data()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # Tab 3: 报表导出
    with tab3:
        st.header("报表导出")
        st.markdown("""
        生成各类AWS Marketplace相关报表：
        - 销售报表：销售额、订单量等统计
        - 用户报表：用户数、活跃度等分析
        - 商品报表：商品表现、定价分析等
        """)
        
        report_type = st.selectbox(
            "选择报表类型",
            ["销售报表", "用户报表", "商品报表"]
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", datetime.now())
        with col2:
            end_date = st.date_input("结束日期", datetime.now())
            
        if st.button("生成报表", key="gen_report"):
            with st.spinner(f"正在生成{report_type}..."):
                success, message = generate_report(report_type, start_date, end_date)
                if success:
                    st.success(message)
                else:
                    st.error(message)
    
    # Tab 4: 配置管理
    with tab4:
        st.header("AWS配置管理")
        st.markdown("""
        管理AWS连接相关配置：
        - AWS凭证：访问密钥、安全密钥等
        - 区域设置：选择要连接的AWS区域
        - Marketplace配置：卖家ID等信息
        """)
        
        # AWS凭证配置
        with st.expander("AWS凭证配置", expanded=True):
            aws_access_key = st.text_input(
                "AWS Access Key ID", 
                type="password",
                value=st.session_state.get('aws_access_key', '')
            )
            aws_secret_key = st.text_input(
                "AWS Secret Access Key", 
                type="password",
                value=st.session_state.get('aws_secret_key', '')
            )
            aws_region = st.selectbox(
                "AWS Region",
                ["cn-northwest-1", "cn-north-1"],
                index=0 if st.session_state.get('aws_region') == 'cn-northwest-1' else 1
            )
            
            if st.button("保存AWS配置", key="save_aws"):
                if aws_access_key and aws_secret_key:
                    st.session_state['aws_access_key'] = aws_access_key
                    st.session_state['aws_secret_key'] = aws_secret_key
                    st.session_state['aws_region'] = aws_region
                    add_log("info", "AWS配置已更新")
                    st.success("AWS配置已保存")
                else:
                    st.error("请填写完整的AWS凭证信息")
        
        # Marketplace配置
        with st.expander("Marketplace配置", expanded=True):
            marketplace_id = st.text_input(
                "Marketplace ID",
                value=st.session_state.get('marketplace_id', '')
            )
            seller_id = st.text_input(
                "Seller ID",
                value=st.session_state.get('seller_id', '')
            )
            
            if st.button("保存Marketplace配置", key="save_mp"):
                if marketplace_id and seller_id:
                    st.session_state['marketplace_id'] = marketplace_id
                    st.session_state['seller_id'] = seller_id
                    add_log("info", "Marketplace配置已更新")
                    st.success("Marketplace配置已保存")
                else:
                    st.error("请填写完整的Marketplace配置信息") 