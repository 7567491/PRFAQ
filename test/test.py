import streamlit as st
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
import plotly.express as px
import sys
from modules.utils import save_history, add_letters_record
import traceback
import plotly.graph_objects as go

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
            from modules.utils import add_log
            
            add_log("info", "=== 开始保存测试结果 ===")
            add_log("info", f"原始结果数据: {json.dumps(results, ensure_ascii=False)}")
            
            # 生成完整的测评报告
            report = generate_report(results)
            if not report:
                error_msg = "生成报告失败: report 为空"
                add_log("error", error_msg)
                st.error(error_msg)
                return False
            
            add_log("info", "报告生成成功，准备保存到历史记录")
            
            try:
                # 准备历史记录数据
                history_data = {
                    'user_id': st.session_state.user,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'leadership_test',
                    'input_text': "领导力测评",
                    'output_text': json.dumps(report, ensure_ascii=False, indent=2),
                    'content': report
                }
                
                # 保存历史记录
                from modules.utils import save_history
                save_history(history_data)
                
                add_log("info", "=== 测评结果保存成功 ===")
                return True
                
            except Exception as e:
                error_msg = f"保存历史记录失败: {str(e)}"
                add_log("error", error_msg)
                add_log("error", traceback.format_exc())
                st.error(error_msg)
                return False
                
        except Exception as e:
            error_msg = (
                f"\n=== 保存测试结果时发生错误 ===\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}"
            )
            add_log("error", error_msg)
            st.error(f"保存测试结果失败: {str(e)}")
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
                    print(f"处理领导力: {str(e)}")
                
                # 获取MBTI具体建议
                mbti_advice = {
                    'INTJ': "您是战略家型人才，适合从事需要深度思考和规划的工作。建议发展方向：战咨询、项目规划、研发管理。",
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
                    'ISFP': "您是探险家型人才，适合艺术体验性作。建议发展方向：艺术创作、产品设计、体验设计。",
                    'ESFP': "您是表演者型人才，适合互动和表现型工作。建议发展方向：活动策划销售推广、品牌推广。"
                }
                
                # 生成具体的发展建议
                development_suggestions = self.generate_development_suggestions(
                    mbti_type, 
                    big5_traits, 
                    holland_primary, 
                    leadership_scores
                )
                
                # 生成完整的文本结
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
        
        欢迎使用职业测评系统！本系统将从以下几个维度对您行全面的职业倾评：
        
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
        try:
            from modules.utils import add_log
            
            if not st.session_state.test_started:
                # 显示介绍页面
                st.write("""
                ## 领导力测评系统
                
                欢迎使用导力测评系统！本系统将从以下几个维度对您进行全面的领导力潜质评估：
                
                1. 大五人格测评
                2. MBTI性格类型
                3. 霍兰德职业兴趣
                4. 领导力准则匹配度
                
                测评完成后，您将获得：
                - 个性特征分析报告
                - 领导力潜质分析
                - 发展建议
                
                点"开始测评"即可开始您的领导力探索之旅！
                """)
                
                if st.button("开始测评", type="primary"):
                    st.session_state.test_started = True
                    st.rerun()
                    
            elif not st.session_state.test_submitted:
                # 加载题目
                questions, leadership = self.load_data()
                if not questions:
                    st.error("无法加载测评题目，请检查数据文件")
                    return
                    
                # 计算完成进度
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
                        st.session_state.report_content = None
                        st.rerun()
                    
                    st.divider()
                    
                    # 初始化报告内容存储
                    report_content = {
                        'text': [],
                        'figures': {}
                    }
                    
                    # 个性特质分析部分
                    with st.expander("个性特质分析", expanded=True):
                        # 只调用显示方法，不重复显示图表
                        self.display_personality_traits(report)
                        # 保存图表供导出使用
                        report_content['figures']['big5_spider'] = self.create_big5_spider_chart(report['personality_traits']['big5'])
                        # 保存文本内容
                        report_content['text'].extend([
                            "# 六页纸领导力测评报告",
                            "\n## 一、个性特质分析",
                            "\n### 1. 大五人格分析",
                            # ... 其他文本内容 ...
                        ])
                    
                    # 职业建议部分
                    with st.expander("职业建议", expanded=True):
                        self.display_career_suggestions(report)
                        career_text = []
                        # ... 保存职业建议文本 ...
                        report_content['text'].extend(["\n## 二、职业发展建议"] + career_text)
                    
                    # 领导力培养部分
                    with st.expander("领导力培养", expanded=True):
                        # 只调用显示方法，不重复显示图表
                        self.display_leadership_analysis(report)
                        # 保存图表供导出使用
                        report_content['figures']['leadership_rose'] = self.create_leadership_rose_chart(report['leadership_analysis']['sorted_scores'])
                        # ... 保存领导力分析文本 ...
                    
                    # 发展建议部分
                    with st.expander("发展��议", expanded=True):
                        # 先显示内容
                        self.display_development_suggestions(report)
                        # 然后保存内容
                        if 'final_result' in st.session_state:
                            report_content['text'].extend([
                                "\n## 四、综合分析与发展建议",
                                st.session_state.final_result
                            ])
                    
                    # 保存完整报告内容
                    st.session_state.report_content = report_content
                    
                    # 在最下方添加导出按钮
                    st.divider()
                    if st.button("📄 导出完整报告", type="primary", key="export_report"):
                        try:
                            from docx import Document
                            from docx.shared import Inches, Pt, RGBColor
                            from docx.enum.text import WD_ALIGN_PARAGRAPH
                            import tempfile
                            import io
                            
                            # 创建文档
                            doc = Document()
                            
                            # 设置页面格式为不分页
                            section = doc.sections[0]
                            section.start_type = None
                            
                            # 添加标题
                            title = doc.add_heading('六页纸领导力测评报告', 0)
                            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            
                            # 添加时间和用户信息
                            info_paragraph = doc.add_paragraph()
                            info_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            info_paragraph.add_run(f"用户：{st.session_state.user}\n")
                            info_paragraph.add_run(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # 添加分隔线
                            doc.add_paragraph('_' * 80)
                            
                            # 添加文本内容（不添加分页符）
                            for line in st.session_state.report_content['text']:
                                if line.startswith('# '):
                                    doc.add_heading(line[2:], 0)
                                elif line.startswith('## '):
                                    doc.add_heading(line[3:], 1)
                                elif line.startswith('### '):
                                    doc.add_heading(line[4:], 2)
                                else:
                                    doc.add_paragraph(line)
                                
                                # 在每个主要部分后添加隔线而不是分页
                                if line.startswith('## '):
                                    doc.add_paragraph('_' * 80)
                            
                            # 添加图表（在相应位置插入，不添加分页符）
                            for fig_name, fig in st.session_state.report_content['figures'].items():
                                # 保存图表为临时文件
                                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                                    fig.write_image(tmp_file.name)
                                    # 在适当位置添加图片
                                    if fig_name == 'big5_spider':
                                        doc.add_heading('大五人格分析图', level=3)
                                    elif fig_name == 'leadership_rose':
                                        doc.add_heading('领导力准则得分分布图', level=3)
                                    doc.add_picture(tmp_file.name, width=Inches(6))
                            
                            # 保存文档到存
                            doc_io = io.BytesIO()
                            doc.save(doc_io)
                            doc_io.seek(0)
                            
                            # 生成文件名
                            filename = f"六页纸领导力测评-{st.session_state.user}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                            
                            # 直接触发下载
                            st.download_button(
                                label="💾 保存Word文档",
                                data=doc_io,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="save_report"
                            )
                            
                        except Exception as e:
                            st.error(f"生成Word报告失败: {str(e)}")
                            add_log("error", f"生成Word报告失败: {str(e)}\n{traceback.format_exc()}")
            
        except Exception as e:
            st.error(f"加载领导力测评模块失败: {str(e)}")
            add_log("error", f"加载领导力测评模块失败: {str(e)}\n{traceback.format_exc()}")

    def display_personality_traits(self, report):
        """显示个性特质分析"""
        try:
            from modules.utils import add_log
            
            add_log("info", "=== 开始显示个性特质分析 ===")
            add_log("info", f"报告数据: {json.dumps(report, ensure_ascii=False, indent=2)}")
            
            # 大五人格蜘蛛图
            st.subheader("大五人格分析")
            
            # 准备数据
            try:
                big5_data = report['personality_traits']['big5']
                add_log("info", f"大五人格数据: {json.dumps(big5_data, ensure_ascii=False, indent=2)}")
            except Exception as e:
                add_log("error", f"获取大五人格数据失败: {str(e)}")
                raise
            
            # 准备数据
            categories = []
            scores = []
            interpretations = []
            
            trait_names = {
                '开放性': 'Openness - 开放性',
                '尽责性': 'Conscientiousness - 尽责性',
                '外向性': 'Extraversion - 外向性',
                '宜人性': 'Agreeableness - 宜人性',
                '情绪稳定性': 'Neuroticism - 情绪稳定性'
            }
            
            # 归一化分数到1-5范围
            max_score = max(data['score'] for data in big5_data.values())
            min_score = min(data['score'] for data in big5_data.values())
            
            def normalize_score(score):
                if max_score == min_score:
                    return 3
                return 1 + 4 * (score - min_score) / (max_score - min_score)
            
            for trait, data in big5_data.items():
                categories.append(trait_names.get(trait, trait))
                normalized_score = normalize_score(data['score'])
                scores.append(normalized_score)
                interpretations.append(data['interpretation'])
            
            # 添加首个点以闭合图形
            categories.append(categories[0])
            scores.append(scores[0])
            
            # 创建蜘蛛图
            fig = go.Figure()
            
            # 添加参考圈
            for level in [1, 2, 3, 4, 5]:
                fig.add_trace(go.Scatterpolar(
                    r=[level] * 6,
                    theta=categories,
                    mode='lines',
                    line=dict(color='rgba(200,200,200,0.2)', dash='dot'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # 添加数据线
            fig.add_trace(go.Scatterpolar(
                r=scores,
                theta=categories,
                fill='toself',
                line=dict(color='rgb(67, 147, 195)', width=2),
                fillcolor='rgba(67, 147, 195, 0.3)',
                name='得分'
            ))
            
            # 更新布局
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 5],
                        tickmode='array',
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=['低', '较低', '中等', '较高', '高'],
                        tickfont=dict(size=10),
                        angle=45,
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=10),
                        rotation=90,
                        direction="clockwise"
                    )
                ),
                showlegend=False,
                height=500,
                margin=dict(l=80, r=80, t=20, b=20)
            )
            
            # 显示图表
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示特质解读（表格形式）
            st.write("### 特质解读")
            
            try:
                # 按分数排序
                sorted_traits = sorted(
                    big5_data.items(),
                    key=lambda x: x[1]['score'],
                    reverse=True
                )
                add_log("info", f"排序后的特质: {json.dumps(sorted_traits, ensure_ascii=False, indent=2)}")
                
                # 准备表格数据
                table_data = []
                for i, (trait, data) in enumerate(sorted_traits):
                    if i < 2:
                        level = "高"
                    elif i < 4:
                        level = "中"
                    else:
                        level = "低"
                    
                    table_data.append({
                        "特质维度": trait,
                        "得分": f"{data['score']:.1f}",
                        "水平": level,
                        "特质解读": data['interpretation']
                    })
                
                add_log("info", f"表格数据: {json.dumps(table_data, ensure_ascii=False, indent=2)}")
                
                # 创建DataFrame并显示表格
                df = pd.DataFrame(table_data)
                st.dataframe(
                    df,
                    column_config={
                        "特质维度": st.column_config.TextColumn("特质维度", width="medium"),
                        "得分": st.column_config.NumberColumn("得分", format="%.1f"),
                        "水平": st.column_config.TextColumn("水平", width="small"),
                        "特质解读": st.column_config.TextColumn("特质解读", width="large"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
                add_log("info", "表格显示成功")
                
            except Exception as e:
                add_log("error", f"处理特质解读表格失败: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # MBTI类型解释
            try:
                st.subheader("MBTI类型")
                mbti_data = report['personality_traits']['mbti']
                # 从原始数据中获取MBTI分数
                mbti_scores = report.get('scores', {}).get('mbti', {})
                
                # 确保所有必要的键都存在
                required_keys = ['E', 'I', 'S', 'N', 'T', 'F', 'J', 'P']
                for key in required_keys:
                    if key not in mbti_scores:
                        add_log("warning", f"缺少MBTI维度 {key}，使用默认值0.5")
                        mbti_scores[key] = 0.5
                
                # MBTI类型描述
                mbti_descriptions = {
                    'INTJ': "您是战略家型人才，擅长系统思考和战略规划。理性客观，追求完美，具有很强的独立思考能力。",
                    'ENTJ': "您是指挥官型人才，天生的领导者。果断坚定，善于统筹全局，追求效率和成功。",
                    'INTP': "您是逻辑学家型人才，擅长理论分析和系统设计。追求真理，富有创造力，喜欢探索新概念。",
                    'ENTP': "您是辩论家型人才，创新思维者。机智灵活，善于发现机会，乐于挑战传统观念。",
                    'INFJ': "您是提倡者型人才，富有同理心和洞察力。追求意义，善于激励他人，致力于实现理想。",
                    'ENFJ': "您是教导主任型人才，天生的教育者和领导者。关注他人成长，善于团队建设，富有感染力。",
                    'INFP': "您是调停者型人才，理想主义者。重视个人价值，具有创造力，追求真实和谐的人际关系。",
                    'ENFP': "您是竞选者型人才，充满热情的创新者。善于激发潜能，适应力强，富有同理心。",
                    'ISTJ': "您是物流师型人才，可靠的执行者。做事认真负责，注重细节，遵循传统和规则。",
                    'ESTJ': "您是总经理型人才，务实的管理者。组织能力强，重视效率，善于制定和执行计划。",
                    'ISFJ': "您是守卫者型人才，忠诚的服务者。做事细心，责任心强，关注他人需求。",
                    'ESFJ': "您是执政官型人才，热心的合作者。善于维护关系，乐于助人，重视和谐。",
                    'ISTP': "您是鉴赏家型人才，灵活的问题解决者。善于实践，反应快速，喜欢探索和冒险。",
                    'ESTP': "您是企业家型人才，灵活的实干家。善于把握机会，适应力强，喜欢具体的挑战。",
                    'ISFP': "您是探险家型人才，灵活的艺术家。重视体验，善于欣赏美，追求自我表达。",
                    'ESFP': "您是表演者型人才，活力四射的娱乐者。善于交际，适应力强，享受当下。"
                }
                
                add_log("info", f"MBTI分数: {json.dumps(mbti_scores, ensure_ascii=False)}")
                
                # 创建并显示MBTI仪表盘
                mbti_gauge = self.create_mbti_gauge_chart(mbti_scores)
                st.plotly_chart(mbti_gauge, use_container_width=True, key="mbti_gauge_chart")
                
                # 显示MBTI类型描述
                st.write(f"您的类型是：**{mbti_data['type']}**")
                st.write(mbti_descriptions.get(mbti_data['type'], "暂无该类型的详细描述"))
                add_log("info", "MBTI类型显示成功")
                
            except Exception as e:
                add_log("error", f"显示MBTI类型失败: {str(e)}\n{traceback.format_exc()}")
                raise
            
            # 霍兰德代码解释
            try:
                st.subheader("霍兰德职业兴趣")
                holland_data = report['personality_traits']['holland']
                add_log("info", f"霍兰德数据: {json.dumps(holland_data, ensure_ascii=False, indent=2)}")
                
                holland_descriptions = {
                    'R': "现实型(Realistic)：偏好动手操作和解决具体问题，具有机械操作能力，喜欢户外工作。",
                    'I': "研究型(Investigative)：偏好分析和研究，具有科学探索精神，喜欢独立思考。",
                    # ... 其他霍兰德类型描述 ...
                }
                
                st.write("#### 主要类型")
                st.write(holland_descriptions.get(holland_data['primary']['title'], '暂无描述'))
                st.write(holland_data['primary']['description'])
                
                st.write("#### 次要类型")
                st.write(holland_descriptions.get(holland_data['secondary']['title'], '暂无描述'))
                st.write(holland_data['secondary']['description'])
                add_log("info", "霍兰德代码显示成功")
                
            except Exception as e:
                add_log("error", f"显示霍兰德代码失败: {str(e)}\n{traceback.format_exc()}")
                raise
            
            add_log("info", "=== 个性特质分析显示完成 ===")
            
        except Exception as e:
            error_msg = f"显示个性特质分析失败: {str(e)}\n{traceback.format_exc()}"
            add_log("error", error_msg)
            st.error(error_msg)

    def display_career_suggestions(self, report):
        """显示职业建议"""
        st.subheader("推荐职业发展方向")
        
        # 获取所有职业建议
        suggestions = report['career_suggestions']
        
        # 确保至少有两个建议
        while len(suggestions) < 2:
            suggestions.append({
                'title': '通用管理',
                'positions': [
                    {
                        'name': '项目经理',
                        'strengths': ['组织协调能力', '沟通管理能力'],
                        'improvements': '需要加强专业技术深度'
                    }
                ]
            })
        
        # 只显示前两个建议，并标记主副方向
        col1, col2 = st.columns(2)
        
        # 主要发展方向
        with col1:
            st.markdown("### 🎯 主要发展方向")
            st.markdown(f"**{suggestions[0]['title']}**")
            for pos in suggestions[0]['positions']:
                st.markdown("#### " + pos['name'])
                st.markdown("**优势匹配：**")
                for strength in pos['strengths']:
                    st.markdown(f"- {strength}")
                st.markdown("**建议提升：**")
                st.markdown(f"- {pos['improvements']}")
        
        # 次要发展方向
        with col2:
            st.markdown("### 🔄 次要发展方向")
            st.markdown(f"**{suggestions[1]['title']}**")
            for pos in suggestions[1]['positions']:
                st.markdown("#### " + pos['name'])
                st.markdown("**优势匹配：**")
                for strength in pos['strengths']:
                    st.markdown(f"- {strength}")
                st.markdown("**建议提升：**")
                st.markdown(f"- {pos['improvements']}")

    def display_development_suggestions(self, report):
        """显示发展建议"""
        try:
            from modules.utils import add_log, load_config
            from modules.api import APIClient
            import streamlit as st
            
            # 配置文件加载配置
            try:
                config = load_config()
                if not config:
                    st.error("配置文件加载失败")
                    add_log("error", "配置文件加载失败")
                    return
            except Exception as e:
                st.error(f"加载配置文件失败: {str(e)}")
                add_log("error", f"加载配置文件失败: {str(e)}")
                return
            
            # 收集所有已显示的分析结果
            big5_data = report['personality_traits']['big5']
            big5_analysis = "\n".join([
                f"{trait}：得分 {data['score']:.1f}\n{data['interpretation']}"
                for trait, data in big5_data.items()
            ])
            
            mbti_data = report['personality_traits']['mbti']
            holland_data = report['personality_traits']['holland']
            
            leadership_scores = report['leadership_analysis']['sorted_scores']
            top_principles = report['leadership_analysis']['top_analysis']
            bottom_principles = report['leadership_analysis']['bottom_analysis']
            
            leadership_analysis = (
                "优势准则（得分最高的3项）：\n" +
                "\n".join([
                    f"- {analysis['name']} (得分: {analysis['score']:.1f})\n  {analysis['description']}"
                    for analysis in top_principles
                ]) +
                "\n\n需要提升的准则（得分最低的2项）：\n" +
                "\n".join([
                    f"- {analysis['name']} (得分: {analysis['score']:.1f})\n  {analysis['description']}"
                    for analysis in bottom_principles
                ])
            )
            
            career_suggestions = "\n".join([
                f"推荐职业方向：{suggestion['title']}\n" +
                "\n".join([
                    f"- {pos['name']}\n  优势：{', '.join(pos['strengths'])}\n  需要提升：{pos['improvements']}"
                    for pos in suggestion['positions']
                ])
                for suggestion in report['career_suggestions']
            ])
            
            # 准备完整的提示词
            prompt = f"""
作为一位资深的职业发展顾问，请根据以下详细的测评结果，为这位候选人提供一份全面的领导力发展建议。

一、个性特质分析：

1. 大五人格测评结果：
{big5_analysis}

2. MBTI类型：{mbti_data['type']}
{mbti_data['description']}

3. 霍兰德职业趣：
主导类型：{holland_data['primary']['title']}
{holland_data['primary']['description']}
次要类型：{holland_data['secondary']['title']}
{holland_data['secondary']['description']}

二、领导力准则评估：

1. 得分分布（从高到低）：
{json.dumps(leadership_scores, ensure_ascii=False, indent=2)}

2. 详细分析：
{leadership_analysis}

三、职业建议：
{career_suggestions}

基于以上全面的测评结果，请提供一份不超过1000字的综合分析和发展建议，内容应包括：
1. 结合所有测评度，分析此人的核心优势和潜在挑战
2. 基于导力准则评估结果，就如何发挥优势���提升短板给出具体建议
3. 结合个性特征和职业兴趣，为其领导力发展路径提供长期规划建议

要求：
1. 使用连贯的段落叙述，避免分点列举
2. 语言要专业、具体且富有洞察力
3. 建议要切实可行，并与测评结果紧密关联
4. 重点关注领导力发展，但也要兼顾个人成长
5. 建议要具体明确，避免泛泛而谈
"""

            # 调用API获取建议
            api_client = APIClient(config)
            
            # 使用 placeholder 显示生成过程
            with st.empty():
                st.subheader("综合分析与发展建议")
                full_response = ""
                
                # 使用 generate_content_stream 替代 chat_completion
                for chunk in api_client.generate_content_stream(prompt, "claude"):
                    if chunk:
                        full_response += chunk
                        st.write(full_response)
                        
                if not full_response:
                    st.error("生成发展建议时出错")
                    
        except Exception as e:
            st.error(f"生成发展建议失败: {str(e)}")
            add_log("error", f"生成发展建议失败: {str(e)}\n{traceback.format_exc()}")

    def display_leadership_analysis(self, report):
        """显示领导力分析"""
        st.subheader("领导力准则得分")
        
        # 准备数据
        scores_data = report['leadership_analysis']['sorted_scores']
        names = [score[0] for score in scores_data]
        scores = [score[1] for score in scores_data]
        
        # 玫瑰图（添加唯一key）
        fig_rose = go.Figure()
        fig_rose.add_trace(go.Barpolar(
            r=scores,
            theta=names,
            width=0.8,
            marker_color=scores,
            marker_colorscale='Viridis',
            marker_showscale=True,
            marker_colorbar_title="得分",
            hovertemplate="准则: %{theta}<br>得分: %{r:.1f}<extra></extra>"
        ))
        
        fig_rose.update_layout(
            polar=dict(
                radialaxis=dict(
                    range=[50, 100],
                    showticklabels=True,
                    tickmode='array',
                    ticktext=['50', '60', '70', '80', '90', '100'],
                    tickvals=[50, 60, 70, 80, 90, 100],
                    tickfont=dict(size=10),
                    tickangle=45,
                ),
                angularaxis=dict(
                    showticklabels=True,
                    tickfont_size=10,
                    rotation=90,
                    direction="clockwise"
                )
            ),
            title=dict(
                text="领导力准则得分分布",
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            height=700,
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        # 显示图表（添加唯一key）
        st.plotly_chart(fig_rose, use_container_width=True, key="leadership_rose_chart")
        
        # 准备表格数据
        table_data = []
        
        # 添加优势准则（前3项）
        for analysis in report['leadership_analysis']['top_analysis']:
            table_data.append({
                "准则类型": "🌟 优势准则",
                "准则名称": analysis['name'],
                "得分": f"{analysis['score']:.1f}",
                "特点描述": analysis['description']
            })
        
        # 添加需要提升的准则（后2项）
        for analysis in report['leadership_analysis']['bottom_analysis']:
            table_data.append({
                "准则类型": "📈 待提升准则",
                "准则名称": analysis['name'],
                "得分": f"{analysis['score']:.1f}",
                "特点描述": analysis['description']
            })
        
        # 创建并显示表格
        df = pd.DataFrame(table_data)
        st.dataframe(
            df,
            column_config={
                "准则类型": st.column_config.TextColumn("类型", width="small"),
                "准则名称": st.column_config.TextColumn("准则", width="medium"),
                "得分": st.column_config.NumberColumn("得分", format="%.1f", width="small"),
                "特点描述": st.column_config.TextColumn("特点描述", width="large"),
            },
            hide_index=True,
            use_container_width=True
        )

    def validate_answers(self, answers):
        """验证所有答案完整"""
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
                    error_msg = f"第{i}题的排序不完整或复: {ranks}"
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
            print("\n=== 开始加载数文件 ===")
            
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
            st.error(f"加载据文件失败: {str(e)}")
            return None, None

    def display_final_result(self, result_text):
        """显示最终结果"""
        st.markdown("## 领导力测评结果")
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
            'INFP': ["创意表达能力", "价值观设能力", "个性化服务能力"],
            'ENFP': ["人际关系能力", "创新思维能力", "激励感染力"],
            'ISTJ': ["执行力", "细节把控能力", "流程管理能力"],
            'ESTJ': ["组织管理能力", "实施执行能力", "目标达成能力"],
            'ISFJ': ["服务意识", "责任心", "团队协作能力"],
            'ESFJ': ["人际协调能力", "服务意识", "团队合作能力"],
            'ISTP': ["实践操作能力", "问题解决能力", "危机处理能力"],
            'ESTP': ["动力", "资源整合能力", "机会把握力"],
            'ISFP': ["艺术审美能力", "实践能力", "适能力"],
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
                    improvement_areas.append("团队协作和人际关")
                elif trait == 'N':
                    improvement_areas.append("压力管理和情绪调节")
        
        # 基于霍兰德代码的职业发展路径
        career_paths = {
            "研究型": "可以向专业技术专家、研究员或技术主管方向发展，注重专业深度",
            "艺术型": "可以向创意总监、设计主管或艺术总监方向发展，发挥创造力",
            "社会型": "可以向人力资源总监、培训总监或咨询顾问方向发展，善用人际优势",
            "企业型": "可以向项目经理、业务总监或创业者方向发展，发挥领导才能",
            "常规型": "可以向运营总监、质量总监或流程管理专家方向发展，强化系统能力",
            "实践型": "可以向技术总监、工总监产品经理方向发展，突出实践能力"
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
                            "可以从小型项目开，逐步承担更多责任"]
        
        # 整合所有建议
        suggestions = {
            'strengths': f"���的优势在于：\n" + "\n".join([f"- {s}" for s in strengths]),
            'improvements': f"短期内可以重点提升\n" + "\n".join([f"- {i}" for i in improvement_areas]) if improvement_areas else "您的各项能力比较均衡，建议：\n- 继续保持并深化现有优势\n- 在工作中尝试承担更具挑战性的任",
            'career_path': f"建议的职业发展路径：\n{career_path}",
            'leadership': f"领导力发展建议：\n" + "\n".join([f"- {l}" for l in leadership_dev])
        }
        
        return suggestions

    def create_big5_spider_chart(self, big5_data):
        """创建大五人格蜘蛛图"""
        # 准备数据
        categories = []
        scores = []
        
        trait_names = {
            '开放性': 'Openness - 开放性',
            '尽责性': 'Conscientiousness - 尽责性',
            '外向性': 'Extraversion - 外向性',
            '宜人性': 'Agreeableness - 宜人性',
            '情绪稳定性': 'Neuroticism - 情绪稳定性'
        }
        
        # 归一化分数到1-5范围
        max_score = max(data['score'] for data in big5_data.values())
        min_score = min(data['score'] for data in big5_data.values())
        
        def normalize_score(score):
            if max_score == min_score:
                return 3
            return 1 + 4 * (score - min_score) / (max_score - min_score)
        
        for trait, data in big5_data.items():
            categories.append(trait_names.get(trait, trait))
            normalized_score = normalize_score(data['score'])
            scores.append(normalized_score)
        
        # 添加首个点以闭合图形
        categories.append(categories[0])
        scores.append(scores[0])
        
        # 创建蜘蛛图
        fig = go.Figure()
        
        # 添加参考圈
        for level in [1, 2, 3, 4, 5]:
            fig.add_trace(go.Scatterpolar(
                r=[level] * 6,
                theta=categories,
                mode='lines',
                line=dict(color='rgba(200,200,200,0.2)', dash='dot'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # 添加数据线
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=categories,
            fill='toself',
            line=dict(color='rgb(67, 147, 195)', width=2),
            fillcolor='rgba(67, 147, 195, 0.3)',
            name='得分'
        ))
        
        # 更新布局
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    tickmode='array',
                    tickvals=[1, 2, 3, 4, 5],
                    ticktext=['低', '较低', '中等', '较高', '高'],
                    tickfont=dict(size=10),
                    angle=45,
                ),
                angularaxis=dict(
                    tickfont=dict(size=10),
                    rotation=90,
                    direction="clockwise"
                )
            ),
            showlegend=False,
            height=500,
            margin=dict(l=80, r=80, t=20, b=20)
        )
        
        return fig

    def create_leadership_rose_chart(self, scores_data):
        """创建领导力准则玫瑰图"""
        names = [score[0] for score in scores_data]
        scores = [score[1] for score in scores_data]
        
        fig_rose = go.Figure()
        fig_rose.add_trace(go.Barpolar(
            r=scores,
            theta=names,
            width=0.8,
            marker_color=scores,
            marker_colorscale='Viridis',
            marker_showscale=True,
            marker_colorbar_title="得分",
            hovertemplate="准则: %{theta}<br>得分: %{r:.1f}<extra></extra>"
        ))
        
        fig_rose.update_layout(
            polar=dict(
                radialaxis=dict(
                    range=[50, 100],
                    showticklabels=True,
                    tickmode='array',
                    ticktext=['50', '60', '70', '80', '90', '100'],
                    tickvals=[50, 60, 70, 80, 90, 100],
                    tickfont=dict(size=10),
                    tickangle=45,
                ),
                angularaxis=dict(
                    showticklabels=True,
                    tickfont_size=10,
                    rotation=90,
                    direction="clockwise"
                )
            ),
            title=dict(
                text="领导力准则得分分布",
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top'
            ),
            height=700,
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        return fig_rose

    def create_mbti_gauge_chart(self, mbti_scores):
        """创建MBTI仪表盘组合图"""
        # 定义四个维度的配置
        dimensions = [
            {
                'title': '外向-内向',
                'left': 'E (外向)',
                'right': 'I (内向)',
                'score': mbti_scores['E'],
                'color': 'rgb(255, 127, 14)',  # 橙色
                'symbol': '👥'
            },
            {
                'title': '感知-直觉',
                'left': 'S (感知)',
                'right': 'N (直觉)',
                'score': mbti_scores['S'],
                'color': 'rgb(44, 160, 44)',  # 绿色
                'symbol': '👁️'
            },
            {
                'title': '思维-情感',
                'left': 'T (思维)',
                'right': 'F (情感)',
                'score': mbti_scores['T'],
                'color': 'rgb(31, 119, 180)',  # 蓝色
                'symbol': '🧠'
            },
            {
                'title': '判断-知觉',
                'left': 'J (判断)',
                'right': 'P (知觉)',
                'score': mbti_scores['J'],
                'color': 'rgb(214, 39, 40)',  # 红色
                'symbol': '⚖️'
            }
        ]
        
        # 创建子图布局
        fig = go.Figure()
        
        # 为每个维度创建仪表盘
        for i, dim in enumerate(dimensions):
            # 计算布局位置
            row = i // 2
            col = i % 2
            x_pos = 0.25 + col * 0.5
            y_pos = 0.75 - row * 0.5
            
            # 添加仪表盘
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=dim['score'] * 100,  # 转换为百分比
                domain={'x': [x_pos-0.2, x_pos+0.2], 'y': [y_pos-0.2, y_pos+0.2]},
                title={
                    'text': f"{dim['symbol']} {dim['title']}<br>"
                           f"<span style='font-size:0.8em'>{dim['left']} - {dim['right']}</span>",
                    'font': {'size': 16}
                },
                gauge={
                    'axis': {
                        'range': [0, 100],
                        'tickwidth': 1,
                        'tickcolor': dim['color']
                    },
                    'bar': {'color': dim['color']},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': dim['color'],
                    'steps': [
                        {'range': [0, 50], 'color': f"rgba{tuple(int(x) for x in dim['color'].strip('rgb()').split(',')) + (0.2,)}"},
                        {'range': [50, 100], 'color': f"rgba{tuple(int(x) for x in dim['color'].strip('rgb()').split(',')) + (0.4,)}"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': dim['score'] * 100
                    }
                }
            ))
        
        # 更新布局
        fig.update_layout(
            title={
                'text': "MBTI 性格维度分析",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 24}
            },
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=600,
            margin=dict(t=100, b=20),
            showlegend=False,
            annotations=[
                dict(
                    text=f"偏好强度: {score*100:.0f}%",
                    x=0.25 + (i%2)*0.5,
                    y=0.75 - (i//2)*0.5 - 0.25,
                    showarrow=False,
                    font={'size': 12}
                ) for i, score in enumerate([
                    mbti_scores['E'],
                    mbti_scores['S'],
                    mbti_scores['T'],
                    mbti_scores['J']
                ])
            ]
        )
        
        return fig
