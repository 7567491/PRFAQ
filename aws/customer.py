"""
AWS Marketplace Customer Authentication Module
"""
import streamlit as st
from typing import Dict, Any
from modules.utils import add_log
from .customer_manager import CustomerManager
from .fakecustomer import generate_test_token, simulate_callback
from typing import Optional
import time

def show_customer_panel():
    """显示AWS Marketplace客户验证界面"""
    st.title("AWS Marketplace客户验证")
    
    try:
        customer_mgr = CustomerManager()
        
        # 测试区域
        st.markdown("### 🧪 测试客户验证")
        with st.expander("展开测试功能说明"):
            st.markdown("""
                #### 测试功能说明
                此功能用于测试AWS Marketplace客户注册流程，无需真实的AWS账户。
                
                测试流程：
                1. 生成模拟的注册Token
                2. 模拟AWS Marketplace的URL回调
                3. 验证Token并创建测试用户
                4. 显示测试结果和用户信息
                
                注意：此功能仅用于测试环境，不要在生产环境使用。
            """)
        
        if st.button("开始测试注册流程", key="start_test"):
            try:
                with st.spinner("正在执行测试流程..."):
                    # 创建进度条
                    progress = st.progress(0)
                    
                    # 步骤1: 生成测试token
                    progress.progress(20)
                    st.info("步骤1/4: 生成测试Token")
                    test_token = generate_test_token()
                    time.sleep(1)
                    
                    # 步骤2: 模拟URL回调
                    progress.progress(40)
                    st.info("步骤2/4: 模拟URL回调")
                    callback_result = simulate_callback(test_token)
                    time.sleep(1)
                    
                    # 步骤3: 验证Token
                    progress.progress(60)
                    st.info("步骤3/4: 验证Token")
                    if not customer_mgr.validate_token(test_token):
                        raise ValueError("Token验证失败")
                    time.sleep(1)
                    
                    # 步骤4: 创建测试用户
                    progress.progress(80)
                    st.info("步骤4/4: 创建测试用户")
                    customer_info = customer_mgr.resolve_customer(test_token)
                    progress.progress(100)
                    
                    # 显示测试结果
                    success_message = f"""
                        ✅ 测试完成！
                        
                        测试用户已成功创建：
                        1. 用户名: mp_{customer_info['customer_identifier'][:8]}
                        2. AWS账户: {customer_info['customer_aws_account_id']}
                        3. 产品代码: {customer_info['product_code']}
                        
                        您可以使用以下信息登录系统：
                        - 用户名: mp_{customer_info['customer_identifier'][:8]}
                        - 初始密码已通过安全方式发送
                        - 首次登录后请修改密码
                        
                        💡 提示：此测试用户具有完整的系统访问权限
                    """
                    st.success(success_message)
                    
                    # 保存测试客户信息到会话
                    st.session_state['aws_customer_info'] = customer_info
                    add_log("info", f"测试用户创建成功: {customer_info['customer_identifier']}")
                    
            except Exception as e:
                error_msg = f"测试流程失败: {str(e)}"
                add_log("error", error_msg)
                st.error(error_msg)
        
        st.markdown("---")
        
        # 原有的Token验证界面
        st.markdown("### 🔐 正式客户验证")
        
        # 获取已保存的客户信息
        if 'aws_customer_info' in st.session_state:
            customer_info = st.session_state['aws_customer_info']
            st.success(f"已验证的客户: {customer_info['customer_identifier']}")
            return
            
        # Token输入界面
        token = st.text_input(
            "请输入AWS Marketplace注册Token",
            type="password",
            help="Token可以从AWS Marketplace订阅页面获取"
        )
        
        if st.button("验证Token", key="verify_real_token"):
            if not token:
                st.error("请输入Token")
                return
                
            try:
                add_log("info", "开始验证AWS MP Token...")
                
                # 解析Token并创建用户
                customer_info = customer_mgr.resolve_customer(token)
                
                # 保存客户信息到会话
                st.session_state['aws_customer_info'] = customer_info
                
                # 显示成功消息
                st.success(f"""
                    ✅ Token验证成功！
                    
                    您的账户信息：
                    - 用户名: mp_{customer_info['customer_identifier'][:8]}
                    - AWS账户: {customer_info['customer_aws_account_id']}
                    
                    请使用以下信息登录系统：
                    1. 用户名: mp_{customer_info['customer_identifier'][:8]}
                    2. 初始密码已通过安全方式发送
                    3. 首次登录后请修改密码
                    
                    您现在可以开始使用所有功能了！
                """)
                
                add_log("info", f"AWS MP Token验证成功，用户已创建: {customer_info['customer_identifier']}")
                
            except Exception as e:
                error_msg = f"Token验证失败: {str(e)}"
                add_log("error", error_msg)
                st.error(error_msg)
                
    except Exception as e:
        error_msg = f"客户验证界面加载失败: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)

def get_customer_info() -> Optional[Dict[str, Any]]:
    """获取当前会话中的客户信息"""
    return st.session_state.get('aws_customer_info')

def clear_customer_info():
    """清除当前会话中的客户信息"""
    if 'aws_customer_info' in st.session_state:
        del st.session_state['aws_customer_info']
        
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
        st.header("测试模拟")
        st.markdown("""
        此功能用于测试AWS Marketplace客户验证流程。
        
        处理流程：
        1. 生成测试Token
        2. 模拟URL回调
        3. 验证Token并创建测试用户
        4. 显示测试结果和用户信息
        """)
        
        if st.button("开始测试", key="start_test"):
            try:
                with st.spinner("正在执行测试流程..."):
                    # 创建进度条
                    progress = st.progress(0)
                    
                    # 步骤1: 生成测试token
                    progress.progress(20)
                    st.info("步骤1/4: 生成测试Token")
                    test_token = generate_test_token()
                    time.sleep(1)
                    
                    # 步骤2: 模拟URL回调
                    progress.progress(40)
                    st.info("步骤2/4: 模拟URL回调")
                    callback_result = simulate_callback(test_token)
                    time.sleep(1)
                    
                    # 步骤3: 验证Token
                    progress.progress(60)
                    st.info("步骤3/4: 验证Token")
                    if not customer_mgr.validate_token(test_token):
                        raise ValueError("Token验证失败")
                    time.sleep(1)
                    
                    # 步骤4: 创建测试用户
                    progress.progress(80)
                    st.info("步骤4/4: 创建测试用户")
                    customer_info = customer_mgr.resolve_customer(test_token)
                    progress.progress(100)
                    
                    # 显示测试结果
                    success_message = f"""
                        ✅ 测试完成！
                        
                        测试用户已成功创建：
                        1. 用户名: mp_{customer_info['customer_identifier'][:8]}
                        2. AWS账户: {customer_info['customer_aws_account_id']}
                        3. 产品代码: {customer_info['product_code']}
                        
                        您可以使用以下信息登录系统：
                        - 用户名: mp_{customer_info['customer_identifier'][:8]}
                        - 初始密码已通过安全方式发送
                        - 首次登录后请修改密码
                        
                        💡 提示：此测试用户具有完整的系统访问权限
                    """
                    st.success(success_message)
                    
                    # 保存测试客户信息到会话
                    st.session_state['aws_customer_info'] = customer_info
                    add_log("info", f"测试用户创建成功: {customer_info['customer_identifier']}")
                    
            except Exception as e:
                error_msg = f"测试流程失败: {str(e)}"
                add_log("error", error_msg)
                st.error(error_msg) 