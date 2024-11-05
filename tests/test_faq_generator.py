import unittest
from unittest.mock import Mock, patch
import streamlit as st
from modules.faq_generator import FAQGenerator

class TestFAQGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = Mock()
        self.faq_generator = FAQGenerator(self.mock_api_client)

    @patch('streamlit.button')
    def test_generate_customer_faq(self, mock_button):
        """测试客户FAQ生成功能"""
        # 模拟按钮点击
        mock_button.return_value = True
        
        # 模拟API响应
        self.mock_api_client.generate_content_stream.return_value = ["测试回答"]
        
        # 执行测试
        with patch('streamlit.markdown') as mock_markdown:
            self.faq_generator.generate_customer_faq()
            
            # 验证API调用
            self.mock_api_client.generate_content_stream.assert_called()
            
            # 验证结果显示
            mock_markdown.assert_called_with("测试回答") 