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
            
            # 生成最终显示的文本结果
            final_text = (
                f"# 职业测评结果报告\n\n"
                f"## 个性类型\n"
                f"MBTI类型：{results.get('mbti_type', 'N/A')}\n"
                f"主要职业倾向：{report['personality_traits']['holland']['primary']['title']}\n\n"
                f"## 人格特征分析\n" + 
                "\n".join([f"- {k}: {v['interpretation']}" 
                          for k, v in report['personality_traits']['big5'].items()]) +
                f"\n\n## 推荐职业方向\n" +
                "\n".join([f"- {s['title']}\n  {s['positions'][0]['name']}" 
                          for s in report['career_suggestions']]) +
                f"\n\n## 发展建议\n"
                f"### 短期发展重点\n{report['development_suggestions']['short_term']['improvements']}\n\n"
                f"### 长期发展方向\n{report['development_suggestions']['long_term']['career_path']}"
            )
            
            try:
                # 计算字符数
                input_chars = len("职业测评")
                output_chars = len(final_text)
                
                # 添加字符使用记录
                if not add_letters_record(
                    input_letters=input_chars,
                    output_letters=output_chars,
                    api_name="career_test",
                    operation="职业测评"
                ):
                    print("添加字符使用记录失败")
                    return False
                
                # 保存历史记录
                from modules.utils import save_history
                save_history(
                    st.session_state.user,
                    'career_test',
                    final_text  # 直接保存最终文本结果
                )
                
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
            report = generate_report(st.session_state.current_results)
            
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
        
        点击"开始测评"即可开始您的职业探索旅！
        """)

    def render(self):
        """渲染主界面"""
        if not st.session_state.test_started:
            # 显示介绍页面
            st.write("""
            ## 职业测评系统
            
            欢使用职业测评系统！本系统将从以下几个维度对您进行全面的职业倾向评估：
            
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
            st.write(f"已完成: {completed_questions}/{total_questions} 题")
            
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
