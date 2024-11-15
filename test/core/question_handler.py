"""问题处理模块"""
import streamlit as st
from typing import Dict, Any, List, Optional

class QuestionHandler:
    """问题处理类"""
    
    def display_situation_question(self, question: Dict[str, Any], number: int, current_answers: Dict[int, Any]) -> Optional[str]:
        """显示情境选择题
        
        Args:
            question: 问题数据
            number: 题目编号
            current_answers: 当前答案
            
        Returns:
            选择的答案
        """
        st.write(f"**{number}. {question['question']}**")
        
        # 获取当前答案或使用默认选项'A'
        current_answer = current_answers.get(number, 'A')
        
        # 创建选项列表
        options = []
        for key, option in question['options'].items():
            options.append({
                'key': key,
                'text': option['text']
            })
        
        # 显示选项
        answer = st.radio(
            "请选择最符合您的选项：",
            options,
            format_func=lambda x: x['text'],
            key=f"situation_{number}",
            index=[i for i, opt in enumerate(options) if opt['key'] == current_answer][0]  # 使用当前答案或默认值的索引
        )
        
        return answer['key'] if answer else 'A'  # 如果没有选择，返回默认值'A'

    def display_scale_question(self, question: Dict[str, Any], number: int, current_answers: Dict[int, Any]) -> Optional[int]:
        """显示量表题
        
        Args:
            question: 问题数据
            number: 题目编号
            current_answers: 当前答案
            
        Returns:
            选择的分数
        """
        st.write(f"**{number}. {question['question']}**")
        
        # 获取当前答案
        current_answer = current_answers.get(number)
        
        # 显示量表选项
        scale_labels = {
            1: "从不",
            2: "很少",
            3: "有时",
            4: "经常",
            5: "总是"
        }
        
        answer = st.select_slider(
            "请选择符合程度：",
            options=list(scale_labels.keys()),
            format_func=lambda x: scale_labels[x],
            value=current_answer if current_answer else 3,
            key=f"scale_{number}"
        )
        
        return answer

    def display_rank_question(self, question: Dict[str, Any], number: int, current_answers: Dict[str, Any]) -> Dict[str, int]:
        """显示排序题
        
        Args:
            question: 问题数据
            number: 题目编号
            current_answers: 当前答案
            
        Returns:
            排序结果
        """
        st.write(f"**{number}. {question['question']}**")
        
        # 创建选项列表
        options = []
        for key, option in question['options'].items():
            options.append({
                'key': key,
                'text': option['text']
            })
        
        # 显示排序说明
        st.write("请为以下选项排序（1表示最符合，4表示最不符合）：")
        
        # 创建4列显示选项
        cols = st.columns(4)
        ranks = {}
        
        for i, option in enumerate(options):
            with cols[i]:
                # 获取当前排序
                current_rank = current_answers.get(f"{number}_{option['key']}", i+1)
                
                # 显示排序输入
                rank = st.number_input(
                    option['text'],
                    min_value=1,
                    max_value=4,
                    value=int(current_rank),
                    key=f"rank_{number}_{option['key']}"
                )
                ranks[f"{number}_{option['key']}"] = rank
        
        # 验证排序是否有效（每个数字只能使用一次）
        used_ranks = list(ranks.values())
        if len(set(used_ranks)) != 4:
            st.warning("请确保每个选项的排序不重复（1-4各使用一次）")
        
        return ranks

    def validate_answers(self, answers: Dict[str, Any]) -> bool:
        """验证答案是否完整
        
        Args:
            answers: 答案数据
            
        Returns:
            是否完整
        """
        try:
            # 检查情境选择题（1-9题）
            for i in range(1, 10):
                if i not in answers or not answers[i]:
                    return False
            
            # 检查量表题（10-17题）
            for i in range(10, 18):
                if i not in answers or not answers[i]:
                    return False
            
            # 检查排序题（18-20题）
            for i in range(18, 21):
                for opt in ['A', 'B', 'C', 'D']:
                    key = f"{i}_{opt}"
                    if key not in answers or not answers[key]:
                        return False
                    
                # 验证排序是否有效
                ranks = [answers[f"{i}_{opt}"] for opt in ['A', 'B', 'C', 'D']]
                if sorted(ranks) != [1, 2, 3, 4]:
                    return False
            
            return True
            
        except Exception as e:
            print(f"验证答案时出错: {str(e)}")
            return False 