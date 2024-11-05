import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log, save_history
from datetime import datetime
import json

class AllInOneGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()
        self.all_content = []  # 存储所有生成的内容

    def render(self):
        """渲染一键生成界面"""
        st.header("PRFAQ 一键生成")
        
        # 添加按钮样式
        st.markdown("""
            <style>
            .stButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                color: #ffffff;
            }
            
            .stFormSubmitButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                width: auto;
                float: left;
            }
            
            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                border-color: #ffb84d;
                color: #ffb84d;
                background-color: rgba(255, 153, 0, 0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 使用与PR生成器相同的表单布局
        with st.form("all_in_one_form"):
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
            generate_all = st.form_submit_button("一键生成所有内容")
        
        if generate_all:
            add_log("user", "👉 点击一键生成所有内容")
            
            # 1. 生成中心句
            customer_needs = f"{customer}在{scenario}下，有{demand}，但他存在{pain}"
            solution = f"{company}开发了{product}，通过{feature}，帮助客户实现{benefit}"
            
            st.session_state.product_core_sentence = {
                'customer_needs': customer_needs,
                'solution': solution
            }
            
            # 显示中心句
            st.markdown("### 产品中心句")
            formatted_core_sentence = (
                f"**客户需求：**`{customer_needs}`\n\n"
                f"**解决方案：**`{solution}`"
            )
            st.markdown(formatted_core_sentence)
            self.all_content.append(("产品中心句", f"客户需求：{customer_needs}\n解决方案：{solution}"))
            add_log("info", "✅ 成功生成中心句")
            
            # 2. 生成PR
            st.markdown("### 虚拟新闻稿")
            pr_prompt = f"""你扮演一名专业的产品经理，你能够使用亚马逊prfaq的格式生成虚拟新闻稿。

客户需求：{customer_needs}
解决方案：{solution}

请生成一份虚拟新闻稿，包含标题、副标题、时间和媒体名称、摘要、客户需求和痛点、解决方案和产品价值、客户旅程，
提供一位行业大咖（使用真实名字���证言，并提供两个客户（使用虚拟名字，包含姓名、公司、职位）证言，最后号召用户购买。"""
            
            pr_content = self._generate_content("新闻稿", pr_prompt)
            if pr_content:
                self.all_content.append(("虚拟新闻稿", pr_content))
            
            # 3. 生成客户FAQ
            st.markdown("### 客户FAQ")
            try:
                customer_faqs = self.prompts.get("customer_faq", {})
                for question_id, faq_data in customer_faqs.items():
                    st.subheader(faq_data['title'])
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        f"客户需求：{customer_needs}\n解决方案：{solution}"
                    )
                    content = self._generate_content(f"客户FAQ-{faq_data['title']}", prompt)
                    if content:
                        self.all_content.append((f"客户FAQ-{faq_data['title']}", content))
            except Exception as e:
                add_log("error", f"❌ 生成客户FAQ时发生错误: {str(e)}")
            
            # 4. 生成内部FAQ
            st.markdown("### 内部FAQ")
            try:
                internal_faqs = self.prompts.get("internal_faq", {})
                for question_id, faq_data in internal_faqs.items():
                    st.subheader(faq_data['title'])
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        f"客户需求：{customer_needs}\n解决方案：{solution}"
                    )
                    content = self._generate_content(f"内部FAQ-{faq_data['title']}", prompt)
                    if content:
                        self.all_content.append((f"内部FAQ-{faq_data['title']}", content))
            except Exception as e:
                add_log("error", f"❌ 生成内部FAQ时发生错误: {str(e)}")
            
            # 5. 生成MLP开发计划
            st.markdown("### MLP开发计划")
            try:
                mlp_prompt = self.prompts.get("mlp", {}).get("prompt", "").replace(
                    "${core_sentence}", 
                    f"客户需求：{customer_needs}\n解决方案：{solution}"
                )
                content = self._generate_content("MLP开发计划", mlp_prompt)
                if content:
                    self.all_content.append(("MLP开发计划", content))
            except Exception as e:
                add_log("error", f"❌ 生成MLP开发计划时发生错误: {str(e)}")
            
            # 6. 在生成完所有内容后，显示字数统计
            if self.all_content:
                st.markdown("### 内容统计")
                
                # 计算每个部分的字数
                stats = []
                total_chars = 0
                
                for section_name, content in self.all_content:
                    chars = len(content)
                    total_chars += chars
                    stats.append({
                        "部分": section_name,
                        "字数": chars,
                    })
                
                # 添加总计行
                stats.append({
                    "部分": "总计",
                    "字数": total_chars,
                })
                
                # 使用pandas创建表格
                import pandas as pd
                df = pd.DataFrame(stats)
                
                # 显示表格
                st.dataframe(
                    df.style.format({
                        "字数": "{:,}",  # 添加千位分隔符
                    }),
                    use_container_width=True
                )
                
                # 准备下载内容
                content = ""
                for section_name, section_content in self.all_content:
                    content += f"\n{'='*50}\n"
                    content += f"{section_name}\n"
                    content += f"{'='*50}\n\n"
                    content += section_content
                    content += "\n\n"
                
                # 使用 streamlit 的下载按钮
                st.download_button(
                    label="导出完整文档",
                    data=content.encode('utf-8'),
                    file_name=f"PRFAQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime='text/plain'
                )
                
                # 保存到历史记录
                save_history({
                    'content': content,
                    'type': 'all_in_one',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                add_log("info", "✅ 已保存到历史记录")

    def _generate_content(self, section_name: str, prompt: str) -> Optional[str]:
        """生成内容并显示"""
        try:
            add_log("info", f"🚀 开始生成{section_name}...")
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in self.api_client.generate_content_stream(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response)
            
            add_log("info", f"✨ {section_name}生成完成")
            return full_response
            
        except Exception as e:
            error_msg = f"生成{section_name}时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")
            return None

    def _export_to_file(self):
        """导出所有内容到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"PRFAQ_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                for section_name, content in self.all_content:
                    f.write(f"\n{'='*50}\n")
                    f.write(f"{section_name}\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(content)
                    f.write("\n\n")
            
            add_log("info", f"✅ 成功导出文件: {filename}")
            st.success(f"文件已导出: {filename}")
            
        except Exception as e:
            error_msg = f"导出文件时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}") 