import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log  # 从utils导入add_log
from modules.notifier import send_wecom_message  # 改用新的导入路径

class PRGenerator:
    def __init__(self, api_client: APIClient, all_in_one: bool = False):
        self.api_client = api_client
        self.all_in_one = all_in_one
        self.prompts = load_prompts()

    def render(self):
        """渲染PR生成界面"""
        st.header("PR 生成")
        
        # 自定义所有按钮样式
        st.markdown("""
            <style>
            /* 通用按钮样式 */
            .stButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                color: #ffffff;
            }
            
            /* 表单提交按钮（生成电梯谈话中心句）样式 */
            .stFormSubmitButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                width: auto;
                float: left;
            }
            
            /* 鼠标悬停效果 */
            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                border-color: #ffb84d;
                color: #ffb84d;
                background-color: rgba(255, 153, 0, 0.1);
            }
            
            /* 点击效果 */
            .stButton > button:active,
            .stFormSubmitButton > button:active {
                border-color: #cc7a00;
                color: #cc7a00;
                background-color: rgba(255, 153, 0, 0.2);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 创建输入表单
        with st.form("pr_form"):
            # 创建两列布局
            col1, col2 = st.columns(2)
            
            # 左列
            with col1:
                customer = st.text_input("客户", value="产品经理")
                demand = st.text_input("需求", value="希望产品畅销的需求")
                company = st.text_input("公司", value="六页纸团队")
                feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿")
            
            # 右列
            with col2:
                scenario = st.text_input("场景", value="开发新产品的场景")
                pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点")
                product = st.text_input("产品", value="PRFAQ生成器")
                benefit = st.text_input("收益", value="打造以客户为中心的产品文案")
            
            # 生成按钮左对齐
            generate_core = st.form_submit_button("生成电梯谈话中心句")
            if generate_core:
                add_log("user", "👉 点击生成电梯谈话中心句")
        
        # 如果点击生成中心句按钮或已经存在中心句
        if generate_core or 'product_core_sentence' in st.session_state:
            if generate_core:
                # 初始化中心句
                customer_needs = f"{customer}在{scenario}下，有{demand}，但他存在{pain}"
                solution = f"{company}开发了{product}，通过{feature}，帮助客户实现{benefit}"
                
                st.session_state.product_core_sentence = {
                    'customer_needs': customer_needs,
                    'solution': solution
                }
                add_log("info", "✅ 成功生成中心句")
            
            # 显示可编辑的中心句（带颜色预览）
            st.markdown("### 产品中心句")
            
            # 获取当前的中心句
            current_needs = st.session_state.product_core_sentence['customer_needs']
            current_solution = st.session_state.product_core_sentence['solution']
            
            # 合并成一个完整的中心句
            combined_core_sentence = f"客户需求：{current_needs}\n解决方案：{current_solution}"
            
            # 创建单个可编辑的文本区域
            edited_text = st.text_area(
                "编辑中心句", 
                value=combined_core_sentence,
                height=100
            )
            
            # 解析编辑后的文本，分离客户需求和解决方案
            try:
                # 分割文本
                parts = edited_text.split('\n')
                edited_needs = parts[0].replace('客户需求：', '').strip()
                edited_solution = parts[1].replace('解决方案：', '').strip()
                
                # 更新session state中的中心句
                st.session_state.product_core_sentence = {
                    'customer_needs': edited_needs,
                    'solution': edited_solution
                }
            except Exception as e:
                st.error("中心句格式错误，请确保包含'客户需求：'和'解决方案：'两行")
                return

            # 生成新闻稿按钮
            if st.button("生成新闻稿", key="generate_pr"):
                add_log("user", "👉 点击生成新闻稿")
                
                # 构建完整提示词
                prompt = f"""你扮演一名专业的产品经理，你能够使用亚马逊prfaq的格式生成虚拟新闻稿。

客户需求：{edited_needs}
解决方案：{edited_solution}

请生成一份虚拟新闻稿，包含标题、副标题、时间和媒体名称、摘要、客户需求和痛点、解决方案和产品价值、客户旅程，
提供一位行业大咖（使用真实名字）证言，并提供两个客户（使用虚拟名字，包含姓名、公司、职位）证言，最后号召用户购买。"""

                # 显示提示词
                st.markdown("### 合成提示词")
                st.text_area(
                    label="",  # 移除标签
                    value=prompt,
                    height=200,  # 减小高度
                    disabled=True,  # 设置为不可编辑
                    key="prompt_display"
                )
                add_log("info", "✅ 成功生成提示词")
                
                # 生成新闻稿
                st.markdown("### 生成的虚拟新闻稿")
                
                # 创建一个空的占位符用于流式输出
                response_placeholder = st.empty()
                
                try:
                    add_log("info", "🚀 开始生成新闻稿...")
                    # 初始化响应文本
                    full_response = ""
                    
                    # 流式生成内容
                    for chunk in self.api_client.generate_content_stream(prompt):
                        full_response += chunk
                        # 实时更新显示的内容
                        response_placeholder.markdown(full_response)
                    
                    add_log("info", "✨ 新闻稿生成完成")
                    
                except Exception as e:
                    error_msg = f"生成内容时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")

    def generate_content(self):
        send_wecom_message('action', st.session_state.user,
            action="生成PR内容",
            details=f"核心理念：{st.session_state.get('product_core_sentence', '未知')}"
        )
        # 原有的生成逻辑