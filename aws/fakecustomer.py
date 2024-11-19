"""
AWS Marketplace Customer Authentication Simulator
"""
import streamlit as st
import base64
import json
import time
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from modules.utils import add_log
from .exceptions import AuthenticationError
from .customer_manager import CustomerManager

class MarketplaceSimulator:
    """AWS Marketplace simulator for testing"""
    
    def __init__(self):
        """Initialize simulator"""
        self.customer_mgr = CustomerManager()
        self._init_test_data()
        
    def _init_test_data(self):
        """Initialize test data"""
        # 模拟产品数据
        self.test_product = {
            'product_code': f'prod-{str(uuid.uuid4())[:8]}',
            'product_name': 'Test SaaS Product',
            'pricing_dimension': 'Users',
            'pricing_unit': 'Count',
            'price': '100.00'
        }
        
        # 模拟客户数据
        self.test_customer = {
            'customer_id': f'cust-{str(uuid.uuid4())[:8]}',
            'aws_account_id': '123456789012',
            'email': 'test@example.com',
            'company': 'Test Company'
        }
        
    def _generate_test_token(self) -> str:
        """Generate test registration token"""
        # 创建token payload
        payload = {
            'customerId': self.test_customer['customer_id'],
            'productCode': self.test_product['product_code'],
            'timestamp': int(time.time()),
            'nonce': str(uuid.uuid4()),
            'signature': None
        }
        
        # 使用当前时间作为密钥生成签名
        key = str(time.time()).encode()
        message = json.dumps(payload, sort_keys=True).encode()
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        
        # 添加签名到payload
        payload['signature'] = signature
        
        # Base64编码
        token = base64.b64encode(json.dumps(payload).encode()).decode()
        add_log("info", f"生成测试Token: {payload['customerId']}")
        return token
        
    def _verify_token(self, token: str) -> bool:
        """Verify test token"""
        try:
            # 解码token
            decoded = json.loads(base64.b64decode(token))
            
            # 验证必要字段
            required_fields = ['customerId', 'productCode', 'timestamp', 'signature']
            if not all(field in decoded for field in required_fields):
                add_log("error", "Token缺少必要字段")
                return False
                
            # 验证时间戳(10分钟有效期)
            token_time = datetime.fromtimestamp(decoded['timestamp'])
            if datetime.now() - token_time > timedelta(minutes=10):
                add_log("error", "Token已过期")
                return False
                
            add_log("info", "Token验证通过")
            return True
            
        except Exception as e:
            add_log("error", f"Token验证失败: {str(e)}")
            return False
            
    def run_test_flow(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Run complete test flow
        
        Returns:
            (success, message, test_data)
        """
        try:
            # Step 1: 生成测试Token
            add_log("info", "步骤1: 生成测试Token")
            token = self._generate_test_token()
            
            # Step 2: 验证Token
            add_log("info", "步骤2: 验证Token")
            if not self._verify_token(token):
                raise AuthenticationError("Token验证失败")
                
            # Step 3: 模拟客户信息
            add_log("info", "步骤3: 生成客户信息")
            customer_info = {
                'customer_identifier': self.test_customer['customer_id'],
                'customer_aws_account_id': self.test_customer['aws_account_id'],
                'product_code': self.test_product['product_code']
            }
            
            # Step 4: 存储客户信息
            add_log("info", "步骤4: 存储客户信息")
            test_user_id = 1  # 测试用户ID
            
            # 存储前检查数据库连接
            try:
                import sqlite3
                conn = sqlite3.connect('db/users.db')
                cursor = conn.cursor()
                
                # 检查users表结构
                add_log("info", "检查users表结构...")
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = {col[1] for col in cursor.fetchall()}
                add_log("info", f"现有列: {existing_columns}")
                
                required_columns = {
                    'user_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
                    'username': 'TEXT NOT NULL UNIQUE',
                    'password': 'TEXT NOT NULL',
                    'email': 'TEXT',
                    'role': 'TEXT DEFAULT "user"',
                    'status': 'INTEGER DEFAULT 1',
                    'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
                }
                
                # 如果表不存在，创建完整的表
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='users'
                """)
                if not cursor.fetchone():
                    add_log("info", "users表不存在，创建新表...")
                    create_users_sql = f"""
                        CREATE TABLE users (
                            {', '.join(f'{col} {dtype}' for col, dtype in required_columns.items())}
                        )
                    """
                    cursor.execute(create_users_sql)
                    conn.commit()
                    add_log("info", "users表创建成功")
                else:
                    # 检查并添加缺失的列
                    missing_columns = set(required_columns.keys()) - existing_columns
                    if missing_columns:
                        add_log("info", f"发现缺失的列: {missing_columns}")
                        for col in missing_columns:
                            try:
                                alter_sql = f"ALTER TABLE users ADD COLUMN {col} {required_columns[col]}"
                                add_log("info", f"添加列: {alter_sql}")
                                cursor.execute(alter_sql)
                                conn.commit()
                                add_log("info", f"成功添加列: {col}")
                            except Exception as e:
                                add_log("error", f"添加列 {col} 失败: {str(e)}")
                                raise
                
                # 检查用户是否存在
                add_log("info", "检查测试用户...")
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", ('1',))
                if not cursor.fetchone():
                    # 如果测试用户不存在，创建一个
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    insert_sql = """
                        INSERT INTO users (
                            user_id, 
                            username, 
                            password, 
                            email, 
                            role, 
                            is_active, 
                            created_at,
                            total_chars,
                            total_cost,
                            daily_chars_limit,
                            used_chars_today,
                            points,
                            status
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """
                    cursor.execute(insert_sql, (
                        '1',                    # user_id (TEXT)
                        'test_user',           # username
                        'test_password',       # password
                        'test@example.com',    # email
                        'user',               # role
                        1,                    # is_active
                        current_time,         # created_at
                        0,                    # total_chars
                        0.0,                  # total_cost
                        100000,              # daily_chars_limit
                        0,                    # used_chars_today
                        1000,                # points
                        1                    # status
                    ))
                    conn.commit()
                    add_log("info", f"创建测试用户成功 ID: 1")
                else:
                    add_log("info", "测试用户已存在")
                
                # 检查aws_customers表结构
                add_log("info", "检查aws_customers表结构...")
                cursor.execute("PRAGMA table_info(aws_customers)")
                existing_aws_columns = {col[1] for col in cursor.fetchall()}
                add_log("info", f"现有AWS列: {existing_aws_columns}")
                
                # 如果aws_customers表已存在但结构不正确，需要重建表
                if 'aws_customers' in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                    if 'id' in existing_aws_columns and 'aws_customer_id' not in existing_aws_columns:
                        add_log("info", "需要重建aws_customers表...")
                        
                        # 重命名旧表
                        cursor.execute("ALTER TABLE aws_customers RENAME TO aws_customers_old")
                        
                        # 创建新表
                        cursor.execute("""
                            CREATE TABLE aws_customers (
                                aws_customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id TEXT NOT NULL,
                                customer_identifier TEXT NOT NULL,
                                aws_account_id TEXT NOT NULL,
                                product_code TEXT NOT NULL,
                                subscription_status INTEGER DEFAULT 1,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users(user_id),
                                UNIQUE (customer_identifier)
                            )
                        """)
                        
                        # 复制数据
                        cursor.execute("""
                            INSERT INTO aws_customers (
                                aws_customer_id, user_id, customer_identifier, 
                                aws_account_id, product_code, subscription_status,
                                created_at, updated_at
                            )
                            SELECT 
                                id, user_id, customer_identifier,
                                aws_account_id, product_code, subscription_status,
                                created_at, updated_at
                            FROM aws_customers_old
                        """)
                        
                        # 删除旧表
                        cursor.execute("DROP TABLE aws_customers_old")
                        
                        conn.commit()
                        add_log("info", "aws_customers表重建完成")
                else:
                    # 如果表不存在，直接创建新表
                    add_log("info", "创建新的aws_customers表...")
                    cursor.execute("""
                        CREATE TABLE aws_customers (
                            aws_customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT NOT NULL,
                            customer_identifier TEXT NOT NULL,
                            aws_account_id TEXT NOT NULL,
                            product_code TEXT NOT NULL,
                            subscription_status INTEGER DEFAULT 1,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (user_id) REFERENCES users(user_id),
                            UNIQUE (customer_identifier)
                        )
                    """)
                    conn.commit()
                    add_log("info", "aws_customers表创建成功")
                
                # 验证最终表结构
                cursor.execute("PRAGMA table_info(aws_customers)")
                final_columns = {col[1] for col in cursor.fetchall()}
                add_log("info", f"最终aws_customers表列: {final_columns}")
                
                conn.close()
                add_log("info", "数据库表结构验证完成")
                
            except Exception as e:
                error_msg = f"检查/创建数据库表失败: {str(e)}\n"
                error_msg += f"错误类型: {type(e).__name__}\n"
                
                # 获取最后执行的SQL（如果可用）
                if 'cursor' in locals():
                    try:
                        # 获取表结构信息作为调试信息
                        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
                        table_info = cursor.fetchall()
                        error_msg += "数据库表结构:\n"
                        for table in table_info:
                            error_msg += f"{table[0]}\n"
                    except:
                        error_msg += "无法获取表结构信息\n"
                        
                    try:
                        # 获取最后一个错误的表名
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                        tables = cursor.fetchall()
                        error_msg += f"现有表: {[t[0] for t in tables]}\n"
                    except:
                        error_msg += "无法获取表名信息\n"
                
                add_log("error", error_msg)
                raise Exception(error_msg)
            
            # 存储客户信息
            self.customer_mgr.store_customer_info(test_user_id, customer_info)
            
            # 验证存储结果
            stored_info = self.customer_mgr.get_customer_info(test_user_id)
            if not stored_info:
                raise Exception("客户信息存储验证失败")
            
            add_log("info", f"客户信息存储验证成功: {stored_info}")
            
            # 返回测试数据
            test_data = {
                'token': token,
                'customer': self.test_customer,
                'product': self.test_product,
                'stored_info': stored_info,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return True, "测试流程执行成功", test_data
            
        except Exception as e:
            error_msg = f"测试流程失败: {str(e)}"
            add_log("error", error_msg)
            return False, error_msg, {}

def show_simulation_panel():
    """Display simulation panel"""
    st.title("AWS Marketplace 模拟测试")
    
    # 显示模拟测试说明
    st.markdown("""
    ### 模拟测试说明
    
    本模块模拟AWS Marketplace的客户注册和验证流程，包括：
    
    1. **Token生成与验证**
       - 生成模拟的注册Token
       - 验证Token的格式和有效期
       - 提取客户和产品信息
    
    2. **客户信息处理**
       - 解析客户标识符
       - 验证AWS账户信息
       - 关联产品订阅
    
    3. **数据存储**
       - 保存客户信息
       - 记录订阅状态
       - 建立用户关联
    
    4. **完整性验证**
       - 验证数据一致性
       - 检查关联关系
       - 确认存储结果
    """)
    
    # 创建测试选项
    st.subheader("测试选项")
    test_type = st.radio(
        "选择测试类型",
        ["完整流程测试", "Token验证测试", "客户信息测试"],
        help="选择要执行的测试类型"
    )
    
    # 创建测试按钮
    if st.button("开始测试", key="start_test"):
        # 初始化模拟器
        simulator = MarketplaceSimulator()
        
        # 创建进度显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            if test_type == "完整流程测试":
                # 执行完整测试流程
                status_text.text("执行完整测试流程...")
                progress_bar.progress(25)
                time.sleep(1)
                
                # 运行测试
                success, message, test_data = simulator.run_test_flow()
                progress_bar.progress(100)
                
                if success:
                    status_text.text("测试完成!")
                    st.success(message)
                    
                    # 显示测试数据
                    st.subheader("测试结果")
                    
                    # 分开显示不同类型的数据
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("📝 生成的测试数据")
                        st.json({
                            "客户信息": test_data['customer'],
                            "产品信息": test_data['product'],
                            "测试时间": test_data['timestamp']
                        })
                        
                    with col2:
                        st.write("💾 数据库存储结果")
                        if 'stored_info' in test_data:
                            st.json(test_data['stored_info'])
                        else:
                            st.warning("未找到存储数据")
                    
                    # 显示验证步骤
                    st.subheader("验证步骤")
                    st.write("✅ Token生成")
                    st.write("✅ Token验证")
                    st.write("✅ 客户信息处理")
                    st.write("✅ 数据存储")
                    
                    # 显示数据库查询按钮
                    if st.button("查询数据库", key="query_db"):
                        try:
                            import sqlite3
                            conn = sqlite3.connect('db/users.db')
                            cursor = conn.cursor()
                            
                            # 查询aws_customers表
                            cursor.execute("""
                                SELECT ac.*, u.username 
                                FROM aws_customers ac
                                JOIN users u ON ac.user_id = u.id
                                WHERE ac.user_id = 1
                            """)
                            columns = [description[0] for description in cursor.description]
                            results = cursor.fetchall()
                            
                            if results:
                                st.success("找到数据库记录")
                                # 将结果转换为字典列表
                                records = [dict(zip(columns, row)) for row in results]
                                st.json(records)
                            else:
                                st.warning("数据库中未找到记录")
                                
                            conn.close()
                            
                        except Exception as e:
                            st.error(f"查询数据库失败: {str(e)}")
                    
                else:
                    status_text.text("测试失败!")
                    st.error(message)
                    
            elif test_type == "Token验证测试":
                # 仅执行Token验证测试
                status_text.text("执行Token验证测试...")
                progress_bar.progress(50)
                
                # 生成并验证Token
                token = simulator._generate_test_token()
                valid = simulator._verify_token(token)
                progress_bar.progress(100)
                
                if valid:
                    status_text.text("Token验证成功!")
                    st.success("Token验证测试通过")
                    st.code(token, language="text")
                else:
                    status_text.text("Token验证失败!")
                    st.error("Token验证测试失败")
                    
            else:  # 客户信息测试
                # 执行客户信息测试
                status_text.text("执行客户信息测试...")
                progress_bar.progress(50)
                
                # 生成测试数据
                customer_info = {
                    'customer_identifier': simulator.test_customer['customer_id'],
                    'customer_aws_account_id': simulator.test_customer['aws_account_id'],
                    'product_code': simulator.test_product['product_code']
                }
                
                # 存储并验证
                simulator.customer_mgr.store_customer_info(1, customer_info)
                stored_info = simulator.customer_mgr.get_customer_info(1)
                progress_bar.progress(100)
                
                if stored_info:
                    status_text.text("客户信息测试完成!")
                    st.success("客户信息测试通过")
                    st.json(stored_info)
                else:
                    status_text.text("客户信息测试失败!")
                    st.error("客户信息测试失败")
                    
        except Exception as e:
            status_text.text(f"测试出错: {str(e)}")
            st.error(f"测试过程中出现错误: {str(e)}")
            add_log("error", f"模拟测试失败: {str(e)}")