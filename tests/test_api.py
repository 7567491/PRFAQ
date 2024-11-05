import unittest
import requests
from typing import Dict
import os

API_URL = "http://localhost:8000"

class TestAPI(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        # 注册测试用户
        self.test_user = {
            "username": "test_user",
            "email": "test@example.com",
            "password": "test_password"
        }
        
        try:
            response = requests.post(
                f"{API_URL}/auth/register",
                json=self.test_user
            )
            if response.status_code == 200:
                # 登录获取token
                response = requests.post(
                    f"{API_URL}/auth/token",
                    data={
                        "username": self.test_user["username"],
                        "password": self.test_user["password"]
                    }
                )
                self.token = response.json()["access_token"]
            else:
                # 用户可能已存在，直接登录
                response = requests.post(
                    f"{API_URL}/auth/token",
                    data={
                        "username": self.test_user["username"],
                        "password": self.test_user["password"]
                    }
                )
                self.token = response.json()["access_token"]
        except Exception as e:
            self.fail(f"Setup failed: {str(e)}")

    def test_prfaq_generation(self):
        """测试PRFAQ生成"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # 测试PR生成
        pr_data = {
            "type": "pr",
            "customer": "测试客户",
            "scenario": "测试场景",
            "demand": "测试需求",
            "pain": "测试痛点",
            "company": "测试公司",
            "product": "测试产品",
            "feature": "测试特色",
            "benefit": "测试收益"
        }
        response = requests.post(
            f"{API_URL}/prfaq/generate",
            headers=headers,
            json=pr_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("content" in response.json())

if __name__ == '__main__':
    unittest.main()