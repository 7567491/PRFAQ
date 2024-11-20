"""
AWS Marketplace 测试客户模拟模块
"""
import base64
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from modules.utils import add_log

def generate_test_token() -> str:
    """
    生成测试用的Token
    
    Returns:
        str: Base64编码的测试Token
    """
    try:
        # 创建测试数据
        test_data = {
            'CustomerIdentifier': f"test_{str(uuid.uuid4())[:8]}",
            'CustomerAWSAccountId': f"{str(uuid.uuid4())}",
            'ProductCode': 'test_product_001',
            'Timestamp': datetime.now().isoformat()
        }
        
        # 转换为JSON并编码
        json_data = json.dumps(test_data)
        token = base64.b64encode(json_data.encode()).decode()
        
        add_log("info", f"生成测试Token: {test_data['CustomerIdentifier']}")
        return token
        
    except Exception as e:
        error_msg = f"生成测试Token失败: {str(e)}"
        add_log("error", error_msg)
        raise ValueError(error_msg)

def simulate_callback(token: str) -> Dict[str, Any]:
    """
    模拟AWS Marketplace的URL回调
    
    Args:
        token: 测试Token
        
    Returns:
        Dict: 模拟的回调结果
    """
    try:
        # 解码Token
        json_data = base64.b64decode(token.encode()).decode()
        data = json.loads(json_data)
        
        # 构建回调结果
        result = {
            'CustomerIdentifier': data['CustomerIdentifier'],
            'CustomerAWSAccountId': data['CustomerAWSAccountId'],
            'ProductCode': data['ProductCode']
        }
        
        add_log("info", f"模拟回调成功: {result['CustomerIdentifier']}")
        return result
        
    except Exception as e:
        error_msg = f"模拟回调失败: {str(e)}"
        add_log("error", error_msg)
        raise ValueError(error_msg)