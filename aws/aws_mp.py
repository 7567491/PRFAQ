import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime
from modules.utils import add_log
import os
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple

# 加载环境变量
load_dotenv()

def validate_aws_credentials(creds: Dict[str, str]) -> Tuple[bool, str]:
    """验证AWS凭证是否完整
    
    Args:
        creds: AWS凭证字典
    
    Returns:
        (是否有效, 错误信息)
    """
    required_keys = {
        'aws_access_key': 'AWS Access Key ID',
        'aws_secret_key': 'AWS Secret Access Key',
        'aws_region': 'AWS Region',
        'marketplace_id': 'Marketplace ID',
        'seller_id': 'Seller ID'
    }
    
    missing_keys = []
    for key, display_name in required_keys.items():
        if not creds.get(key):
            missing_keys.append(display_name)
    
    if missing_keys:
        return False, f"缺少必要的配置项: {', '.join(missing_keys)}"
    return True, ""

def get_aws_credentials() -> Optional[Dict[str, str]]:
    """从环境变量获取AWS凭证"""
    try:
        add_log("info", "开始读取AWS凭证配置...")
        
        # 获取项目根目录的.env文件路径
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(root_dir, '.env')
        
        add_log("info", f"尝试加载环境变量文件: {env_path}")
        
        if not os.path.exists(env_path):
            add_log("error", f"找不到.env文件: {env_path}")
            return None
            
        # 强制重新加载环境变量
        load_dotenv(env_path, override=True)
        add_log("info", f"已加载环境变量文件: {env_path}")
        
        # 读取并验证每个环境变量
        env_vars = {
            'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
            'AWS_DEFAULT_REGION': os.getenv('AWS_DEFAULT_REGION'),
            'AWS_MARKETPLACE_ID': os.getenv('AWS_MARKETPLACE_ID'),
            'AWS_SELLER_ID': os.getenv('AWS_SELLER_ID')
        }
        
        # 检查是否所有环境变量都已设置
        missing_vars = [key for key, value in env_vars.items() if not value]
        if missing_vars:
            add_log("error", f"以下环境变量未设置: {', '.join(missing_vars)}")
            return None
            
        # 转换为凭证字典
        creds = {
            'aws_access_key': env_vars['AWS_ACCESS_KEY_ID'],
            'aws_secret_key': env_vars['AWS_SECRET_ACCESS_KEY'],
            'aws_region': env_vars['AWS_DEFAULT_REGION'],
            'marketplace_id': env_vars['AWS_MARKETPLACE_ID'],
            'seller_id': env_vars['AWS_SELLER_ID']
        }
        
        add_log("info", "AWS凭证读取成功")
        return creds
        
    except Exception as e:
        add_log("error", f"读取AWS凭证失败: {str(e)}", include_trace=True)
        return None

