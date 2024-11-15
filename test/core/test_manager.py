"""测试管理模块"""
import streamlit as st
from pathlib import Path
import json
from typing import Dict, Any, Optional
from datetime import datetime

from test.utils.test_processor import process_test_results
from test.utils.result_generator import ReportDisplayer, generate_report
from modules.utils import add_log

class TestManager:
    """测试管理类"""
    
    def __init__(self):
        """初始化测试管理器"""
        # 初始化session状态
        if 'test_started' not in st.session_state:
            st.session_state.test_started = False
        if 'test_submitted' not in st.session_state:
            st.session_state.test_submitted = False
        if 'current_answers' not in st.session_state:
            st.session_state.current_answers = {}
        if 'current_results' not in st.session_state:
            st.session_state.current_results = None
        if 'report_content' not in st.session_state:
            st.session_state.report_content = None

    def load_data(self) -> tuple:
        """加载测试数据"""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            
            # 加载题目数据
            with open(data_dir / "personality_questions.json", 'r', encoding='utf-8') as f:
                questions = json.load(f)['questions']
                
            # 加载领导力准则数据
            with open(data_dir / "leadership_principles.json", 'r', encoding='utf-8') as f:
                leadership = json.load(f)
                
            return questions, leadership
            
        except Exception as e:
            add_log("error", f"加载测试数据失败: {str(e)}")
            return [], {}

    def process_results(self) -> Optional[Dict[str, Any]]:
        """处理测试结果"""
        try:
            # 处理答案
            results = process_test_results(st.session_state.current_answers)
            if not results:
                add_log("error", "处理测试结果失败")
                return None
            
            # 生成报告
            report = generate_report(results)
            if not report:
                add_log("error", "生成报告失败")
                return None
                
            return report
            
        except Exception as e:
            add_log("error", f"处理测试结果时出错: {str(e)}")
            return None

    def reset_test(self):
        """重置测试状态"""
        st.session_state.test_started = False
        st.session_state.test_submitted = False
        st.session_state.current_answers = {}
        st.session_state.current_results = None
        st.session_state.report_content = None

    def render(self, question_handler, visualizers):
        """渲染测试界面
        
        Args:
            question_handler: 问题处理器
            visualizers: 可视化器字典
        """
        try:
            if not st.session_state.test_started:
                self.display_intro()
                
                if st.button("开始测评", type="primary"):
                    st.session_state.test_started = True
                    st.rerun()
                    
            elif not st.session_state.test_submitted:
                self.display_questions(question_handler)
            
            else:
                self.display_results(visualizers)
                
        except Exception as e:
            st.error(f"加载领导力测评模块失败: {str(e)}")
            add_log("error", f"加载领导力测评模块失败: {str(e)}")

    def display_intro(self):
        """显示测评介绍"""
        st.write("""
        ## 领导力测评系统
        
        欢迎使用领导力测评系统！本系统将从以下几个维度对您进行全面的领导力潜质评估：
        
        1. 大五人格测评
        2. MBTI性格类型
        3. 霍兰德职业兴趣
        4. 领导力准则匹配度
        
        测评完成后，您将获得：
        - 个性特征分析报告
        - 领导力潜质分析
        - 发展建议
        
        点击"开始测评"即可开始您的领导力探索之旅！
        """)

    def display_questions(self, question_handler):
        """显示测评题目"""
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
        
        # 添加顶部提交按钮
        if completed_questions == total_questions:  # 只有在所有题目都完成时才显示顶部提交按钮
            if st.button("提交测评", type="primary", key="submit_top"):
                if question_handler.validate_answers(st.session_state.current_answers):
                    report = self.process_results()
                    if report:
                        st.session_state.current_results = report
                        st.session_state.test_submitted = True
                        st.success('测评完成！')
                        st.rerun()
                    else:
                        st.error("处理测评结果失败")
                else:
                    st.error("请确保所有题目都已完成作答")
        
        # 第一部分：情境选择题（1-9题）
        st.header("第一部分：情境选择题")
        for i in range(9):
            q = questions[i]
            st.session_state.current_answers[i+1] = question_handler.display_situation_question(
                q, i+1, st.session_state.current_answers
            )
        
        # 第二部分：行为频率量表题（10-17题）
        st.header("第二部分：行为频率量表题")
        for i in range(9, 17):
            q = questions[i]
            st.session_state.current_answers[i+1] = question_handler.display_scale_question(
                q, i+1, st.session_state.current_answers
            )
        
        # 第三部分：工作偏好排序题（18-20题）
        st.header("第三部分：工作偏好排序题")
        for i in range(17, 20):
            q = questions[i]
            rank_answers = question_handler.display_rank_question(
                q, i+1, st.session_state.current_answers
            )
            st.session_state.current_answers.update(rank_answers)
        
        # 底部提交按钮
        st.divider()
        if st.button("提交测评", type="primary", key="submit_bottom"):
            if question_handler.validate_answers(st.session_state.current_answers):
                report = self.process_results()
                if report:
                    st.session_state.current_results = report
                    st.session_state.test_submitted = True
                    st.success('测评完成！')
                    st.rerun()
                else:
                    st.error("处理测评结果失败")
            else:
                st.error("请确保所有题目都已完成作答")

    def display_results(self, visualizers):
        """显示测评结果"""
        if st.session_state.current_results:
            report = self.process_results()
            
            # 创建报告显示器
            report_displayer = ReportDisplayer(visualizers)
            
            # 添加重新测评按钮
            if st.button("重新测评", type="primary"):
                self.reset_test()
                st.rerun()
            
            st.divider()
            
            # 显示各部分结果
            with st.expander("个性特质分析", expanded=True):
                report_displayer.display_personality_traits(report)
            
            with st.expander("职业建议", expanded=True):
                report_displayer.display_career_suggestions(report)
            
            with st.expander("领导力培养", expanded=True):
                report_displayer.display_leadership_analysis(report)
            
            with st.expander("发展建议", expanded=True):
                report_displayer.display_development_suggestions(report)
            
            # 在最下方添加导出按钮
            st.divider()
            if st.button("📄 导出完整报告", type="primary"):
                report_displayer.export_report(report)
        else:
            st.info("请完成测评后查看结果")