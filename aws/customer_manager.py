"""
AWS Marketplace Customer Manager
"""
import boto3
import json
import sqlite3
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple, Any
from modules.utils import add_log
from .exceptions import AuthenticationError, MarketplaceError
import os
from dotenv import load_dotenv
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

class CustomerManager:
    """AWS Marketplace customer management"""
    
    def __init__(self):
        """Initialize customer manager"""
        self.load_config()
        self._init_clients()
        self._token_queue = queue.Queue()
        self._lock = threading.Lock()
        
    def load_config(self):
        """Load AWS configuration"""
        load_dotenv()
        self.config = {
            'region': os.getenv('AWS_DEFAULT_REGION', 'cn-northwest-1'),
            'api_version': '2017-01-11',
            'entitlement_endpoint': 'https://entitlement-marketplace.cn-northwest-1.amazonaws.com.cn'
        }
        
    def _init_clients(self):
        """Initialize AWS clients"""
        try:
            session = boto3.Session(
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=self.config['region']
            )
            
            self.metering_client = session.client(
                'meteringmarketplace',
                region_name=self.config['region']
            )
            
            self.entitlement_client = session.client(
                'marketplace-entitlement',
                region_name=self.config['region'],
                endpoint_url=self.config['entitlement_endpoint']
            )
            
            add_log("info", "AWS clients initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize AWS clients: {str(e)}"
            add_log("error", error_msg)
            raise AuthenticationError(error_msg)
            
    def validate_token(self, token: str) -> bool:
        """
        Validate marketplace registration token
        
        Args:
            token: Registration token from AWS Marketplace
            
        Returns:
            bool: True if token is valid
        """
        if not token or len(token) < 10:
            return False
            
        # Basic format validation
        try:
            # Token should be base64 encoded
            import base64
            base64.b64decode(token)
            return True
        except:
            return False
            
    def create_user_record(self, customer_info: Dict[str, Any]) -> str:
        """
        为MP客户创建普通用户记录
        
        Args:
            customer_info: 客户信息字典
            
        Returns:
            str: 创建的用户ID
            
        Raises:
            MarketplaceError: 如果创建失败
        """
        try:
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                # 生成用户ID和用户名
                user_id = str(uuid.uuid4())
                username = f"mp_{customer_info['customer_identifier'][:8]}"
                
                # 生成随机密码并哈希
                temp_password = str(uuid.uuid4())[:12]
                password_hash = hashlib.sha256(temp_password.encode()).hexdigest()
                
                # 创建用户记录
                cursor.execute("""
                    INSERT INTO users (
                        user_id, username, password, role, is_active,
                        created_at, points, daily_chars_limit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    username,
                    password_hash,
                    'user',
                    1,  # 活跃状态
                    datetime.now().isoformat(),
                    1000,  # 初始积分
                    100000  # 默认日限额
                ))
                
                # 添加积分交易记录
                cursor.execute("""
                    INSERT INTO point_transactions (
                        user_id, timestamp, type, amount, balance,
                        description, operation_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    datetime.now().isoformat(),
                    'reward',
                    1000,
                    1000,
                    'AWS Marketplace新用户注册奖励',
                    None
                ))
                
                # 更新aws_customers表
                cursor.execute("""
                    UPDATE aws_customers 
                    SET user_id = ?
                    WHERE customer_identifier = ?
                """, (
                    user_id,
                    customer_info['customer_identifier']
                ))
                
                conn.commit()
                add_log("info", f"已为MP客户创建用户记录: {username}")
                
                return user_id
                
        except Exception as e:
            error_msg = f"创建用户记录失败: {str(e)}"
            add_log("error", error_msg)
            raise MarketplaceError(error_msg)
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    def resolve_customer(self, token: str) -> Dict[str, Any]:
        """
        解析客户Token并创建用户记录
        
        Args:
            token: Registration token from AWS Marketplace
            
        Returns:
            Dict with customer information
            
        Raises:
            AuthenticationError: If token resolution fails
        """
        try:
            add_log("info", "开始解析客户token...")
            
            # 验证token
            if not self.validate_token(token):
                raise AuthenticationError("Invalid token format")
            
            # 检查是否为测试token
            try:
                # 尝试解码token看是否是测试token
                import base64
                import json
                decoded_data = json.loads(base64.b64decode(token.encode()).decode())
                if 'CustomerIdentifier' in decoded_data and decoded_data['CustomerIdentifier'].startswith('test_'):
                    # 这是测试token，直接使用解码的数据
                    customer_info = {
                        'customer_identifier': decoded_data['CustomerIdentifier'],
                        'customer_aws_account_id': decoded_data['CustomerAWSAccountId'],
                        'product_code': decoded_data['ProductCode']
                    }
                    add_log("info", "检测到测试Token，使用模拟数据")
                else:
                    # 不是测试token，调用真实的AWS API
                    response = self.metering_client.resolve_customer(
                        RegistrationToken=token
                    )
                    customer_info = {
                        'customer_identifier': response['CustomerIdentifier'],
                        'customer_aws_account_id': response['CustomerAWSAccountId'],
                        'product_code': response['ProductCode']
                    }
            except json.JSONDecodeError:
                # 如果解码失败，说明不是测试token，使用真实API
                response = self.metering_client.resolve_customer(
                    RegistrationToken=token
                )
                customer_info = {
                    'customer_identifier': response['CustomerIdentifier'],
                    'customer_aws_account_id': response['CustomerAWSAccountId'],
                    'product_code': response['ProductCode']
                }
            
            # 存储客户信息并创建用户记录
            user_id = self.create_user_record(customer_info)
            customer_info['user_id'] = user_id
            
            add_log("info", f"客户token解析成功并创建用户: {customer_info['customer_identifier']}")
            return customer_info
            
        except Exception as e:
            error_msg = f"Failed to resolve customer token: {str(e)}"
            add_log("error", error_msg)
            raise AuthenticationError(error_msg)
            
    def store_customer_info(self, user_id: int, customer_info: Dict[str, Any]) -> bool:
        """
        Store customer information in database
        
        Args:
            user_id: Internal user ID
            customer_info: Customer information from AWS
            
        Returns:
            bool: True if successful
            
        Raises:
            MarketplaceError: If storage fails
        """
        try:
            with self._lock:
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                # Check if customer already exists
                cursor.execute(
                    "SELECT aws_customer_id FROM aws_customers WHERE customer_identifier = ?",
                    (customer_info['customer_identifier'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing customer
                    cursor.execute("""
                        UPDATE aws_customers 
                        SET user_id = ?,
                            aws_account_id = ?,
                            product_code = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE customer_identifier = ?
                    """, (
                        user_id,
                        customer_info['customer_aws_account_id'],
                        customer_info['product_code'],
                        customer_info['customer_identifier']
                    ))
                else:
                    # Insert new customer
                    cursor.execute("""
                        INSERT INTO aws_customers (
                            user_id,
                            customer_identifier,
                            aws_account_id,
                            product_code
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        user_id,
                        customer_info['customer_identifier'],
                        customer_info['customer_aws_account_id'],
                        customer_info['product_code']
                    ))
                    
                conn.commit()
                add_log("info", f"客户信息已存储: {customer_info['customer_identifier']}")
                return True
                
        except Exception as e:
            error_msg = f"Failed to store customer information: {str(e)}"
            add_log("error", error_msg)
            raise MarketplaceError(error_msg)
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    def get_customer_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get customer information for user
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Dict with customer information or None
        """
        try:
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT customer_identifier, aws_account_id, product_code, subscription_status
                FROM aws_customers
                WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    'customer_identifier': result[0],
                    'aws_account_id': result[1],
                    'product_code': result[2],
                    'subscription_status': result[3]
                }
            return None
            
        except Exception as e:
            add_log("error", f"Failed to get customer information: {str(e)}")
            return None
            
        finally:
            if 'conn' in locals():
                conn.close() 
    
    def get_user_by_customer_identifier(self, customer_identifier: str) -> Optional[Dict[str, Any]]:
        """
        通过customer_identifier获取用户完整信息
        
        Args:
            customer_identifier: AWS Marketplace客户标识符
            
        Returns:
            Dict: 包含用户和客户信息的字典，如果未找到则返回None
            
        Raises:
            MarketplaceError: 如果查询失败
        """
        try:
            conn = sqlite3.connect('db/users.db')
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    u.user_id,
                    u.username,
                    u.email,
                    u.phone,
                    u.org_name,
                    u.role,
                    u.is_active,
                    u.created_at,
                    u.last_login,
                    u.total_chars,
                    u.total_cost,
                    u.points,
                    ac.aws_customer_id,
                    ac.customer_identifier,
                    ac.aws_account_id,
                    ac.product_code,
                    ac.subscription_status,
                    ac.created_at as aws_created_at,
                    ac.updated_at as aws_updated_at
                FROM users u
                JOIN aws_customers ac ON u.user_id = ac.user_id
                WHERE ac.customer_identifier = ?
            """
            
            cursor.execute(query, (customer_identifier,))
            row = cursor.fetchone()
            
            if not row:
                add_log("warning", f"未找到customer_identifier对应的用户: {customer_identifier}")
                return None
                
            # 构建用户信息字典
            user_info = {
                'user': {
                    'user_id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'phone': row[3],
                    'org_name': row[4],
                    'role': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'last_login': row[8],
                    'total_chars': row[9],
                    'total_cost': row[10],
                    'points': row[11]
                },
                'aws': {
                    'aws_customer_id': row[12],
                    'customer_identifier': row[13],
                    'aws_account_id': row[14],
                    'product_code': row[15],
                    'subscription_status': row[16],
                    'created_at': row[17],
                    'updated_at': row[18]
                }
            }
            
            # 获取最新的订阅信息
            cursor.execute("""
                SELECT 
                    entitlement_value,
                    dimension_name,
                    valid_from,
                    valid_to,
                    created_at
                FROM aws_subscriptions
                WHERE aws_customer_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (row[12],))
            
            subscription = cursor.fetchone()
            if subscription:
                user_info['subscription'] = {
                    'entitlement_value': subscription[0],
                    'dimension_name': subscription[1],
                    'valid_from': subscription[2],
                    'valid_to': subscription[3],
                    'created_at': subscription[4]
                }
            
            add_log("info", f"成功获取用户信息: {customer_identifier}")
            return user_info
            
        except Exception as e:
            error_msg = f"获取用户信息失败: {str(e)}"
            add_log("error", error_msg)
            raise MarketplaceError(error_msg)
            
        finally:
            if 'conn' in locals():
                conn.close()
                
    # ... (其他方法保持不变) ...