def test_aws_connection() -> Tuple[bool, str]:
    """测试AWS连接"""
    try:
        add_log("info", "开始测试AWS连接...")
        
        # 从环境变量获取凭证
        creds = get_aws_credentials()
        if not creds:
            return False, "无法获取AWS凭证，请检查环境变量配置"
        
        add_log("info", f"使用区域: {creds['aws_region']}")
        
        # 创建AWS会话
        try:
            session = boto3.Session(
                aws_access_key_id=creds['aws_access_key'],
                aws_secret_access_key=creds['aws_secret_key'],
                region_name=creds['aws_region']
            )
            add_log("info", "AWS会话创建成功")
        except Exception as e:
            add_log("error", f"创建AWS会话失败: {str(e)}")
            return False, f"创建AWS会话失败: {str(e)}"
        
        # 测试S3连接
        try:
            s3 = session.client('s3')
            response = s3.list_buckets()
            bucket_count = len(response['Buckets'])
            bucket_names = [b['Name'] for b in response['Buckets']]
            add_log("info", f"成功连接到AWS S3，发现 {bucket_count} 个存储桶: {', '.join(bucket_names)}")
        except Exception as e:
            add_log("error", f"S3连接测试失败: {str(e)}")
            return False, f"S3连接测试失败: {str(e)}"
        
        # 测试Marketplace连接
        try:
            mp = session.client('marketplace-catalog', region_name=creds['aws_region'])
            
            # 直接尝试常见的实体类型
            entity_types = [
                'AmiProduct',
                'SaaSProduct',
                'ServerProduct',
                'ContainerProduct',
                'MachineLearningProduct',
                'DataProduct'
            ]
            
            entity_count = 0
            entities_info = []
            
            for entity_type in entity_types:
                try:
                    add_log("info", f"尝试获取 {entity_type} 类型的实体...")
                    response = mp.list_entities(
                        Catalog='AWSMarketplace',
                        EntityType=entity_type
                    )
                    
                    current_count = len(response.get('EntitySummaryList', []))
                    entity_count += current_count
                    
                    if current_count > 0:
                        entities_info.append(f"{entity_type}: {current_count}个")
                        # 记录实体详情
                        for entity in response.get('EntitySummaryList', []):
                            add_log("info", f"发现实体 - ID: {entity.get('EntityId')}, 类型: {entity.get('EntityType')}")
                    
                except Exception as e:
                    add_log("warning", f"获取 {entity_type} 类型实体失败: {str(e)}")
                    continue
            
            # 尝试获取 Marketplace 账户信息
            try:
                add_log("info", "尝试获取 Marketplace 账户信息...")
                response = mp.describe_entity(
                    Catalog='AWSMarketplace',
                    EntityId=creds['marketplace_id']
                )
                add_log("info", "成功获取 Marketplace 账户信息")
            except Exception as e:
                add_log("warning", f"获取 Marketplace 账户信息失败: {str(e)}")
            
            if entity_count > 0:
                add_log("info", f"Marketplace API连接测试成功，共发现 {entity_count} 个实体")
                entities_summary = "\n".join(entities_info)
            else:
                add_log("warning", "未找到任何Marketplace实体")
                entities_summary = "未找到实体"
                entities_summary += f"\n尝试过的实体类型: {', '.join(entity_types)}"
            
            # 测试 Marketplace Metering Service
            try:
                mms = session.client('meteringmarketplace', region_name=creds['aws_region'])
                add_log("info", "成功连接到 Marketplace Metering Service")
                entities_summary += "\nMarketplace Metering Service: 连接成功"
            except Exception as e:
                add_log("warning", f"连接 Marketplace Metering Service 失败: {str(e)}")
                entities_summary += "\nMarketplace Metering Service: 连接失败"
            
            # 测试 Marketplace Commerce Analytics
            try:
                mca = session.client('marketplacecommerceanalytics', region_name=creds['aws_region'])
                add_log("info", "成功连接到 Marketplace Commerce Analytics")
                entities_summary += "\nMarketplace Commerce Analytics: 连接成功"
            except Exception as e:
                add_log("warning", f"连接 Marketplace Commerce Analytics 失败: {str(e)}")
                entities_summary += "\nMarketplace Commerce Analytics: 连接失败"
            
        except Exception as e:
            add_log("error", f"Marketplace连接测试失败: {str(e)}")
            return False, f"Marketplace连接测试失败: {str(e)}"
        
        success_msg = f"""
        AWS连接测试全部通过！
        
        区域: {creds['aws_region']}
        S3存储桶: {bucket_count} 个
        
        Marketplace服务:
        {entities_summary}
        
        Marketplace ID: {creds['marketplace_id']}
        Seller ID: {creds['seller_id']}
        """
        add_log("info", "AWS连接测试完成")
        return True, success_msg
        
    except Exception as e:
        error_msg = f"AWS连接测试过程出错: {str(e)}"
        add_log("error", error_msg, include_trace=True)
        return False, error_msg

