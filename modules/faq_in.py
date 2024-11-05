import streamlit as st
import json
from typing import Optional
from .api import APIClient
from .utils import load_prompts, add_log

class InternalFAQGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()

    def generate_internal_faq(self):
        """生成内部FAQ内容"""
        st.header("内部 FAQ")
        
        # 检查全局产品中心句
        if 'product_core_sentence' not in st.session_state:
            st.warning("请先在PR生成模块生成产品中心句")
            return
            
        # 显示产品中心句
        core_sentence = st.session_state.product_core_sentence
        st.markdown("### 产品中心句")
        
        # 合并显示客户需求和解决方案，并添加高亮
        if isinstance(core_sentence, dict):
            formatted_core_sentence = (
                f"**客户需求：**`{core_sentence.get('customer_needs', '')}`\n\n"
                f"**解决方案：**`{core_sentence.get('solution', '')}`"
            )
            st.markdown(formatted_core_sentence)
            
            # 合并成完整的中心句用于提示词
            full_core_sentence = (
                f"客户需求：{core_sentence.get('customer_needs', '')}\n"
                f"解决方案：{core_sentence.get('solution', '')}"
            )
        else:
            st.error("产品中心句格式错误")
            return

        # 创建生成按钮
        if st.button("一键生成内部FAQ", key="generate_all_internal_faq"):
            add_log("user", "👉 点击一键生成内部FAQ")
            
            # 获取internal_faq提示词
            try:
                prompts = self.prompts  # 使用初始化时加载的提示词
                internal_faqs = prompts.get("internal_faq", {})
                
                if not internal_faqs:
                    st.error("未找到内部FAQ提示词配置")
                    add_log("error", "❌ 未找到内部FAQ提示词配置")
                    return
                
                # 遍历生成每个FAQ的答案
                for question_id, faq_data in internal_faqs.items():
                    st.subheader(faq_data['title'])
                    add_log("info", f"🚀 开始生成问题: {faq_data['title']}")
                    
                    # 构建完整提示词，替换${core_sentence}占位符
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        full_core_sentence
                    )
                    
                    # 创建占位符用于流式输出
                    response_placeholder = st.empty()
                    
                    try:
                        # 初始化响应文本
                        full_response = ""
                        
                        # 流式生成内容
                        for chunk in self.api_client.generate_content_stream(prompt):
                            full_response += chunk
                            # 实时更新显示的内容
                            response_placeholder.markdown(full_response)
                        
                        add_log("info", f"✨ 问题 {faq_data['title']} 生成完成")
                        
                    except Exception as e:
                        error_msg = f"生成问题 {faq_data['title']} 时发生错误: {str(e)}"
                        st.error(error_msg)
                        add_log("error", f"❌ {error_msg}")
                    
                    # 添加分隔线
                    st.markdown("---")
                
                add_log("info", "✅ 所有内部FAQ生成完成")
                
            except Exception as e:
                error_msg = f"读取提示词配置时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}") 