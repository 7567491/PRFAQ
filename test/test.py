import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import sys
from modules.utils import save_history, add_letters_record
import traceback

try:
    from test.utils.test_processor import process_test_results
    from test.utils.result_generator import generate_report
except ImportError as e:
    st.error(f"""
    导入模块失败: {str(e)}
    当前Python路径: {sys.path}
    当前工作目录: {Path.cwd()}
    """)
    raise

class CareerTest:
    def __init__(self):
        self.initialize_session_state()
        st.session_state.test_error = None
            
    def initialize_session_state(self):
        """初始化session state"""
        if 'current_answers' not in st.session_state:
            st.session_state.current_answers = {}
        if 'test_submitted' not in st.session_state:
            st.session_state.test_submitted = False
        if 'current_results' not in st.session_state:
            st.session_state.current_results = None
        if 'test_started' not in st.session_state:
            st.session_state.test_started = False
    
    def save_test_result(self, results):
        """保存测试结果到历史记录"""
        try:
            print("\n=== 开始保存测试结果 ===")
            
            # 生成完整的测评报告
            report = generate_report(results)
            if not report:
                error_msg = "生成报告失败: report 为空"
                print(error_msg)
                st.error(error_msg)
                return False
            
            try:
                # 获取MBTI和霍兰德代码的主要特征
                mbti_type = results.get('mbti_type', 'N/A')
                holland_primary = report.get('personality_traits', {}).get('holland', {}).get('primary', {}).get('title', '未知')
                big5_traits = report.get('personality_traits', {}).get('big5', {})
                leadership_scores = []
                
                # 安全获取领导力得分
                try:
                    raw_scores = report.get('leadership_analysis', {}).get('sorted_scores', [])
                    for score_data in raw_scores:
                        if isinstance(score_data, (list, tuple)) and len(score_data) >= 2:
                            try:
                                principle = str(score_data[0])
                                score = float(score_data[1]) if isinstance(score_data[1], (int, float, str)) else 0.0
                                leadership_scores.append((principle, score))
                            except (ValueError, TypeError) as e:
                                print(f"处理单个领导力得分时出错: {str(e)}")
                                continue
                except Exception as e:
                    print(f"处理领导力得分列表时出错: {str(e)}")
                    leadership_scores = []
                
                # 获取MBTI具体建议
                mbti_advice = {
                    'INTJ': "您是战略家型人才，适合从事需要深度思考和规划的工作。建议发展方向：战略咨询、项目规划、研发管理。",
                    'ENTJ': "您是指挥官型人才，适合担任领导和决策角色。建议发展方向：企业管理、团队领导、业务拓展。",
                    'INTP': "您是逻辑学家型人才，适合从事分析和研究工作。建议发展方向：数据分析、系统架构、学术研究。",
                    'ENTP': "您是辩论家型人才，适合创新和探索性工作。建议发展方向：创业、产品创新、市场策略。",
                    'INFJ': "您是提倡者型人才，适合从事助人和创造性工作。建议发展方向：人力资源、心理咨询、创意设计。",
                    'ENFJ': "您是教导主任型人才，适合培训和引导他人。建议发展方向：培训讲师、团队建设、教育管理。",
                    'INFP': "您是调停者型人才，适合个性化和创意工作。建议发展方向：文案创作、艺术设计、个人咨询。",
                    'ENFP': "您是竞选者型人才，适合人际互动和创新工作。建议发展方向：市场营销、公共关系、创意总监。",
                    'ISTJ': "您是物流师型人才，适合精确和系统化工作。建议发展方向：项目管理、质量控制、财务分析。",
                    'ESTJ': "您是总经理型人才，适合管理和执行工作。建议发展方向：运营管理、行政主管、项目督导。",
                    'ISFJ': "您是守卫者型人才，适合服务和支持性工作。建议发展方向：客户服务、行政支持、医疗护理。",
                    'ESFJ': "您是执政官型人才，适合团队协作和服务工作。建议发展方向：团队协调、客户关系、社区服务。",
                    'ISTP': "您是鉴赏家型人才，适合技术和实践性工作。建议发展方向：技术开发、工程设计、产品测试。",
                    'ESTP': "您是企业家型人才，适合行动导向的工作。建议发展方向：销售管理、风险投资、项目执行。",
                    'ISFP': "您是探险家型人才，适合艺术和体验性工作。建议发展方向：艺术创作、产品设计、体验设计。",
                    'ESFP': "您是表演者型人才，适合互动和表现型工作。建议发展方向：活动策划、销售推广、品牌推广。"
                }
                
                # 生成具体的发展建议
                development_suggestions = self.generate_development_suggestions(
                    mbti_type, 
                    big5_traits, 
                    holland_primary, 
                    leadership_scores
                )
                
                # 安全获取霍兰德代码描述
                holland_description = report.get('personality_traits', {}).get('holland', {}).get('primary', {}).get('description', '暂无具体描述')
                
                # 生成最终显示的文本结果
                final_text = (
                    f"# 职业测评结果报告\n\n"
                    f"## 个性类型分析\n"
                    f"MBTI类型：{mbti_type}\n"
                    f"{mbti_advice.get(mbti_type, '未能获取具体的MBTI类型建议')}\n\n"
                    f"主要职业倾向：{holland_primary}\n"
                    f"{holland_description}\n\n"
                    f"## 人格特征分析\n"
                )
                
                # 安全添加大五人格分析
                try:
                    final_text += "\n".join([f"- {k}: {v.get('interpretation', '暂无解释')}" 
                                           for k, v in big5_traits.items()])
                except Exception as e:
                    print(f"处理大五人格分析时出错: {str(e)}")
                    final_text += "- 暂无详细人格特征分析"
                
                # 安全添加职业建议
                final_text += "\n\n## 推荐职业方向\n"
                try:
                    for suggestion in report.get('career_suggestions', []):
                        final_text += f"### {suggestion.get('title', '未知职业')}\n"
                        for position in suggestion.get('positions', []):
                            final_text += (
                                f"- {position.get('name', '未知职位')}\n"
                                f"  优势匹配：{', '.join(position.get('strengths', ['待评估']))}\n"
                                f"  建议提升：{position.get('improvements', '待评估')}\n"
                            )
                except Exception as e:
                    print(f"处理职业建议时出错: {str(e)}")
                    final_text += "暂无具体职业建议\n"
                
                # 添加发展建议
                final_text += (
                    f"\n## 发展建议\n"
                    f"### 个人优势\n{development_suggestions.get('strengths', '待评估')}\n\n"
                    f"### 短期发展重点\n{development_suggestions.get('improvements', '待评估')}\n\n"
                    f"### 长期发展建议\n{development_suggestions.get('career_path', '待评估')}\n\n"
                    f"### 领导力发展建议\n{development_suggestions.get('leadership', '待评估')}"
                )
                
                try:
                    # 计算字符数和保存结果
                    input_text = "职业测评"
                    
                    # 添加字符使用记录
                    if not add_letters_record(
                        input_letters=len(input_text),
                        output_letters=len(final_text),
                        api_name="career_test",
                        operation="职业测评"
                    ):
                        print("添加字符使用记录失败")
                        return False
                    
                    # 准备历史记录数据
                    history_data = {
                        'user_id': st.session_state.user,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'career_test',
                        'input_text': input_text,
                        'output_text': final_text,
                        'content': final_text  # 保存完整的测评报告
                    }
                    
                    # 保存历史记录
                    from modules.utils import save_history
                    save_history(history_data)
                    
                    # 保存到 session_state 供显示使用
                    st.session_state.final_result = final_text
                    
                    print("=== 测评结果保存成功 ===")
                    return True
                    
                except Exception as e:
                    error_msg = f"保存结果失败: {str(e)}"
                    print(error_msg)
                    st.error(error_msg)
                    return False
                    
            except Exception as e:
                error_msg = f"处理测评数据时出错: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                return False
                
        except Exception as e:
            error_msg = (
                f"\n=== 保存测试结果时发生错误 ===\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}"
            )
            print(error_msg)
            st.error(error_msg)
            return False

    def display_situation_question(self, q, index, current_answers):
        """显示情境选择题"""
        st.write(f"**第{index}题**")
        st.write(q['question'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("A. " + q['options']['A']['text'])
            st.write("B. " + q['options']['B']['text'])
        with col2:
            st.write("C. " + q['options']['C']['text'])
            st.write("D. " + q['options']['D']['text'])
        
        answer = st.radio(
            "您的选择：",
            ['A', 'B', 'C', 'D'],
            key=f"q_{index}",
            index=['A', 'B', 'C', 'D'].index(current_answers.get(index, 'A')),
            horizontal=True
        )
        
        st.divider()
        return answer

    def display_scale_question(self, q, index, current_answers):
        """显示量表题"""
        st.write(f"**第{index}题**")
        st.write(q['question'])
        
        col1, col2 = st.columns([4, 1])
        with col1:
            value = st.slider(
                "符合程度：",
                1, 5,
                current_answers.get(index, 3),
                key=f"q_{index}"
            )
        with col2:
            st.write(
                {
                    1: "完全不符合",
                    2: "比较不符合",
                    3: "一般",
                    4: "比较符合",
                    5: "完全符"
                }[value]
            )
        
        st.divider()
        return value

    def display_rank_question(self, q, index, current_answers):
        """显示排序题"""
        st.write(f"**第{index}题**")
        st.write(q['question'])
        
        col1, col2 = st.columns(2)
        ranks = {}
        used_ranks = set()
        
        with col1:
            st.write("请为每个选项分配1-4的排序（1为最偏好，4为最不偏好）：")
            for opt in ['A', 'B', 'C', 'D']:
                st.write(f"{opt}. {q['options'][opt]['text']}")
        
        with col2:
            for opt in ['A', 'B', 'C', 'D']:
                key = f"{index}_{opt}"
                current_rank = current_answers.get(key, len(used_ranks) + 1)
                rank = st.number_input(
                    f"选项{opt}的排序",
                    min_value=1,
                    max_value=4,
                    value=int(current_rank),
                    key=f"q_{key}"
                )
                ranks[key] = rank
                used_ranks.add(rank)
        
        if len(used_ranks) != 4:
            st.error("请确保每个选项的排序不重复，且都在1-4之间")
        
        st.divider()
        return ranks

    def display_results(self):
        """显示测评结果"""
        if st.session_state.test_submitted and st.session_state.current_results:
            try:
                # 生成报告
                report = generate_report(st.session_state.current_results)
                
                # 获取MBTI和霍兰德代码的主要特征
                mbti_type = st.session_state.current_results.get('mbti_type', 'N/A')
                holland_primary = report.get('personality_traits', {}).get('holland', {}).get('primary', {}).get('title', '未知')
                big5_traits = report.get('personality_traits', {}).get('big5', {})
                
                # 安全获取领导力得分
                leadership_scores = []
                try:
                    raw_scores = report.get('leadership_analysis', {}).get('sorted_scores', [])
                    for score_data in raw_scores:
                        if isinstance(score_data, (list, tuple)) and len(score_data) >= 2:
                            try:
                                principle = str(score_data[0])
                                score = float(score_data[1]) if isinstance(score_data[1], (int, float, str)) else 0.0
                                leadership_scores.append((principle, score))
                            except (ValueError, TypeError) as e:
                                print(f"处理单个领导力得分时出错: {str(e)}")
                                continue
                except Exception as e:
                    print(f"处理领导力得分列表时出错: {str(e)}")
                
                # 获取MBTI具体建议
                mbti_advice = {
                    'INTJ': "您是战略家型人才，适合从事需要深度思考和规划的工作。建议发展方向：战略咨询、项目规划、研发管理。",
                    'ENTJ': "您是指挥官型人才，适合担任领导和决策角色。建议发展方向：企业管理、团队领导、业务拓展。",
                    'INTP': "您是逻辑学家型人才，适合从事分析和研究工作。建议发展方向：数据分析、系统架构、学术研究。",
                    'ENTP': "您是辩论家型人才，适合创新和探索性工作。建议发展方向：创业、产品创新、市场策略。",
                    'INFJ': "您是提倡者型人才，适合从事助人和创造性工作。建议发展方向：人力资源、心理咨询、创意设计。",
                    'ENFJ': "您是教导主任型人才，适合培训和引导他人。建议发展方向：培训讲师、团队建设、教育管理。",
                    'INFP': "您是调停者型人才，适合个性化和创意工作。建议发展方向：文案创作、艺术设计、个人咨询。",
                    'ENFP': "您是竞选者型人才，适合人际互动和创新工作。建议发展方向：市场营销、公共关系、创意总监。",
                    'ISTJ': "您是物流师型人才，适合精确和系统化工作。建议发展方向：项目管理、质量控制、财务分析。",
                    'ESTJ': "您是总经理型人才，适合管理和执行工作。建议发展方向：运营管理、行政主管、项目督导。",
                    'ISFJ': "您是守卫者型人才，适合服务和支持性工作。建议发展方向：客户服务、行政支持、医疗护理。",
                    'ESFJ': "您是执政官型人才，适合团队协作和服务工作。建议发展方向：团队协调、客户关系、社区服务。",
                    'ISTP': "您是鉴赏家型人才，适合技术和实践性工作。建议发展方向：技术开发、工程设计、产品测试。",
                    'ESTP': "您是企业家型人才，适合行动导向的工作。建议发展方向：销售管理、风险投资、项目执行。",
                    'ISFP': "您是探险家型人才，适合艺术和体验性工作。建议发展方向：艺术创作、产品设计、体验设计。",
                    'ESFP': "您是表演者型人才，适合互动和表现型工作。建议发展方向：活动策划、销售推广、品牌推广。"
                }
                
                # 生成具体的发展建议
                development_suggestions = self.generate_development_suggestions(
                    mbti_type, 
                    big5_traits, 
                    holland_primary, 
                    leadership_scores
                )
                
                # 生成完整的文本结果
                final_text = (
                    f"# 职业测评结果报告\n\n"
                    f"## 个性类型分析\n"
                    f"MBTI类型：{mbti_type}\n"
                    f"{mbti_advice.get(mbti_type, '未能获取具体的MBTI类型建议')}\n\n"
                    f"主要职业倾向：{holland_primary}\n"
                    f"{report.get('personality_traits', {}).get('holland', {}).get('primary', {}).get('description', '暂无描述')}\n\n"
                    f"## 人格特征分析\n" + 
                    "\n".join([f"- {k}: {v.get('interpretation', '暂无解释')}" 
                              for k, v in big5_traits.items()]) +
                    f"\n\n## 推荐职业方向\n" +
                    "\n".join([f"### {s.get('title', '未知职业')}\n" +
                              "\n".join([f"- {p.get('name', '未知职位')}\n  优势匹配：{', '.join(p.get('strengths', ['待评估']))}\n  建议提升：{p.get('improvements', '待评估')}" 
                                       for p in s.get('positions', [])])
                              for s in report.get('career_suggestions', [])]) +
                    f"\n\n## 发展建议\n"
                    f"### 个人优势\n{development_suggestions.get('strengths', '待评估')}\n\n"
                    f"### 短期发展重点\n{development_suggestions.get('improvements', '待评估')}\n\n"
                    f"### 长期发展建议\n{development_suggestions.get('career_path', '待评估')}\n\n"
                    f"### 领导力发展建议\n{development_suggestions.get('leadership', '待评估')}"
                )
                
                # 显示结果
                st.markdown(final_text)
                
                # 保存到 session_state 供保存使用
                st.session_state.final_result = final_text
                
                # 添加下载按钮
                st.download_button(
                    label="下载完整报告",
                    data=final_text,
                    file_name="career_assessment_report.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"显示测评结果时出错: {str(e)}")
                add_log("error", f"显示测评结果时出错: {str(e)}")
        else:
            st.info("请完成测评后查看结果")

    def display_intro(self):
        """显示测评介绍"""
        st.write("""
        ## 职业测评系统
        
        欢迎使用职业测评系统！本系统将从以下几个维度对您进行全面的职业倾向评估：
        
        1. 大五人格测评
        2. MBTI性格类型
        3. 霍兰德职业兴趣
        4. 领导力准则匹配度
        
        测评完成后，您将获得：
        - 个性特征分报告
        - 职业发展建议
        - 能力提升计划
        
        点击"开始测评"即可开始您的职业探索之旅！
        """)

    def render(self):
        """渲染主界面"""
        if not st.session_state.test_started:
            # 显示介绍页面
            st.write("""
            ## 职业测评系统
            
            欢迎使用职业测评系统！本系统将从以下几个维度对您进行全面的职业倾向评估：
            
            1. 大五人格测评
            2. MBTI性格类型
            3. 霍兰德职业兴趣
            4. 领导力准则匹配度
            
            测评完成后，您将获得：
            - 个性特征分析报告
            - 职业发展建议
            - 能力提升计划
            
            点击"开始测评"即可开始您的职业探索之旅！
            """)
            
            if st.button("开始测评", type="primary"):
                st.session_state.test_started = True
                st.rerun()
                
        elif not st.session_state.test_submitted:
            # 加载题目
            questions, _ = self.load_data()
            if not questions:
                st.error("无法加载测评题目，请检查数据文件")
                return
                
            # 计算完成进度（确保值在0-1之间）
            total_questions = 29  # 9个选择题 + 8个量表题 + 12个排序题选项
            completed_questions = len(st.session_state.current_answers)
            progress = min(1.0, max(0.0, completed_questions / total_questions))
            
            # 显示测评进度
            st.progress(progress)
            st.write(f"完成: {completed_questions}/{total_questions} 题")
            
            # 第一部分：情境选择题（1-9题）
            st.header("第一部分：情境选择题")
            for i in range(9):
                q = questions[i]
                st.session_state.current_answers[i+1] = self.display_situation_question(
                    q, i+1, st.session_state.current_answers
                )
            
            # 第二部分：行为频率量表题（10-17题）
            st.header("第二部分：行为频率量表题")
            for i in range(9, 17):
                q = questions[i]
                st.session_state.current_answers[i+1] = self.display_scale_question(
                    q, i+1, st.session_state.current_answers
                )
            
            # 第三部分：工作偏好排序题（18-20题）
            st.header("第三部分：工作偏好排序题")
            for i in range(17, 20):
                q = questions[i]
                rank_answers = self.display_rank_question(
                    q, i+1, st.session_state.current_answers
                )
                st.session_state.current_answers.update(rank_answers)
            
            # 提交按钮
            st.divider()
            if st.button("提交测评", type="primary"):
                if self.validate_answers(st.session_state.current_answers):
                    results = process_test_results(st.session_state.current_answers)
                    st.session_state.current_results = results
                    st.session_state.test_submitted = True
                    
                    # 保存结果到历史记录
                    if self.save_test_result(results):
                        st.success('测评完成！')
                        st.rerun()  # 重新加载以显示结果
                    else:
                        st.warning("测评完成，但结果保存失败")
                else:
                    st.error("请确保所有题目都已完成作答")
        
        else:
            # 显示测评结果
            if st.session_state.current_results:
                report = generate_report(st.session_state.current_results)
                
                # 添加重新测评按钮
                if st.button("重新测评", type="primary"):
                    st.session_state.test_started = False
                    st.session_state.test_submitted = False
                    st.session_state.current_answers = {}
                    st.session_state.current_results = None
                    st.rerun()
                
                st.divider()
                
                with st.expander("个性特质分析", expanded=True):
                    # 显示大五人格、MBTI和霍兰德代码分析结果
                    self.display_personality_traits(report)
                
                with st.expander("职业建议", expanded=True):
                    # 显示职业建议
                    self.display_career_suggestions(report)
                
                with st.expander("发展建议", expanded=True):
                    # 显示发展建议
                    self.display_development_suggestions(report)
                
                with st.expander("领导力培养", expanded=True):
                    # 显示领导力分析
                    self.display_leadership_analysis(report)
                
                # 下载报告按钮
                st.download_button(
                    label="下载完整报告",
                    data=json.dumps(report, ensure_ascii=False, indent=2),
                    file_name="career_assessment_report.json",
                    mime="application/json"
                )

    def display_personality_traits(self, report):
        """显示个性特质分析"""
        # 大五人格
        st.subheader("大五人格得分")
        big5_df = pd.DataFrame([
            {
                '维度': k,
                '得分': v['score'],
                '解释': v['interpretation']
            }
            for k, v in report['personality_traits']['big5'].items()
        ])
        st.dataframe(big5_df, use_container_width=True)
        
        # MBTI
        st.subheader("MBTI类型")
        st.write(f"您的类型是：**{report['personality_traits']['mbti']['type']}**")
        st.write(report['personality_traits']['mbti']['description'])
        
        # 霍兰德代码
        st.subheader("霍兰德职业兴趣")
        st.write(f"主要类型：{report['personality_traits']['holland']['primary']['description']}")
        st.write(f"次要类型：{report['personality_traits']['holland']['secondary']['description']}")

    def display_career_suggestions(self, report):
        """显示职业建议"""
        for suggestion in report['career_suggestions']:
            st.subheader(f"推荐职业方向：{suggestion['title']}")
            for pos in suggestion['positions']:
                st.write(f"- **{pos['name']}**")
                st.write(f"  优势：{', '.join(pos['strengths'])}")
                st.write(f"  需要提升：{pos['improvements']}")

    def display_development_suggestions(self, report):
        """显示发展建议"""
        # 短期发展建议
        st.subheader("短期发展建议")
        st.write(report['development_suggestions']['short_term']['strengths'])
        st.write(report['development_suggestions']['short_term']['improvements'])
        
        # 长期发展建议
        st.subheader("长期发展建议")
        st.write(report['development_suggestions']['long_term']['career_path'])
        st.write(report['development_suggestions']['long_term']['leadership'])

    def display_leadership_analysis(self, report):
        """显示领导力分析"""
        st.subheader("领导力则得分")
        scores_df = pd.DataFrame([
            {
                '则': name,
                '得分': data['score']
            }
            for name, data in report['leadership_analysis']['sorted_scores']
        ])
        st.dataframe(scores_df, use_container_width=True)
        
        # 显示高分准则分析
        st.subheader("优势准则分析")
        for analysis in report['leadership_analysis']['top_analysis']:
            with st.container():
                st.write(f"**{analysis['name']}** (得分: {analysis['score']})")
                st.write(analysis['description'])
                st.write(analysis['strength_analysis'])
                st.divider()

    def validate_answers(self, answers):
        """验证所有答案是否完整"""
        try:
            print("\n=== 开始验证答案 ===")
            print(f"当前答案: {json.dumps(answers, ensure_ascii=False, indent=2)}")
            
            # 检查情境选择题（1-9题）
            for i in range(1, 10):
                if i not in answers:
                    error_msg = f"缺少第{i}题的答案"
                    print(error_msg)
                    st.error(error_msg)
                    return False
                if answers[i] not in ['A', 'B', 'C', 'D']:
                    error_msg = f"第{i}题的答案无效: {answers[i]}"
                    print(error_msg)
                    st.error(error_msg)
                    return False
            print("情境选择题验证通过")
            
            # 检查量表题（10-17题）
            for i in range(10, 18):
                if i not in answers:
                    error_msg = f"缺少第{i}题的答案"
                    print(error_msg)
                    st.error(error_msg)
                    return False
                if not isinstance(answers[i], int) or answers[i] < 1 or answers[i] > 5:
                    error_msg = f"第{i}题的答案无效: {answers[i]}"
                    print(error_msg)
                    st.error(error_msg)
                    return False
            print("量表题验证通过")
            
            # 检查排序题（18-20题）
            for i in range(18, 21):
                ranks = set()
                for opt in ['A', 'B', 'C', 'D']:
                    key = f"{i}_{opt}"
                    if key not in answers:
                        error_msg = f"缺少第{i}题选项{opt}的排序"
                        print(error_msg)
                        st.error(error_msg)
                        return False
                    rank = answers[key]
                    if not isinstance(rank, int) or rank < 1 or rank > 4:
                        error_msg = f"第{i}题选项{opt}的排序无效: {rank}"
                        print(error_msg)
                        st.error(error_msg)
                        return False
                    ranks.add(rank)
                if ranks != {1, 2, 3, 4}:
                    error_msg = f"第{i}题的排序不完整或重复: {ranks}"
                    print(error_msg)
                    st.error(error_msg)
                    return False
            print("排序题验证通过")
            
            print("=== 答案验证成功 ===")
            return True
            
        except Exception as e:
            error_msg = (
                f"\n=== 答案验证失败 ===\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}\n"
                f"当前答案: {json.dumps(answers, ensure_ascii=False, indent=2)}"
            )
            print(error_msg)
            st.error(f"验证答案时发生错误: {str(e)}")
            return False

    def load_data(self):
        """加载所有必要的数据文件"""
        try:
            print("\n=== 开始加载数据文件 ===")
            
            # 使用Path来处理路径
            data_dir = Path(__file__).parent / "data"
            print(f"数据目录: {data_dir.absolute()}")
            
            if not data_dir.exists():
                error_msg = f"数据目录不存在: {data_dir}"
                print(error_msg)
                st.error(error_msg)
                return None, None
            
            # 加载题目数据
            questions_file = data_dir / "personality_questions.json"
            if not questions_file.exists():
                error_msg = f"题目文件不存在: {questions_file}"
                print(error_msg)
                st.error(error_msg)
                return None, None
                
            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions = json.load(f)['questions']
                    print(f"成功加载{len(questions)}个题目")
            except json.JSONDecodeError as e:
                error_msg = f"题目文件格式错误: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                return None, None
            except Exception as e:
                error_msg = f"加载题目文件失败: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                return None, None
                    
            # 加载领导力准则数据
            leadership_file = data_dir / "leadership_principles.json"
            if not leadership_file.exists():
                error_msg = f"领导力准则文件不存在: {leadership_file}"
                print(error_msg)
                st.error(error_msg)
                return None, None
                
            try:
                with open(leadership_file, 'r', encoding='utf-8') as f:
                    leadership = json.load(f)['principles']
                    print(f"成功加载{len(leadership)}个领导力准则")
            except json.JSONDecodeError as e:
                error_msg = f"领导力准则文件格式错误: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                return None, None
            except Exception as e:
                error_msg = f"加载领导力准则文件失败: {str(e)}"
                print(error_msg)
                st.error(error_msg)
                return None, None
            
            print("=== 数据文件加载成功 ===")
            return questions, leadership
                
        except Exception as e:
            error_msg = (
                f"\n=== 加载数据文件失败 ===\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}"
            )
            print(error_msg)
            st.error(f"加载数据文件失败: {str(e)}")
            return None, None

    def display_final_result(self, result_text):
        """显示最终结果"""
        st.markdown("## 职业测评结果")
        st.markdown(result_text)
        
        # 保存最终结果到 session_state
        st.session_state.final_result = result_text

    def generate_development_suggestions(self, mbti_type, big5_traits, holland_primary, leadership_scores):
        """生成具体的发展建议"""
        # 基于MBTI的优势分析
        mbti_strengths = {
            'INTJ': ["战略思维能力", "独立分析能力", "创新规划能力"],
            'ENTJ': ["领导决策能力", "目标管理能力", "团队建设能力"],
            'INTP': ["逻辑分析能力", "问题解决能力", "系统思维能力"],
            'ENTP': ["创新思维能力", "适应变化能力", "沟通说服能力"],
            'INFJ': ["洞察力", "同理心", "创造力"],
            'ENFJ': ["人际影响力", "团队激励能力", "发展他人能力"],
            'INFP': ["创意表达能力", "价值观建设能力", "个性化服务能力"],
            'ENFP': ["人际关系能力", "创新思维能力", "激励感染力"],
            'ISTJ': ["执行力", "细节把控能力", "流程管理能力"],
            'ESTJ': ["组织管理能力", "实施执行能力", "目标达成能力"],
            'ISFJ': ["服务意识", "责任心", "团队协作能力"],
            'ESFJ': ["人际协调能力", "服务意识", "团队合作能力"],
            'ISTP': ["实践操作能力", "问题解决能力", "危机处理能力"],
            'ESTP': ["行动力", "资源整合能力", "机会把握力"],
            'ISFP': ["艺术审美能力", "实践能力", "适应能力"],
            'ESFP': ["表现力", "人际交往能力", "现场应变能力"]
        }
        
        # 获取具体优势
        strengths = mbti_strengths.get(mbti_type, ["分析能力", "执行能力", "沟通能力"])
        
        # 基于大五人格的发展建议
        improvement_areas = []
        for trait, data in big5_traits.items():
            score = float(data.get('score', 0))  # 确保score是浮点数
            if score < 0.4:  # 低分特质需要提升
                if trait == 'O':
                    improvement_areas.append("创新思维和开放性思维")
                elif trait == 'C':
                    improvement_areas.append("计划性和组织性")
                elif trait == 'E':
                    improvement_areas.append("社交技能和表达能力")
                elif trait == 'A':
                    improvement_areas.append("团队协作和人际关系")
                elif trait == 'N':
                    improvement_areas.append("压力管理和情绪调节")
        
        # 基于霍兰德代码的职业发展路径
        career_paths = {
            "研究型": "可以向专业技术专家、研究员或技术主管方向发展，注重专业深度",
            "艺术型": "可以向创意总监、设计主管或艺术总监方向发展，发挥创造力",
            "社会型": "可以向人力资源总监、培训总监或咨询顾问方向发展，善用人际优势",
            "企业型": "可以向项目经理、业务总监或创业者方向发展，发挥领导才能",
            "常规型": "可以向运营总监、质量总监或流程管理专家方向发展，强化系统能力",
            "实践型": "可以向技术总监、工程总监或产品经理方向发展，突出实践能力"
        }
        
        # 获取职业发展路径建议
        career_path = career_paths.get(holland_primary, "建议往专业管理者方向发展，持续提升领导力和专业能力")
        
        # 生成领导力发展建议
        leadership_dev = []
        for principle_data in leadership_scores[:3]:
            try:
                principle = principle_data[0]  # 获取准则名称
                score = float(principle_data[1])  # 获取分数并转换为浮点数
                
                if score > 0.7:  # 高分准则
                    leadership_dev.append(f"充分发挥您在{principle}方面的优势（得分：{score:.2f}），可以担任相关领域的项目负责人")
                else:  # 需要提升的准则
                    leadership_dev.append(f"建议通过实践项目来强化{principle}方面的能力（当前得分：{score:.2f}）")
            except (IndexError, TypeError, ValueError) as e:
                print(f"处理领导力得分时出错: {str(e)}")
                continue
        
        # 如果没有有效的领导力建议，添加默认建议
        if not leadership_dev:
            leadership_dev = ["建议通过参与项目实践来提升领导力", 
                            "可以从小型项目开始，逐步承担更多责任"]
        
        # 整合所有建议
        suggestions = {
            'strengths': f"您的优势在于：\n" + "\n".join([f"- {s}" for s in strengths]),
            'improvements': f"短期内可以重点提升：\n" + "\n".join([f"- {i}" for i in improvement_areas]) if improvement_areas else "您的各项能力都比较均衡，建议：\n- 继续保持并深化现有优势\n- 在工作中尝试承担更具挑战性的任务",
            'career_path': f"建议的职业发展路径：\n{career_path}",
            'leadership': f"领导力发展建议：\n" + "\n".join([f"- {l}" for l in leadership_dev])
        }
        
        return suggestions
