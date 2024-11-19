"""
AWS Marketplace Customer Manager
"""
import boto3
import json
import sqlite3
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
            
    def resolve_customer(self, token: str) -> Dict[str, Any]:
        """
        Resolve customer information from registration token
        
        Args:
            token: Registration token from AWS Marketplace
            
        Returns:
            Dict with customer information
            
        Raises:
            AuthenticationError: If token resolution fails
        """
        try:
            add_log("info", "开始解析客户token...")
            
            # Validate token
            if not self.validate_token(token):
                raise AuthenticationError("Invalid token format")
                
            # Call ResolveCustomer API
            response = self.metering_client.resolve_customer(
                RegistrationToken=token
            )
            
            # Extract customer information
            customer_info = {
                'customer_identifier': response['CustomerIdentifier'],
                'customer_aws_account_id': response['CustomerAWSAccountId'],
                'product_code': response['ProductCode']
            }
            
            add_log("info", f"客户token解析成功: {customer_info['customer_identifier']}")
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