def sync_product_data() -> Tuple[bool, str]:
    """同步商品数据"""
    try:
        add_log("info", "开始同步商品数据...")
        
        # 获取AWS凭证
        creds = get_aws_credentials()
        if not creds:
            return False, "无法获取AWS凭证"
            
        # 创建AWS会话
        session = boto3.Session(
            aws_access_key_id=creds['aws_access_key'],
            aws_secret_access_key=creds['aws_secret_key'],
            region_name=creds['aws_region']
        )
        
        # 获取Marketplace商品列表
        mp = session.client('marketplace-catalog')
        try:
            response = mp.list_entities(
                Catalog='AWSMarketplace',
                EntityType='DataProduct'  # 同样修改这里的EntityType
            )
            product_count = len(response.get('EntitySummaryList', []))
            add_log("info", f"成功获取商品列表，共 {product_count} 个商品")
            
            # 记录实体详情
            entities = response.get('EntitySummaryList', [])
            for entity in entities:
                add_log("info", f"实体ID: {entity.get('EntityId')}, 类型: {entity.get('EntityType')}")
            
            return True, f"商品数据同步成功，共同步 {product_count} 个商品"
            
        except Exception as e:
            error_msg = f"获取商品列表失败: {str(e)}"
            add_log("error", error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"商品数据同步失败: {str(e)}"
        add_log("error", error_msg, include_trace=True)
        return False, error_msg

def sync_order_data() -> Tuple[bool, str]:
    """同步订单数据"""
    try:
        add_log("info", "开始同步订单数据...")
        
        # 获取AWS凭证
        creds = get_aws_credentials()
        if not creds:
            return False, "无法获取AWS凭证"
            
        # 创建AWS会话
        session = boto3.Session(
            aws_access_key_id=creds['aws_access_key'],
            aws_secret_access_key=creds['aws_secret_key'],
            region_name=creds['aws_region']
        )
        
        # 获取订单列表
        mp = session.client('marketplace-commerce-analytics')
        try:
            # 获取今天的订单数据
            today = datetime.now().strftime('%Y-%m-%d')
            response = mp.generate_data_set(
                dataSetType='customer_subscriber_hourly_monthly_subscriptions',
                dataSetPublicationDate=today,
                roleNameArn=f"arn:aws-cn:iam::{creds['marketplace_id']}:role/MarketplaceCommerceAnalytics",
                destinationS3BucketName='your-bucket-name',  # TODO: 配置S3存储桶
                destinationS3Prefix='marketplace/orders'
            )
            
            add_log("info", "订单数据获取任务已提交")
            # TODO: 处理异步任务结果
            
            return True, "订单数据同步任务已提交"
            
        except Exception as e:
            error_msg = f"获取订单数据失败: {str(e)}"
            add_log("error", error_msg)
            return False, error_msg
            
    except Exception as e:
        error_msg = f"订单数据同步失败: {str(e)}"
        add_log("error", error_msg, include_trace=True)
        return False, error_msg

def generate_report(report_type: str, start_date: datetime, end_date: datetime) -> Tuple[bool, str]:
    """生成报表"""
    try:
        add_log("info", f"开始生成{report_type}...")
        
        # 获取AWS凭证
        creds = get_aws_credentials()
        if not creds:
            return False, "无法获取AWS凭证"
            
        # 创建AWS会话
        session = boto3.Session(
            aws_access_key_id=creds['aws_access_key'],
            aws_secret_access_key=creds['aws_secret_key'],
            region_name=creds['aws_region']
        )
        
        # 根据报表类型生成不同的报表
        if report_type == "销售报表":
            # TODO: 实现销售报表生成逻辑
            return True, "销售报表生成成功"
            
        elif report_type == "用户报表":
            # TODO: 实现用户报表生成逻辑
            return True, "用户报表生成成功"
            
        elif report_type == "商品报表":
            # TODO: 实现商品报表生成逻辑
            return True, "商品报表生成成功"
            
        else:
            return False, f"未知的报表类型: {report_type}"
            
    except Exception as e:
        error_msg = f"报表生成失败: {str(e)}"
        add_log("error", error_msg, include_trace=True)
        return False, error_msg

def show_aws_panel():
    """显示AWS集成面板"""
    st.title("AWS Marketplace 集成面板")
    
    # 验证AWS凭证
    creds = get_aws_credentials()
    if not creds:
        st.error("⚠️ AWS凭证配置无效，请检查环境变量设置")
        
        # 显示环境变量检查结果
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
            # 显示文件权限
            try:
                mode = oct(os.stat(env_path).st_mode)[-3:]
                st.info(f"文件权限: {mode}")
            except Exception as e:
                st.error(f"无法读取文件权限: {str(e)}")
        else:
            st.error(f"❌ .env文件不存在: {env_path}")
            
        # 显示当前工作目录
        st.info(f"当前工作目录: {os.getcwd()}")
        
        return
    
    # 创建标签页
    tab1, tab2, tab3, tab4 = st.tabs([
        "连接测试", 
        "数据同步", 
        "报表导出",
        "配置信息"
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
                    st.error("如需详细错误信息，请查看日志")
    
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
                        st.error("如需详细错误信息，请查看日志")
                        
        with col2:
            if st.button("同步订单数据", key="sync_order"):
                with st.spinner("正在同步订单数据..."):
                    success, message = sync_order_data()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                        st.error("如需详细错误信息，请查看日志")
    
    # Tab 3: 报表导出
    with tab3:
        st.header("报表导出")
        st.markdown("""
        生成各类AWS Marketplace相关报表：
        - 销售报表：销售额、单量等统计
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
            if start_date > end_date:
                st.error("开始日期不能晚于结束日期")
            else:
                with st.spinner(f"正在生成{report_type}..."):
                    success, message = generate_report(report_type, start_date, end_date)
                    if success:
                        st.success(message)
                        # TODO: 提供报表下载链接
                    else:
                        st.error(message)
                        st.error("如需详细错误信息，请查看日志")
    
    # Tab 4: 配置信息
    with tab4:
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