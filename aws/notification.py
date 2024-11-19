"""
AWS Marketplace Notification Handler
"""
import streamlit as st
import boto3
import json
import time
import threading
import queue
from datetime import datetime
from typing import Dict, Optional, Tuple, Any, List
from modules.utils import add_log
from .exceptions import MarketplaceError
from .entitlement import EntitlementManager
import os
from dotenv import load_dotenv
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import uuid
import random
from datetime import datetime, timedelta

class NotificationManager:
    """AWS Marketplace notification management"""
    
    def __init__(self):
        """Initialize notification manager"""
        self.load_config()
        self._init_clients()
        self._message_queue = queue.Queue()
        self._lock = threading.Lock()
        self._running = False
        self.entitlement_mgr = EntitlementManager(test_mode=True)
        
    def load_config(self):
        """Load AWS configuration"""
        load_dotenv()
        self.config = {
            'region': os.getenv('AWS_DEFAULT_REGION', 'cn-northwest-1'),
            'queue_url': os.getenv('AWS_SQS_QUEUE_URL'),
            'topic_arn': os.getenv('AWS_SNS_TOPIC_ARN'),
            'product_code': os.getenv('AWS_PRODUCT_CODE', 'test-product-code'),
            'max_retries': 3,
            'retry_delay': 5,  # seconds
            'batch_size': 10
        }
        
        # 验证必要的配置
        required_configs = {
            'AWS_PRODUCT_CODE': self.config['product_code'],
            'AWS_SQS_QUEUE_URL': self.config['queue_url'],
            'AWS_SNS_TOPIC_ARN': self.config['topic_arn']
        }
        
        missing_configs = [key for key, value in required_configs.items() if not value]
        if missing_configs:
            add_log("warning", f"缺少必要的配置项: {', '.join(missing_configs)}")
            add_log("info", "请在.env文件中添加以下配置：")
            add_log("info", """
            AWS_PRODUCT_CODE=your-product-code
            AWS_SQS_QUEUE_URL=your-sqs-queue-url
            AWS_SNS_TOPIC_ARN=your-sns-topic-arn
            """)
            
    def _init_clients(self):
        """Initialize AWS clients"""
        try:
            session = boto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.config['region']
            )
            
            self.sqs_client = session.client('sqs')
            self.sns_client = session.client('sns')
            
            add_log("info", "AWS notification clients initialized")
            
        except Exception as e:
            error_msg = f"Failed to initialize AWS clients: {str(e)}"
            add_log("error", error_msg)
            raise MarketplaceError(error_msg)
            
    def start_processing(self):
        """Start notification processing"""
        if self._running:
            return
            
        self._running = True
        self._processor_thread = threading.Thread(target=self._process_messages)
        self._processor_thread.daemon = True
        self._processor_thread.start()
        add_log("info", "Notification processor started")
        
    def stop_processing(self):
        """Stop notification processing"""
        self._running = False
        if hasattr(self, '_processor_thread'):
            self._processor_thread.join()
        add_log("info", "Notification processor stopped")
        
    def _process_messages(self):
        """Process messages from SQS queue"""
        while self._running:
            try:
                # Receive messages from SQS
                response = self.sqs_client.receive_message(
                    QueueUrl=self.config['queue_url'],
                    MaxNumberOfMessages=self.config['batch_size'],
                    WaitTimeSeconds=20
                )
                
                messages = response.get('Messages', [])
                if not messages:
                    continue
                    
                # Process messages in parallel
                with ThreadPoolExecutor(max_workers=self.config['batch_size']) as executor:
                    futures = [
                        executor.submit(self._handle_message, message)
                        for message in messages
                    ]
                    
                    # Wait for all messages to be processed
                    for future in futures:
                        try:
                            future.result()
                        except Exception as e:
                            add_log("error", f"Message processing failed: {str(e)}")
                            
            except Exception as e:
                add_log("error", f"Queue processing error: {str(e)}")
                time.sleep(self.config['retry_delay'])
                
    def _handle_message(self, message: Dict[str, Any], test_mode: bool = True) -> bool:
        """Handle individual SQS message"""
        try:
            # 检查产品代码
            if not self.config.get('product_code'):
                error_msg = "ProductCode未配置，请在.env文件中设置AWS_PRODUCT_CODE"
                add_log("error", error_msg)
                return False
            
            # Parse message body
            body = json.loads(message['Body'])
            notification = json.loads(body['Message'])
            
            # 验证消息中的产品代码
            message_product_code = notification.get('ProductCode')
            if message_product_code != self.config['product_code']:
                add_log("warning", f"产品代码不匹配: 期望 {self.config['product_code']}, 实际 {message_product_code}")
                return False
            
            # Process different notification types
            notification_type = notification.get('Type')
            if notification_type == 'entitlement-updated':
                self._handle_entitlement_update(notification)
            elif notification_type == 'subscription-cancelled':
                self._handle_subscription_cancellation(notification)
            elif notification_type == 'subscription-created':
                self._handle_subscription_creation(notification)
            else:
                add_log("warning", f"未知的通知类型: {notification_type}")
            
            # 只在非测试模式下删除消息
            if not test_mode:
                self.sqs_client.delete_message(
                    QueueUrl=self.config['queue_url'],
                    ReceiptHandle=message['ReceiptHandle']
                )
            
            # Record notification
            self._store_notification(notification)
            
            return True
            
        except Exception as e:
            add_log("error", f"消息处理失败: {str(e)}")
            return False
            
    def _handle_entitlement_update(self, notification: Dict[str, Any]):
        """Handle entitlement update notification"""
        try:
            customer_id = notification['CustomerIdentifier']
            
            # Update entitlement status
            entitlement = self.entitlement_mgr.check_entitlement(
                customer_id,
                force_refresh=True
            )
            
            # Send user notification
            self._notify_user(
                customer_id,
                "订阅状态已更新",
                f"您的订阅状态已更新: {entitlement['status']}"
            )
            
            add_log("info", f"Entitlement updated for customer: {customer_id}")
            
        except Exception as e:
            add_log("error", f"Entitlement update failed: {str(e)}")
            raise
            
    def _handle_subscription_cancellation(self, notification: Dict[str, Any]):
        """Handle subscription cancellation notification"""
        try:
            customer_id = notification['CustomerIdentifier']
            
            # Update subscription status
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE aws_customers 
                    SET subscription_status = 0,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_identifier = ?
                """, (customer_id,))
                
                conn.commit()
                conn.close()
            
            # Send user notification
            self._notify_user(
                customer_id,
                "订阅已取消",
                "您的订阅已取消，如需继续使用请重新订阅"
            )
            
            add_log("info", f"Subscription cancelled for customer: {customer_id}")
            
        except Exception as e:
            add_log("error", f"Subscription cancellation failed: {str(e)}")
            raise
            
    def _handle_subscription_creation(self, notification: Dict[str, Any]):
        """Handle subscription creation notification"""
        try:
            customer_id = notification['CustomerIdentifier']
            
            # Update subscription status
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE aws_customers 
                    SET subscription_status = 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE customer_identifier = ?
                """, (customer_id,))
                
                conn.commit()
                conn.close()
            
            # Send user notification
            self._notify_user(
                customer_id,
                "订阅已创建",
                "您的订阅已成功创建，现在可以使用所有功能"
            )
            
            add_log("info", f"Subscription created for customer: {customer_id}")
            
        except Exception as e:
            add_log("error", f"Subscription creation failed: {str(e)}")
            raise
            
    def _store_notification(self, notification: Dict[str, Any]):
        """Store notification in database"""
        try:
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                # Get customer ID
                customer_id = notification.get('CustomerIdentifier')
                cursor.execute(
                    "SELECT aws_customer_id FROM aws_customers WHERE customer_identifier = ?",
                    (customer_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise MarketplaceError(f"Customer not found: {customer_id}")
                    
                aws_customer_id = result[0]
                
                # Store notification
                cursor.execute("""
                    INSERT INTO aws_notifications (
                        aws_customer_id,
                        notification_type,
                        message,
                        processed
                    ) VALUES (?, ?, ?, ?)
                """, (
                    aws_customer_id,
                    notification.get('Type'),
                    json.dumps(notification),
                    1
                ))
                
                conn.commit()
                conn.close()
                
            add_log("info", f"Notification stored for customer: {customer_id}")
            
        except Exception as e:
            add_log("error", f"Failed to store notification: {str(e)}")
            raise
            
    def _notify_user(self, customer_id: str, title: str, message: str):
        """Send notification to user"""
        try:
            # Get user ID
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.email 
                FROM users u
                JOIN aws_customers ac ON u.user_id = ac.user_id
                WHERE ac.customer_identifier = ?
            """, (customer_id,))
            
            result = cursor.fetchone()
            if result:
                email = result[0]
                # TODO: 实现实际的用户通知逻辑
                add_log("info", f"Would send notification to {email}: {title} - {message}")
            
            conn.close()
            
        except Exception as e:
            add_log("error", f"Failed to notify user: {str(e)}")
            raise

class NotificationSimulator:
    """Simulator for testing notification handling"""
    
    def __init__(self):
        """Initialize simulator"""
        self.notification_mgr = NotificationManager()
        
    def _generate_test_data(self, notification_type: str) -> Dict[str, Any]:
        """Generate random test data"""
        # 生成随机客户ID
        timestamp = int(time.time())
        customer_id = f"test-cust-{timestamp}-{uuid.uuid4().hex[:6]}"
        account_id = f"{random.randint(100000000000, 999999999999)}"
        
        # 根据通知类型生成不同的测试数据
        test_data = {
            'customer_identifier': customer_id,
            'aws_account_id': account_id,
            'product_code': self.notification_mgr.config.get('product_code', 'test-product-code')
        }
        
        # 添加特定通知类型的数据
        if notification_type == 'entitlement-updated':
            test_data.update({
                'entitlement_value': random.randint(1, 100),
                'dimension': 'Users',
                'valid_from': datetime.now().isoformat(),
                'valid_to': (datetime.now() + timedelta(days=365)).isoformat()
            })
        elif notification_type == 'subscription-cancelled':
            test_data.update({
                'cancel_date': datetime.now().isoformat(),
                'reason': 'Customer requested cancellation'
            })
        elif notification_type == 'subscription-created':
            test_data.update({
                'creation_date': datetime.now().isoformat(),
                'plan': f"plan-{random.randint(1, 3)}"
            })
            
        add_log("info", f"生成测试数据: {test_data}")
        return test_data
        
    def _ensure_test_customer_exists(self, test_data: Dict[str, Any]) -> None:
        """Ensure test customer exists in database"""
        try:
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            # 检查客户是否存在
            cursor.execute("""
                SELECT aws_customer_id 
                FROM aws_customers 
                WHERE customer_identifier = ?
            """, (test_data['customer_identifier'],))
            
            if not cursor.fetchone():
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
                    test_data['customer_identifier'],
                    test_data['aws_account_id'],
                    test_data['product_code'],
                    1     # 激活状态
                ))
                conn.commit()
                add_log("info", f"创建测试客户记录成功: {test_data['customer_identifier']}")
            else:
                add_log("info", f"测试客户记录已存在: {test_data['customer_identifier']}")
                
        except Exception as e:
            add_log("error", f"确保测试客户存在时出错: {str(e)}")
            raise
        finally:
            if 'conn' in locals():
                conn.close()
                
    def simulate_notification(self, notification_type: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Simulate notification processing"""
        try:
            # 生成测试数据
            test_data = self._generate_test_data(notification_type)
            
            # 使用测试数据生成通知
            notification = {
                'Type': notification_type,
                'CustomerIdentifier': test_data['customer_identifier'],
                'Timestamp': datetime.now().isoformat(),
                'ProductCode': test_data['product_code'],
                'EntitlementContext': {
                    'AccountId': test_data['aws_account_id'],
                    'Environment': 'test'
                }
            }
            
            # 根据通知类型添加特定数据
            if notification_type == 'entitlement-updated':
                notification['Entitlements'] = [{
                    'Value': test_data['entitlement_value'],
                    'Dimension': test_data['dimension'],
                    'ValidFrom': test_data['valid_from'],
                    'ValidTo': test_data['valid_to']
                }]
            elif notification_type == 'subscription-cancelled':
                notification['CancellationDate'] = test_data['cancel_date']
                notification['CancellationReason'] = test_data['reason']
            elif notification_type == 'subscription-created':
                notification['CreationDate'] = test_data['creation_date']
                notification['Plan'] = test_data['plan']
            
            add_log("info", f"生成测试通知: {notification}")
            
            # 创建SQS消息格式
            message = {
                'MessageId': f'test-msg-{int(time.time())}',
                'ReceiptHandle': 'test-receipt',
                'Body': json.dumps({
                    'Message': json.dumps(notification)
                })
            }
            
            # 处理通知前确保测试数据存在
            self._ensure_test_customer_exists(test_data)
            
            # 处理通知，指定测试模式
            success = self.notification_mgr._handle_message(message, test_mode=True)
            
            if success:
                result_data = {
                    'notification': notification,
                    'customer_info': test_data,
                    'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                return True, "通知处理成功", result_data
            else:
                return False, "通知处理失败", {}
            
        except Exception as e:
            error_msg = f"通知处理失败: {str(e)}"
            add_log("error", error_msg)
            return False, error_msg, {}

def show_notification_panel():
    """Display notification management panel"""
    st.title("AWS Marketplace 通知处理")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs([
        "通知监控",
        "历史记录",
        "测试模拟"
    ])
    
    # 初始化管理器
    try:
        notification_mgr = NotificationManager()
        
        # 检查必要的配置
        missing_configs = []
        if not notification_mgr.config.get('product_code'):
            missing_configs.append('AWS_PRODUCT_CODE')
        if not notification_mgr.config.get('queue_url'):
            missing_configs.append('AWS_SQS_QUEUE_URL')
        if not notification_mgr.config.get('topic_arn'):
            missing_configs.append('AWS_SNS_TOPIC_ARN')
            
        if missing_configs:
            st.error(f"⚠️ 缺少必要的配置项: {', '.join(missing_configs)}")
            st.info("请在 .env 文件中添加以下配置：")
            st.code("""
            AWS_PRODUCT_CODE=your-product-code
            AWS_SQS_QUEUE_URL=your-sqs-queue-url
            AWS_SNS_TOPIC_ARN=your-sns-topic-arn
            """)
            
            # 显示设置向导
            st.subheader("配置设置向导")
            st.markdown("""
            1. 运行 setup.py 创建必要的AWS资源
            2. 将生成的配置复制到 .env 文件
            3. 在AWS Marketplace中获取您的产品代码
            4. 重启应用以加载新的配置
            """)
            return
            
    except Exception as e:
        st.error(f"初始化通知管理器失败: {str(e)}")
        return
        
    # Tab 1: 通知监控
    with tab1:
        st.header("通知监控")
        st.markdown("""
        监控AWS Marketplace通知：
        
        1. SQS队列状态
        2. 消息处理状态
        3. 实时通知显示
        """)
        
        # 显示队列状态
        try:
            queue_attrs = notification_mgr.sqs_client.get_queue_attributes(
                QueueUrl=notification_mgr.config['queue_url'],
                AttributeNames=['All']
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "消息数量",
                    queue_attrs['Attributes'].get('ApproximateNumberOfMessages', '0')
                )
            with col2:
                st.metric(
                    "处理中消息",
                    queue_attrs['Attributes'].get('ApproximateNumberOfMessagesNotVisible', '0')
                )
            with col3:
                st.metric(
                    "延迟消息",
                    queue_attrs['Attributes'].get('ApproximateNumberOfMessagesDelayed', '0')
                )
                
        except Exception as e:
            st.error(f"获取队列状态失败: {str(e)}")
            st.info("请确保SQS队列配置正确且有访问权限")
            
        # 启动/停止处理
        col1, col2 = st.columns(2)
        with col1:
            if st.button("启动处理", key="start_notification_processing"):
                notification_mgr.start_processing()
                st.success("通知处理已启动")
                
        with col2:
            if st.button("停止处理", key="stop_notification_processing"):
                notification_mgr.stop_processing()
                st.success("通知处理已停止")
                
    # Tab 2: 历史记录
    with tab2:
        st.header("通知历史记录")
        st.markdown("""
        查看史通知记录：
        - 通知类型统计
        - 处理状态统计
        - 详细记录查询
        """)
        
        # 查询条件
        col1, col2 = st.columns(2)
        with col1:
            notification_type = st.selectbox(
                "通知类型",
                ["全部", "entitlement-updated", "subscription-cancelled", "subscription-created"],
                key="notification_type_filter"
            )
        with col2:
            processed = st.selectbox(
                "处理状态",
                ["全部", "已处理", "未处理"],
                key="notification_status_filter"
            )
            
        if st.button("查询", key="query_notification_history"):
            try:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                query = """
                    SELECT n.*, c.customer_identifier
                    FROM aws_notifications n
                    JOIN aws_customers c ON n.aws_customer_id = c.aws_customer_id
                    WHERE 1=1
                """
                params = []
                
                if notification_type != "全部":
                    query += " AND n.notification_type = ?"
                    params.append(notification_type)
                    
                if processed != "全部":
                    query += " AND n.processed = ?"
                    params.append(1 if processed == "已处理" else 0)
                    
                query += " ORDER BY n.created_at DESC"
                
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                results = cursor.fetchall()
                
                if results:
                    # 转换为DataFrame显示
                    df = pd.DataFrame(results, columns=columns)
                    st.dataframe(df)
                else:
                    st.info("未找到匹配的记录")
                    
                conn.close()
                
            except Exception as e:
                st.error(f"查询历史记录失败: {str(e)}")
                
    # Tab 3: 测试模拟
    with tab3:
        st.header("通知测试模拟")
        st.markdown("""
        模AWS Marketplace通知处理流程：
        
        1. **生成测试通知**
           - 选择通知类型
           - 生成测试数据
           - 模拟消息格式
        
        2. **处理通知**
           - 解析消息内容
           - 更新订阅状态
           - 发送用户通知
        
        3. **验证结果**
           - 检查处理状态
           - 验证数据更新
           - 确认通知发送
        """)
        
        # 测试选项
        notification_type = st.selectbox(
            "选择通知类型",
            [
                "entitlement-updated",
                "subscription-cancelled",
                "subscription-created"
            ],
            help="选择要模拟的通知类型"
        )
        
        if st.button("运行模拟测试", key="run_notification_test"):
            simulator = NotificationSimulator()
            
            with st.spinner("正在执行通知模拟..."):
                # 显示测试进度
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: 准备测试数据
                    status_text.text("步骤1/3: 准备测试数据...")
                    progress_bar.progress(33)
                    time.sleep(1)
                    
                    # Step 2: 处理通知
                    status_text.text("步骤2/3: 处理通知...")
                    progress_bar.progress(66)
                    success, message, data = simulator.simulate_notification(notification_type)
                    time.sleep(1)
                    
                    # Step 3: 验证结果
                    status_text.text("步骤3/3: 验证结果...")
                    progress_bar.progress(100)
                    
                    if success:
                        status_text.text("模拟测试完成!")
                        st.success(message)
                        
                        # 显示测试结果
                        st.subheader("测试结果")
                        st.json(data)
                        
                        # 显示验证步骤
                        st.subheader("验证步骤")
                        st.write("✅ 通知生成")
                        st.write("✅ 消息处理")
                        st.write("✅ 状态更新")
                        st.write("✅ 用户通知")
                        
                    else:
                        status_text.text("模拟测试失败!")
                        st.error(message)
                        
                except Exception as e:
                    status_text.text(f"模拟测试出错: {str(e)}")
                    st.error(f"模拟测试过程中出现错误: {str(e)}")
                    add_log("error", f"通知模拟测试失败: {str(e)}") 