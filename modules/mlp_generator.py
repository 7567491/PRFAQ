import streamlit as st
import json
from typing import Optional
from .api import APIClient
from .utils import load_prompts, add_log

class MLPGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()

    def generate_mlp(self):
        """生成MLP开发计划"""
        st.header("MLP 开发")
        
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
        if st.button("生成MLP开发计划", key="generate_mlp"):
            add_log("user", "👉 点击生成MLP开发计划")
            
            # 获取mlp提示词
            try:
                prompts = self.prompts
                mlp_prompt = prompts.get("mlp", {}).get("prompt")
                
                if not mlp_prompt:
                    st.error("未找到MLP提示词配置")
                    add_log("error", "❌ 未找到MLP提示词配置")
                    return
                
                # 构建完整提示词，替换${core_sentence}占位符
                prompt = mlp_prompt.replace(
                    "${core_sentence}", 
                    full_core_sentence
                )
                
                add_log("info", "🚀 开始生成MLP开发计划")
                
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
                    
                    add_log("info", "✨ MLP开发计划生成完成")
                    
                except Exception as e:
                    error_msg = f"生成MLP开发计划时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")
                
            except Exception as e:
                error_msg = f"读取提示词配置时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}") 