import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log, save_history
from datetime import datetime
import json
from pathlib import Path

def load_aar_prompts():
    """Load AAR prompts from prompt-aar.json"""
    prompt_path = Path("config/prompt-aar.json")
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return json.load(file)["aar"]

class AARGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_aar_prompts()  # Load prompts from JSON
        self.context = ""  # 存储全局Context
        self.data_fact = ""  # 存储全局Data_fact
        
    def render(self):
        """渲染AAR复盘生成界面"""
        st.header("AAR 复盘")
        
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
        
        # 初始化表单数据
        if 'aar_form_data' not in st.session_state:
            st.session_state.aar_form_data = {
                'project_purpose': '产品推广',
                'project_goal': '找到100个种子用户',
                'project_conditions': '3个人，1个月，1万元'
            }
        
        # 显示表单
        with st.form("aar_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                project_purpose = st.text_input("项目目的 (Why)", value=st.session_state.aar_form_data['project_purpose'])
                project_goal = st.text_input("项目目标 (What)", value=st.session_state.aar_form_data['project_goal'])
            
            with col2:
                project_conditions = st.text_input("项目条件 (How)", value=st.session_state.aar_form_data['project_conditions'])
            
            submitted = st.form_submit_button("生成复盘中心句")
        
        # 如果点击生成中心句按钮
        if submitted:
            # 更新表单数据到session state
            st.session_state.aar_form_data = {
                'project_purpose': project_purpose,
                'project_goal': project_goal,
                'project_conditions': project_conditions
            }
            
            # 生成Context
            self.context = (
                f"这是一次项目管理的复盘，首先请记住，本项目的性质和目的是{project_purpose}，项目目标是{project_goal}，项目条件是{project_conditions}。"
                f"该项目中涉及产品的客户需求和解决方案如下：\n"
                f"客户需求：{core_sentence.get('customer_needs', '')}\n"
                f"解决方案：{core_sentence.get('solution', '')}\n"
                
            )
            
            # 保存Context到session state
            st.session_state.aar_context = self.context
            st.session_state.aar_data_fact = self.context
        
        # 显示可编辑的中心句
        if 'aar_context' in st.session_state:
            st.markdown("### 复盘中心句")
            st.session_state.aar_context = st.text_area("编辑复盘中心句", value=st.session_state.aar_context, height=150)
        
        # 显示开始复盘按钮（放在表单外）
        if st.button("开始复盘", key="start_review", use_container_width=True):
            # 设置 context 和 data_fact 的初值
            self.context = st.session_state.aar_context
            self.data_fact = st.session_state.aar_context
            st.session_state.aar_generation_started = True
        
        # 如果已经开始生成，显示生成步骤
        if 'aar_generation_started' in st.session_state and st.session_state.aar_generation_started:
            self._generate_all_steps()

    def _generate_all_steps(self):
        """生成所有复盘内容"""
        # 生成前三步
        self._generate_first_three_steps()
        
        # 直接生成后三步
        self._generate_last_three_steps()

    def _generate_first_three_steps(self):
        """生成前三步复盘内容"""
        if 'aar_first_three_done' in st.session_state:
            return
        
        # 第一步：设定目标
        self._generate_step("step1", "标设定")
        
        # 第二步：指定具体计划
        self._generate_step("step2_1", "指定具体计划")
        
        # 第二步：过程复盘
        self._generate_step("step2_2", "过程复盘")
        
        # 第三步：结果比较
        self._generate_step("step3", "结果比较")
        
        st.session_state.aar_first_three_done = True

    def _generate_last_three_steps(self):
        """生成后三步复盘内容"""
        if 'aar_last_three_done' in st.session_state:
            return
        
        # 归因分析
        self._generate_step("step4", "归因分析")
        
        # 经验总结
        self._generate_step("step5_1", "经验总结")
        
        # 教训总结
        self._generate_step("step5_2", "教训总结")
        
        # 形成文档
        self._generate_step("step6", "形成文档")
        
        st.session_state.aar_last_three_done = True

    def _generate_step(self, step_key: str, step_title: str):
        """通用步骤生成方法"""
        st.markdown(f"### {self.prompts['steps'][step_key]['title']}")
        
        prompt = self.prompts['steps'][step_key]['prompt'].format(
            context=self.context,
            data_fact=self.data_fact,
            project_name=st.session_state.aar_form_data['project_purpose'],
            team_size=st.session_state.aar_form_data['project_conditions'],
            time_period=st.session_state.aar_form_data['project_conditions']
        )
        
        response_placeholder = st.empty()  # 使用空占位符来更新内容
        try:
            add_log("info", f"🚀 开始生成{step_title}...")
            full_response = ""
            
            for chunk in self.api_client.generate_content_stream(prompt):
                full_response += chunk
                # 使用 unsafe_allow_html=True 来渲染 HTML 标签
                response_placeholder.markdown(full_response, unsafe_allow_html=True)
            
            # 更新Context和data_fact
            self.data_fact += f"\n\n{step_title}：\n{full_response}"
            self.context += f"\n\n{step_title}：\n{full_response}"
            
            add_log("info", f"✨ {step_title}生成完成")
            
            # 保存到session state
            st.session_state.aar_context = self.context
            st.session_state.aar_data_fact = self.data_fact
            
            # 添加分隔线
            st.markdown("---")
            
        except Exception as e:
            error_msg = f"生成{step_title}时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")