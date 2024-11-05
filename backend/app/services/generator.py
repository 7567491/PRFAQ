from typing import Optional, AsyncGenerator
from ..models.database import SessionLocal, APIUsage
import aiohttp
import json
import os
from typing import Dict, Any
import sys
import logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from config import CLAUDE_API_KEY

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PRFAQGenerator:
    def __init__(self):
        self.api_key = CLAUDE_API_KEY
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
            "x-api-key": self.api_key
        }

    async def generate_stream(
        self,
        type: str,
        customer: str,
        scenario: str,
        demand: str,
        pain: str,
        company: str,
        product: str,
        feature: str,
        benefit: str
    ) -> AsyncGenerator[str, None]:
        """流式生成PRFAQ内容"""
        # 构建提示词
        core_sentence = (
            f"{customer}在{scenario}下，有{demand}，但他存在{pain}\n"
            f"{company}开发了{product}，通过{feature}，帮助客户实现{benefit}"
        )
        
        prompts = {
            "pr": f"""你扮演一名专业的产品经理，使用亚马逊prfaq格式生成虚拟新闻稿。
            
{core_sentence}

请生成一份虚拟新闻稿，包含标题、副标题、时间和媒体名称、摘要、客户需求和痛点、解决方案和产品价值、客户旅程，
提供一位行业大咖（使用真实名字）证言，并提供两个客户（使用虚拟名字，包含姓名、公司、职位）证言，最后号召用户购买。""",
            
            "faq": f"""基于以下产品信息，生成5个最常见的客户问题和答案：

{core_sentence}

问题应该涵盖：市场规模、盈利预测、合规风险、供应商依赖、竞品分析等方面。""",
            
            "internal_faq": f"""基于以下产品信息，生成5个内部FAQ问答：

{core_sentence}

问题应该涵盖：产品独特性、售后服务、定价策略、购买渠道、促销活动等方面。""",
            
            "mlp": f"""基于以下产品信息，生成最小可行产品(MVP)开发计划：

{core_sentence}

包含：核心功能定义、技术方案、开发周期、测试计划、上线策略等内容。"""
        }
        
        # 调用Claude API
        data = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": prompts[type]
                }
            ]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API请求失败: {error_text}")
                        raise Exception(f"API请求失败: {error_text}")
                    
                    result = await response.json()
                    logger.info(f"API响应: {result}")
                    
                    if 'content' in result and len(result['content']) > 0:
                        content = result['content'][0]['text']
                        # 一次性返回全部内容
                        yield content
                    else:
                        logger.error(f"API响应格式错误: {result}")
                        raise Exception("API响应格式错误")
                        
        except Exception as e:
            logger.error(f"生成内容时发生错误: {str(e)}")
            raise

    async def record_usage(self, user_id: int, total_chars: int):
        """记录API使用情况"""
        db = SessionLocal()
        try:
            cost = total_chars * 0.000003
            usage = APIUsage(
                user_id=user_id,
                api_name="claude",
                input_chars=total_chars,
                output_chars=total_chars,
                cost=cost
            )
            db.add(usage)
            db.commit()
        finally:
            db.close()