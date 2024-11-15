"""领导力测评主模块"""
import streamlit as st
from modules.utils import add_log

from test.core.test_manager import TestManager
from test.core.question_handler import QuestionHandler
from test.visualization.mbti_charts import MBTIVisualizer
from test.visualization.big5_charts import Big5Visualizer
from test.visualization.holland_charts import HollandVisualizer
from test.visualization.lp import LeadershipVisualizer

class CareerTest:
    """领导力测评类"""
    
    def __init__(self):
        """初始化测评系统"""
        # 初始化各个组件
        self.test_manager = TestManager()
        self.question_handler = QuestionHandler()
        self.mbti_viz = MBTIVisualizer()
        self.big5_viz = Big5Visualizer()
        self.holland_viz = HollandVisualizer()
        self.lp_viz = LeadershipVisualizer()

    def render(self):
        """渲染主界面"""
        try:
            # 委托给TestManager处理测试流程
            self.test_manager.render(
                question_handler=self.question_handler,
                visualizers={
                    'mbti': self.mbti_viz,
                    'big5': self.big5_viz,
                    'holland': self.holland_viz,
                    'lp': self.lp_viz
                }
            )
                
        except Exception as e:
            st.error(f"加载领导力测评模块失败: {str(e)}")
            add_log("error", f"加载领导力测评模块失败: {str(e)}")
