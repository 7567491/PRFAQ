import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log, save_history
from datetime import datetime

class AARGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()
        self.context = ""  # 存储全局Context
        self.data_fact = ""  # 存储全局Data_fact
        
    def render(self):
        """渲染AAR复盘生成界面"""
        st.header("AAR 复盘")
        
        # 初始化表单数据
        if 'aar_form_data' not in st.session_state:
            st.session_state.aar_form_data = {
                'customer_name': '产品经理',
                'demand': '做复盘的需求',
                'product_solution': '六页软件',
                'customer_value': '用AI迅速高效完成结构完整逻辑严密的复盘',
                'project_name': '陆业科技团队',
                'team_size': '3',
                'time_period': '1个月',
                'project_type': '原型产品的开发和推广'
            }
        
        # 显示表单
        with st.form("aar_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                customer_name = st.text_input("客户名称", value=st.session_state.aar_form_data['customer_name'])
                demand = st.text_input("需求", value=st.session_state.aar_form_data['demand'])
                product_solution = st.text_input("产品和解决方案", value=st.session_state.aar_form_data['product_solution'])
                customer_value = st.text_input("客户价值", value=st.session_state.aar_form_data['customer_value'])
            
            with col2:
                project_name = st.text_input("项目名称", value=st.session_state.aar_form_data['project_name'])
                team_size = st.text_input("团队人数", value=st.session_state.aar_form_data['team_size'])
                time_period = st.text_input("时间", value=st.session_state.aar_form_data['time_period'])
                project_type = st.text_input("项目类型", value=st.session_state.aar_form_data['project_type'])
            
            submitted = st.form_submit_button("生成复盘中心句")
        
        # 如果点击生成中心句按钮
        if submitted:
            # 更新表单数据到session state
            st.session_state.aar_form_data = {
                'customer_name': customer_name,
                'demand': demand,
                'product_solution': product_solution,
                'customer_value': customer_value,
                'project_name': project_name,
                'team_size': team_size,
                'time_period': time_period,
                'project_type': project_type
            }
            
            # 生成Context
            self.context = (
                f"{customer_name}有{demand}的需求，通过{product_solution}，帮助客户实现{customer_value}。\n"
                f"{project_name}由{team_size}位成员组成，使用{time_period}时间，完成{project_type}。"
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
            st.session_state.aar_generation_started = True
        
        # 如果已经开始生成，显示生成步骤
        if 'aar_generation_started' in st.session_state and st.session_state.aar_generation_started:
            self._generate_all_steps()

    def _generate_all_steps(self):
        """生成所有复盘内容"""
        # 生成前三步
        self._generate_first_three_steps()
        
        # 生成后三步
        self._generate_last_three_steps()

    def _generate_first_three_steps(self):
        """生成前三步复盘内容"""
        if 'aar_first_three_done' in st.session_state:
            return
        
        st.markdown("### 第一步：设定目标")
        
        # 构建提示词
        prompt = f"""请为一次{st.session_state.aar_form_data['project_name']}制定一个可量化的产出指标，和三个可控可量化的投入指标，投入指标包括人天、预算等。

{self.context}

在制定目标的时候，请使用一些尽量接近的数字，使其显得更加真实"""
        
        # 生成内容
        response_placeholder = st.empty()
        try:
            add_log("info", "🚀 开始生成目标设定...")
            full_response = ""
            
            for chunk in self.api_client.generate_content_stream(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response)
            
            # 更新Context和data_fact
            self.data_fact = full_response
            self.context += f"\n\n目标设定：\n{full_response}"
            
            add_log("info", "✨ 目标设定生成完成")
            
            # 保存到session state
            st.session_state.aar_context = self.context
            st.session_state.aar_data_fact = self.data_fact
            
            # 继续生成第二步和第三步...
            self._generate_step_two_and_three()
            
        except Exception as e:
            error_msg = f"生成目标设定时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")
    
    def _generate_step_two_and_three(self):
        """生成第二步和第三步内容"""
        if 'aar_first_three_done' in st.session_state:
            return
        
        # 2.1 指定具体计划
        st.markdown("### 第2.1步：指定具体计划")
        
        plan_prompt = f"""请为一次{st.session_state.aar_form_data['project_name']}制定可实施的工作计划，组建一个{st.session_state.aar_form_data['team_size']}人团队做好分工，并说明每个人每周所要达成的具体工作：

{self.context}"""
        
        plan_placeholder = st.empty()
        try:
            add_log("info", "🚀 开始生成具体计划...")
            plan_response = ""
            
            for chunk in self.api_client.generate_content_stream(plan_prompt):
                plan_response += chunk
                plan_placeholder.markdown(plan_response)
            
            # 更新Context和data_fact
            self.data_fact += f"\n\n具体计划：\n{plan_response}"
            self.context += f"\n\n具体计划：\n{plan_response}"
            
            add_log("info", "✨ 具体计划生成完成")
            
            # 每次更新data_fact和context后都保存到session state
            st.session_state.aar_context = self.context
            st.session_state.aar_data_fact = self.data_fact
            
            # 2.2 过程复盘
            st.markdown("### 第2.2步：过程复盘")
            
            process_prompt = f"""请根据以下工作计划，模拟每个人实际每周所作的工作，梳理这个项目的过程。
请按照时间顺序，按周列举每个实际发生的任务，每个任务用不超过50字进行陈述，包括时间、地点、人物、任务、具体动作和结果，并说出该任务的投入是否达到预期。

{self.context}"""
            
            process_placeholder = st.empty()
            try:
                add_log("info", "🚀 开始生成过程复盘...")
                process_response = ""
                
                for chunk in self.api_client.generate_content_stream(process_prompt):
                    process_response += chunk
                    process_placeholder.markdown(process_response)
                
                # 更新Context和data_fact
                self.data_fact += f"\n\n过程复盘：\n{process_response}"
                self.context += f"\n\n过程复盘：\n{process_response}"
                
                add_log("info", "✨ 过程复盘生成完成")
                
                # 每次更新data_fact和context后都保存到session state
                st.session_state.aar_context = self.context
                st.session_state.aar_data_fact = self.data_fact
                
                # 3. 结果比较
                st.markdown("### 第3步：结果比较")
                
                result_prompt = f"""请为一次{st.session_state.aar_form_data['project_name']}作复盘分析，标记出highlight和lowlight。

{self.context}

请使用模拟数字，模拟生成实际数据。
请比较实际数据和目标，分为四种情况：
如果实际数据超过目标120%以上，则标记为-超出预期；标为Highlight
如果实际数据位于目标70-120%之间，标记为达到预期；
如果实际数据位于目标50-70%之间，标记为未达到预期，
如果实际数据不到目标50%，标记为远未达到预期。标为Lowlight"""
                
                result_placeholder = st.empty()
                try:
                    add_log("info", "🚀 开始生成结果比较...")
                    result_response = ""
                    
                    for chunk in self.api_client.generate_content_stream(result_prompt):
                        result_response += chunk
                        result_placeholder.markdown(result_response)
                    
                    # 更新Context和data_fact
                    self.data_fact += f"\n\n结果比较：\n{result_response}"
                    self.context += f"\n\n结果比较：\n{result_response}"
                    
                    add_log("info", "✨ 结果比较生成完成")
                    
                    # 更新状态
                    st.session_state.aar_first_three_done = True
                    
                except Exception as e:
                    error_msg = f"生成结果比较时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"生成过程复盘时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}")
                
        except Exception as e:
            error_msg = f"生成具体计划时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")

    def _generate_last_three_steps(self):
        """生成后三步复盘内容"""
        if 'aar_last_three_done' in st.session_state:
            return
        
        # 恢复之前的context和data_fact
        if hasattr(st.session_state, 'aar_context'):
            self.context = st.session_state.aar_context
        if hasattr(st.session_state, 'aar_data_fact'):
            self.data_fact = st.session_state.aar_data_fact
        
        # 4. 归因分析
        st.markdown("### 第4步：归因分析")
        
        cause_prompt = f"""请你针对{st.session_state.aar_form_data['project_name']}，作原因分析、规律总结和行动计划。

{self.data_fact}

分析达到目标的3个原因，其中2个为可控的主观原因，1个为客观的不可控原因，
以及没有达到目标的3个原因，其中2个为可控的主观原因，1个客观的不可控原因。
每个原因使用五个为什么进行追因，从而找到根本原因，每个追因分析的答案，追因分析需要非常具体并且可量化。
请按主观/客观、达到目标/未达到目标四个象限，以表格的形式进行输出。"""
        
        cause_placeholder = st.empty()
        try:
            add_log("info", "🚀 开始生成归因分析...")
            cause_response = ""
            
            for chunk in self.api_client.generate_content_stream(cause_prompt):
                cause_response += chunk
                cause_placeholder.markdown(cause_response)
            
            # 更新Context
            self.context += f"\n\n归因分析：\n{cause_response}"
            
            add_log("info", "✨ 归因分析生成完成")
            
            # 5.1 经验(Highlight)总结
            st.markdown("### 第5.1步：经验(Highlight)总结")
            
            highlight_prompt = f"""请你针对以下经营数据的一个highlight作原因分析、可复用的规律总结：

{self.data_fact}

每个原因使用五个为什么进行追因，从而找到根本原因，每个追因分析的答案，追因分析需要非常具体并且可量化，从而找到这项Hightligh的、可量化的根本可控输入指标是什么。

分析原因之后，请总结这项hightlight的可复用的经验。
在保证哪一个质量指标的前提下可以继续加大哪些方面的投入。"""
            
            highlight_placeholder = st.empty()
            try:
                add_log("info", "🚀 开始生成Highlight总结...")
                highlight_response = ""
                
                for chunk in self.api_client.generate_content_stream(highlight_prompt):
                    highlight_response += chunk
                    highlight_placeholder.markdown(highlight_response)
                
                # 更新Context
                self.context += f"\n\n经验总结：\n{highlight_response}"
                
                add_log("info", "✨ Highlight总结生成完成")
                
                # 5.2 教训(Lowlight)总结
                st.markdown("### 第5.2步：教训(Lowlight)总结")
                
                lowlight_prompt = f"""请你针对以下经营数据的一个lowlight作原因分析、改进的行动计划、制定一个如何避免再次发生的机制：

{self.data_fact}

每个原因使用五个为什么进行追因，从而找到根本原因，每个追因分析的答案，追因分析需要非常具体并且可量化，从而找到这项lowlight的根本可控输入指标是什么。

分析原因之后，给出一个具体的改进计划，改进计划要有具体负责人、时间线、达到程度。
制定一项避免这项Lowlight再次发生的机制，以避免同样的错误再次发生。"""
                
                lowlight_placeholder = st.empty()
                try:
                    add_log("info", "🚀 开始生成Lowlight总结...")
                    lowlight_response = ""
                    
                    for chunk in self.api_client.generate_content_stream(lowlight_prompt):
                        lowlight_response += chunk
                        lowlight_placeholder.markdown(lowlight_response)
                    
                    # 更新Context
                    self.context += f"\n\n教训总结：\n{lowlight_response}"
                    
                    add_log("info", "✨ Lowlight总结生成完成")
                    
                    # 6. 形成文档
                    st.markdown("### 第6步：形成文档")
                    
                    doc_prompt = f"""把以下内容总结成不超过500字的一段话：

{self.context}"""
                    
                    doc_placeholder = st.empty()
                    try:
                        add_log("info", "🚀 开始生成最终文档...")
                        doc_response = ""
                        
                        for chunk in self.api_client.generate_content_stream(doc_prompt):
                            doc_response += chunk
                            doc_placeholder.markdown(doc_response)
                        
                        # 保存到历史记录
                        save_history({
                            'content': self.context + f"\n\n最终总结：\n{doc_response}",
                            'type': 'aar',
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        add_log("info", "✨ 复盘文档生成完成")
                        
                        # 显示导出按钮
                        if st.button("导出完整复盘文档", key="export_document"):
                            self._export_document()
                        
                    except Exception as e:
                        error_msg = f"生成最终文档时发生错误: {str(e)}"
                        st.error(error_msg)
                        add_log("error", f"❌ {error_msg}")
                    
                except Exception as e:
                    error_msg = f"生成Lowlight总结时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")
                
            except Exception as e:
                error_msg = f"生成Highlight总结时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}")
            
        except Exception as e:
            error_msg = f"生成归因分析时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")
        
        # 在生成完所有步骤后，更新状态机状态
        st.session_state.aar_state = 'completed'
        st.session_state.aar_last_three_done = True
        
        # 保存最终结果
        st.session_state.aar_final_context = self.context

    def _export_document(self):
        """导出完整的复盘文档"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"AAR_{timestamp}.txt"
            
            # 使用st.download_button来提供下载功能
            st.download_button(
                label="下载复盘文档",
                data=st.session_state.aar_final_context.encode('utf-8'),
                file_name=filename,
                mime='text/plain'
            )
            
            add_log("info", f"✅ 成功导出文件: {filename}")
            
        except Exception as e:
            error_msg = f"导出文件时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")

    def _show_final_result(self):
        """显示最终的复盘结果"""
        st.markdown("### 复盘结果")
        
        # 确保最终内容已保存
        if 'aar_final_context' not in st.session_state:
            st.session_state.aar_final_context = self.context
        
        # 显示完整内容
        if st.session_state.aar_final_context:
            st.markdown(st.session_state.aar_final_context)
            
            # 导出按钮
            col1, col2 = st.columns([1, 4])  # 创建两列，按钮占1份，空白占4份
            with col1:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"AAR_{timestamp}.txt"
                
                st.download_button(
                    label="下载复盘文档",
                    data=st.session_state.aar_final_context.encode('utf-8'),
                    file_name=filename,
                    mime='text/plain',
                    use_container_width=True
                )
                add_log("info", f"✅ 成功导出文件: {filename}")
            
            # 重新生成按钮
            with col2:
                if st.button("重新生成", key="regenerate_aar"):
                    # 清除复盘相关的状态
                    for key in ['aar_state', 'aar_context', 'aar_data_fact', 'aar_final_context']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
        else:
            st.error("复盘结果未找到")
            add_log("error", "❌ 复盘结果未找到")