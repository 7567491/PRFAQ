import json
import requests
from typing import Dict, Any, Generator
import streamlit as st
from .utils import add_letters_record, save_history
from user.logger import add_log
from flask import Blueprint, jsonify, request
from datetime import datetime

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/api/internal-faq/<int:question_id>', methods=['GET'])
def get_internal_faq(question_id):
    """获取内部FAQ答案"""
    internal_faqs = {
        1: "产品独特性分析...",
        2: "产品售后服务流程...", 
        3: "产品定价策略...",
        4: "产品购买渠道...",
        5: "产品促销活动..."
    }
    return jsonify({"answer": internal_faqs.get(question_id, "未找到答案")})

@faq_bp.route('/api/external-faq/<int:question_id>', methods=['GET'])
def get_external_faq(question_id):
    """获取客户FAQ答案"""
    external_faqs = {
        1: "市场规模分析...",
        2: "三年盈利预测...",
        3: "合规风险分析...",
        4: "供应商依赖分析...",
        5: "竞品分析..."
    }
    return jsonify({"answer": external_faqs.get(question_id, "未找到答案")})

class APIClient:
    def __init__(self, config: Dict[str, Any]):
        """初始化API客户端"""
        self.config = config  # 使用传入的配置
        self.full_content = ""  # 初始化为实例变量
        #add_log("info", "APIClient initialized")
        
    def generate_content_stream(self, prompt: str, api_name: str = "claude") -> Generator[str, None, None]:
        """生成内容的流式接口"""
        try:
            #add_log("info", f"Generating content stream for API: {api_name}")
            # 每次生成前清空内容
            self.full_content = ""
            input_letters = len(prompt)
            
            # 准备API请求
            if api_name == "claude":
                headers = {
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": self.config['api_keys'][api_name]
                }
                data = {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                }
            else:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config['api_keys'][api_name]}"
                }
                data = {
                    "model": self.config["models"][api_name],
                    "messages": [
                        {"role": "system", "content": "你是一个专业的产品经理..."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True
                }
            
            # 发送请求
            response = requests.post(
                self.config["api_urls"][api_name],
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                #add_log("info", f"API request successful for {api_name}")
                chunk_count = 0
                
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    line = line.decode('utf-8')
                    
                    if not line.startswith('data: '):
                        continue
                    
                    # 如果是结束标记
                    if line == 'data: [DONE]':
                        break
                    
                    # 处理内容块
                    try:
                        json_str = line[6:]
                        json_data = json.loads(json_str)
                        
                        if api_name == "claude":
                            chunk = json_data.get('delta', {}).get('text', '') or json_data.get('content', '')
                        else:
                            chunk = json_data['choices'][0]['delta'].get('content', '')
                        
                        if chunk:
                            chunk_count += 1
                            self.full_content += chunk
                            yield chunk
                            
                    except json.JSONDecodeError as e:
                        continue
                
                # 在所有内容接收完成后
                if self.full_content:
                    try:
                        # 记录字符统计
                        success = add_letters_record(
                            input_letters=input_letters,
                            output_letters=len(self.full_content),
                            api_name=api_name,
                            operation=f"生成{st.session_state.current_section}内容"
                        )
                        
                        # 保存到历史记录
                        if success:  # 只有在成功记录账单后才保存历史记录
                            save_history(
                                content=self.full_content,
                                history_type=st.session_state.current_section
                            )
                        
                        # 在内容末尾添加字符统计
                        yield f"\n\n生成内容总字符数: {len(self.full_content)}"
                        add_log("info", f"Content generation completed for {api_name}")
                        
                    except Exception as e:
                        add_log("error", f"内容生成错误: {str(e)}")
                        
            else:
                raise Exception(f"API请求失败 (状态码: {response.status_code})")
                
        except Exception as e:
            add_log("error", f"API调用失败: {str(e)}")
            # API切换逻辑
            next_api = None
            if api_name == "claude":
                next_api = "moonshot"
            elif api_name == "moonshot":
                next_api = "zhipu"
                
            if next_api:
                add_log("info", f"尝试下一个API: {next_api}")
                # 不清空 self.full_content，继续累积内容
                yield from self.generate_content_stream(prompt, next_api)
            else:
                # 记录已生成的内容(如果有)
                if self.full_content:
                    try:
                        success = add_letters_record(
                            input_letters=input_letters,
                            output_letters=len(self.full_content),
                            api_name=api_name,
                            operation=f"生成{st.session_state.current_section}内容(部分)"
                        )
                        # 在内容末尾添加字符统计
                        yield f"\n\n生成内容总字符数: {len(self.full_content)}"
                    except Exception as e:
                        add_log("error", f"内容生成部分错误: {str(e)}")
                yield ""