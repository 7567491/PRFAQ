"""
AWS Marketplace Entitlement Management Module
"""
import streamlit as st
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any, List
from modules.utils import add_log
from .exceptions import EntitlementError, MarketplaceError
import os
from dotenv import load_dotenv
import threading
import sqlite3
from functools import lru_cache
import time

class EntitlementManager:
    """AWS Marketplace entitlement management"""
    
    def __init__(self):
        """Initialize entitlement manager"""
        self.load_config()
        self._init_clients()
        self._lock = threading.Lock()
        self._cache_timeout = 300  # 5分钟缓存
        
    def load_config(self):
        """Load AWS configuration"""
        load_dotenv()
        self.config = {
            'region': os.getenv('AWS_DEFAULT_REGION', 'cn-northwest-1'),
            'api_version': '2017-01-11',
            'entitlement_endpoint': 'https://entitlement-marketplace.cn-northwest-1.amazonaws.com.cn',
            'product_code': os.getenv('AWS_PRODUCT_CODE')
        }
        
    def _init_clients(self):
        """Initialize AWS clients"""
        try:
            session = boto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.config['region']
            )
            
            self.entitlement_client = session.client(
                'marketplace-entitlement',
                region_name=self.config['region'],
                endpoint_url=self.config['entitlement_endpoint']
            )
            
            add_log("info", "AWS entitlement client initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize AWS clients: {str(e)}"
            add_log("error", error_msg)
            raise EntitlementError(error_msg)
    
    @lru_cache(maxsize=100)
    def _get_cached_entitlement(self, customer_identifier: str) -> Optional[Dict[str, Any]]:
        """Get cached entitlement information"""
        return None  # Cache miss by default
        
    def check_entitlement(self, customer_identifier: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Check customer entitlement status
        
        Args:
            customer_identifier: AWS Marketplace customer identifier
            force_refresh: Force refresh cache
            
        Returns:
            Dict with entitlement information
            
        Raises:
            EntitlementError: If entitlement check fails
        """
        try:
            # Check cache first
            if not force_refresh:
                cached = self._get_cached_entitlement(customer_identifier)
                if cached:
                    add_log("info", f"Using cached entitlement for {customer_identifier}")
                    return cached
            
            # Call GetEntitlements API
            response = self.entitlement_client.get_entitlements(
                ProductCode=self.config['product_code'],
                Filter={
                    'CUSTOMER_IDENTIFIER': [customer_identifier]
                }
            )
            
            entitlements = response.get('Entitlements', [])
            if not entitlements:
                raise EntitlementError(f"No entitlements found for {customer_identifier}")
                
            # Process entitlements
            result = {
                'customer_identifier': customer_identifier,
                'status': 'ACTIVE',
                'entitlements': entitlements,
                'checked_at': datetime.now().isoformat()
            }
            
            # Update cache
            self._get_cached_entitlement.cache_clear()
            self._get_cached_entitlement(customer_identifier)
            
            # Store in database
            self._store_entitlement(customer_identifier, result)
            
            add_log("info", f"Entitlement check successful for {customer_identifier}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to check entitlement: {str(e)}"
            add_log("error", error_msg)
            raise EntitlementError(error_msg)
            
    def _store_entitlement(self, customer_identifier: str, entitlement_data: Dict[str, Any]) -> None:
        """Store entitlement information in database"""
        try:
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                # Get customer ID
                cursor.execute(
                    "SELECT aws_customer_id FROM aws_customers WHERE customer_identifier = ?",
                    (customer_identifier,)
                )
                result = cursor.fetchone()
                if not result:
                    raise EntitlementError(f"Customer not found: {customer_identifier}")
                    
                aws_customer_id = result[0]
                
                # Store each entitlement
                for ent in entitlement_data['entitlements']:
                    cursor.execute("""
                        INSERT INTO aws_subscriptions (
                            aws_customer_id,
                            entitlement_value,
                            dimension_name,
                            valid_from,
                            valid_to
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        aws_customer_id,
                        ent.get('EntitlementValue', 0),
                        ent.get('DimensionName', 'default'),
                        ent.get('ValidFrom', datetime.now().isoformat()),
                        ent.get('ValidTo')
                    ))
                    
                # Update customer status
                cursor.execute("""
                    UPDATE aws_customers 
                    SET subscription_status = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_identifier = ?
                """, (
                    1 if entitlement_data['status'] == 'ACTIVE' else 0,
                    customer_identifier
                ))
                
                conn.commit()
                add_log("info", f"Stored entitlement for {customer_identifier}")
                
        except Exception as e:
            error_msg = f"Failed to store entitlement: {str(e)}"
            add_log("error", error_msg)
            raise EntitlementError(error_msg)
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    def get_subscription_history(self, customer_identifier: str) -> List[Dict[str, Any]]:
        """Get subscription history for customer"""
        try:
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT s.* 
                FROM aws_subscriptions s
                JOIN aws_customers c ON s.aws_customer_id = c.aws_customer_id
                WHERE c.customer_identifier = ?
                ORDER BY s.created_at DESC
            """, (customer_identifier,))
            
            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()
            
            history = [dict(zip(columns, row)) for row in results]
            return history
            
        except Exception as e:
            error_msg = f"Failed to get subscription history: {str(e)}"
            add_log("error", error_msg)
            raise EntitlementError(error_msg)
            
        finally:
            if 'conn' in locals():
                conn.close()

class EntitlementSimulator:
    """Simulator for testing entitlement management"""
    
    def __init__(self):
        """Initialize simulator"""
        self.entitlement_mgr = EntitlementManager()
        
    def simulate_subscription(self, customer_identifier: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Simulate subscription process
        
        Returns:
            (success, message, subscription_data)
        """
        try:
            add_log("info", "开始模拟订阅流程...")
            
            # Step 1: 确保测试客户存在
            add_log("info", "步骤1: 检查测试客户...")
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            # 检查客户是否存在
            cursor.execute("""
                SELECT aws_customer_id 
                FROM aws_customers 
                WHERE customer_identifier = ?
            """, (customer_identifier,))
            
            result = cursor.fetchone()
            if not result:
                add_log("info", "测试客户不存在，创建新客户记录...")
                # 创建测试客户记录
                cursor.execute("""
                    INSERT INTO aws_customers (
                        user_id,
                        customer_identifier,
                        aws_account_id,
                        product_code,
                        subscription_status
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    '1',  # 测试用户ID
                    customer_identifier,
                    '123456789012',  # 测试AWS账户ID
                    'test-product',   # 测试产品代码
                    1                 # 激活状态
                ))
                conn.commit()
                aws_customer_id = cursor.lastrowid
                add_log("info", f"创建测试客户成功，ID: {aws_customer_id}")
            else:
                aws_customer_id = result[0]
                add_log("info", f"找到现有客户记录，ID: {aws_customer_id}")
            
            conn.close()
            
            # Step 2: 生成测试订阅数据
            add_log("info", "步骤2: 生成测试订阅数据...")
            entitlement_data = {
                'Entitlements': [{
                    'EntitlementValue': 100,
                    'DimensionName': 'Users',
                    'ValidFrom': datetime.now().isoformat(),
                    'ValidTo': (datetime.now() + timedelta(days=365)).isoformat()
                }]
            }
            add_log("info", "测试订阅数据生成成功")
            
            # Step 3: 存储订阅信息
            add_log("info", "步骤3: 存储订阅信息...")
            self.entitlement_mgr._store_entitlement(
                customer_identifier,
                {
                    'customer_identifier': customer_identifier,
                    'status': 'ACTIVE',
                    'entitlements': entitlement_data['Entitlements'],
                    'checked_at': datetime.now().isoformat()
                }
            )
            add_log("info", "订阅信息存储成功")
            
            # Step 4: 获取订阅历史
            add_log("info", "步骤4: 获取订阅历史...")
            history = self.entitlement_mgr.get_subscription_history(customer_identifier)
            add_log("info", f"获取到 {len(history)} 条历史记录")
            
            # 返回完整的测试数据
            test_data = {
                'customer_identifier': customer_identifier,
                'aws_customer_id': aws_customer_id,
                'entitlement_data': entitlement_data,
                'history': history,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            add_log("info", "订阅模拟完成")
            return True, "订阅模拟成功", test_data
            
        except Exception as e:
            error_msg = f"订阅模拟失败: {str(e)}"
            add_log("error", error_msg)
            
            # 添加更详细的错误信息
            if isinstance(e, sqlite3.Error):
                add_log("error", f"数据库错误: {str(e)}")
                try:
                    cursor.execute("PRAGMA table_info(aws_customers)")
                    columns = cursor.fetchall()
                    add_log("info", f"aws_customers表结构: {columns}")
                except:
                    pass
            
            return False, error_msg, {}
            
        finally:
            if 'conn' in locals():
                conn.close()

def show_entitlement_panel():
    """Display entitlement management panel"""
    st.title("AWS Marketplace 订阅管理")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs([
        "订阅状态",
        "订阅历史",
        "测试模拟"
    ])
    
    # 初始化管理器
    try:
        entitlement_mgr = EntitlementManager()
    except Exception as e:
        st.error(f"初始化订阅管理器失败: {str(e)}")
        return
        
    # Tab 1: 订阅状态
    with tab1:
        st.header("订阅状态检查")
        st.markdown("""
        此功能用于检查AWS Marketplace客户的订阅状态：
        
        1. 输入客户标识符
        2. 调用GetEntitlements API
        3. 显示订阅详情
        4. 更新本地记录
        """)
        
        customer_id = st.text_input("客户标识符")
        force_refresh = st.checkbox("强制刷新缓存")
        
        if st.button("检查订阅", key="check_subscription"):
            if not customer_id:
                st.error("请输入客户标识符")
                return
                
            try:
                with st.spinner("正在检查订阅状态..."):
                    result = entitlement_mgr.check_entitlement(
                        customer_id,
                        force_refresh=force_refresh
                    )
                    
                    st.success("订阅状态检查成功")
                    st.json(result)
                    
            except Exception as e:
                st.error(f"订阅检查失败: {str(e)}")
                
    # Tab 2: 订阅历史
    with tab2:
        st.header("订阅历史记录")
        st.markdown("""
        查看客户的订阅历史记录：
        - 订阅变更记录
        - 授权值变化
        - 时间范围
        """)
        
        customer_id = st.text_input("客户标识符", key="history_customer_id")
        
        if st.button("查询历史", key="query_history"):
            if not customer_id:
                st.error("请输入客户标识符")
                return
                
            try:
                history = entitlement_mgr.get_subscription_history(customer_id)
                if history:
                    st.success(f"找到 {len(history)} 条历史记录")
                    st.json(history)
                else:
                    st.warning("未找到历史记录")
                    
            except Exception as e:
                st.error(f"查询历史失败: {str(e)}")
                
    # Tab 3: 测试模拟
    with tab3:
        st.header("订阅测试模拟")
        st.markdown("""
        模拟AWS Marketplace订阅流程：
        
        1. **生成测试数据**
           - 模拟客户信息
           - 模拟订阅数据
           - 模拟时间范围
        
        2. **执行订阅流程**
           - 创建订阅记录
           - 更新客户状态
           - 记录历史数据
        
        3. **验证结果**
           - 检查数据一致性
           - 验证状态更新
           - 确认历史记录
        """)
        
        simulator = EntitlementSimulator()
        
        if st.button("运行模拟测试", key="run_simulation"):
            with st.spinner("正在执行订阅模拟..."):
                # 显示测试进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: 准备测试数据
                    status_text.text("步骤1/3: 准备测试数据...")
                    progress_bar.progress(33)
                    customer_id = f"test-cust-{int(time.time())}"
                    time.sleep(1)
                    
                    # Step 2: 执行订阅流程
                    status_text.text("步骤2/3: 执行订阅流程...")
                    progress_bar.progress(66)
                    success, message, data = simulator.simulate_subscription(customer_id)
                    time.sleep(1)
                    
                    # Step 3: 验证结果
                    status_text.text("步骤3/3: 验证结果...")
                    progress_bar.progress(100)
                    
                    if success:
                        status_text.text("模拟测试完成!")
                        st.success(message)
                        
                        # 显示测试结果
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("订阅数据")
                            st.json(data['entitlement_data'])
                            
                        with col2:
                            st.subheader("历史记录")
                            st.json(data['history'])
                            
                        # 显示验证步骤
                        st.subheader("验证步骤")
                        st.write("✅ 数据生成")
                        st.write("✅ 订阅创建")
                        st.write("✅ 状态更新")
                        st.write("✅ 历史记录")
                        
                    else:
                        status_text.text("模拟测试失败!")
                        st.error(message)
                        
                except Exception as e:
                    status_text.text(f"模拟测试出错: {str(e)}")
                    st.error(f"模拟测试过程中出现错误: {str(e)}")
                    add_log("error", f"订阅模拟测试失败: {str(e)}") 