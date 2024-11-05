import streamlit as st
import requests
from typing import Dict
from utils import add_log

def generate_content(type: str, data: dict):
    """通用生成内容函数"""
    try:
        # 创建占位符
        result_container = st.empty()
        content = ""
        
        # 添加日志
        add_log("开始生成内容...", st.session_state)
        
        # 发送请求
        with st.spinner('正在生成内容...'):
            with requests.post(
                f"{st.session_state.API_URL}/prfaq/generate",
                headers={
                    "Authorization": f"Bearer {st.session_state.token}",
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                json={"type": type, **data},
                stream=True
            ) as response:
                add_log(f"请求状态码: {response.status_code}", st.session_state)
                
                if response.status_code == 200:
                    # 使用迭代器处理流式响应
                    for line in response.iter_lines():
                        if line:
                            try:
                                line = line.decode('utf-8')
                                add_log(f"收到数据: {line[:50]}...", st.session_state)
                                
                                if line.startswith('data: '):
                                    chunk = line[6:]  # 去掉'data: '前缀
                                    if chunk.startswith('[ERROR]'):
                                        st.error(chunk[8:])  # 去掉'[ERROR] '前缀
                                        break
                                    else:
                                        # 直接显示新收到的内容
                                        result_container.markdown(
                                            f"""
                                            ### 生成结果
                                            <div class="generated-content">
                                            {chunk}
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )
                                        content = chunk  # 保存最新内容
                            except Exception as e:
                                error_msg = f"解析响应失败: {str(e)}"
                                add_log(error_msg, st.session_state)
                                add_log(f"原始数据: {line}", st.session_state)
                                continue
                else:
                    error_msg = f"请求失败: {response.status_code}"
                    add_log(error_msg, st.session_state)
                    try:
                        error_detail = response.json()["detail"]
                        add_log(error_detail, st.session_state)
                    except:
                        add_log("无法解析错误信息", st.session_state)
                    
    except Exception as e:
        error_msg = f"生成失败: {str(e)}"
        add_log(error_msg, st.session_state)
        st.error(error_msg)
    finally:
        # 生成完成后，显示最终内容
        if content:
            st.markdown("### 最终生成结果")
            st.markdown(
                f"""
                <div class="generated-content">
                {content}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown("---")
            add_log("生成完成", st.session_state)
        else:
            st.warning("未生成任何内容")
            add_log("生成失败：未生成任何内容", st.session_state)

def generate_pr():
    """PR生成页面"""
    st.subheader("生成新闻稿")
    
    with st.form("pr_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer = st.text_input("客户", value="产品经理")
            demand = st.text_input("需求", value="希望产品畅销的需求")
            company = st.text_input("公司", value="六页纸团队")
            feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿")
        
        with col2:
            scenario = st.text_input("场景", value="开发新产品的场景")
            pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点")
            product = st.text_input("产品", value="PRFAQ生成器")
            benefit = st.text_input("收益", value="打造以客户为中心的产品文案")
        
        submitted = st.form_submit_button("生成新闻稿")
        
        if submitted:
            data = {
                "customer": customer,
                "scenario": scenario,
                "demand": demand,
                "pain": pain,
                "company": company,
                "product": product,
                "feature": feature,
                "benefit": benefit
            }
            generate_content("pr", data)

def generate_customer_faq():
    """客户FAQ生成页面"""
    st.subheader("生成客户FAQ")
    
    with st.form("customer_faq_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer = st.text_input("客户", value="产品经理", key="faq_customer")
            demand = st.text_input("需求", value="希望产品畅销的需求", key="faq_demand")
            company = st.text_input("公司", value="六页纸团队", key="faq_company")
            feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿", key="faq_feature")
        
        with col2:
            scenario = st.text_input("场景", value="开发新产品的场景", key="faq_scenario")
            pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点", key="faq_pain")
            product = st.text_input("产品", value="PRFAQ生成器", key="faq_product")
            benefit = st.text_input("收益", value="打造以客户为中心的产品文案", key="faq_benefit")
        
        submitted = st.form_submit_button("生成客户FAQ")
        
        if submitted:
            data = {
                "customer": customer,
                "scenario": scenario,
                "demand": demand,
                "pain": pain,
                "company": company,
                "product": product,
                "feature": feature,
                "benefit": benefit
            }
            generate_content("faq", data)

def generate_internal_faq():
    """内部FAQ生成页面"""
    st.subheader("生成内部FAQ")
    
    with st.form("internal_faq_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer = st.text_input("客户", value="产品经理", key="internal_customer")
            demand = st.text_input("需求", value="希望产品畅销的需求", key="internal_demand")
            company = st.text_input("公司", value="六页纸团队", key="internal_company")
            feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿", key="internal_feature")
        
        with col2:
            scenario = st.text_input("场景", value="开发新产品的场景", key="internal_scenario")
            pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点", key="internal_pain")
            product = st.text_input("产品", value="PRFAQ生成器", key="internal_product")
            benefit = st.text_input("收益", value="打造以客户为中心的产品文案", key="internal_benefit")
        
        submitted = st.form_submit_button("生成内部FAQ")
        
        if submitted:
            data = {
                "customer": customer,
                "scenario": scenario,
                "demand": demand,
                "pain": pain,
                "company": company,
                "product": product,
                "feature": feature,
                "benefit": benefit
            }
            generate_content("internal_faq", data)

def generate_mlp():
    """MLP开发计划生成页面"""
    st.subheader("生成MLP开发计划")
    
    with st.form("mlp_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer = st.text_input("客户", value="产品经理", key="mlp_customer")
            demand = st.text_input("需求", value="希望产品畅销的需求", key="mlp_demand")
            company = st.text_input("公司", value="六页纸团队", key="mlp_company")
            feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿", key="mlp_feature")
        
        with col2:
            scenario = st.text_input("场景", value="开发新产品的场景", key="mlp_scenario")
            pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点", key="mlp_pain")
            product = st.text_input("产品", value="PRFAQ生成器", key="mlp_product")
            benefit = st.text_input("收益", value="打造以客户为中心的产品文案", key="mlp_benefit")
        
        submitted = st.form_submit_button("生成MLP开发计划")
        
        if submitted:
            data = {
                "customer": customer,
                "scenario": scenario,
                "demand": demand,
                "pain": pain,
                "company": company,
                "product": product,
                "feature": feature,
                "benefit": benefit
            }
            generate_content("mlp", data)