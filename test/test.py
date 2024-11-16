"""领导力测评主模块"""
import streamlit as st
from pathlib import Path
import json
import traceback
from modules.logger import add_log

from test.core.test_manager import TestManager
from test.core.question_handler import QuestionHandler
from test.visualization.mbti_charts import MBTIVisualizer
from test.visualization.big5_charts import Big5Visualizer
from test.visualization.holland_charts import HollandVisualizer
from test.visualization.lp import LeadershipVisualizer

def check_dependencies():
    """检查必要的依赖是否已安装"""
    try:
        import docx
        return True
    except ImportError:
        st.error("""
        缺少必要的依赖包：python-docx
        
        请执行以下命令安装：
        ```
        pip install python-docx==0.8.11
        ```
        
        或联系管理员安装所需依赖。
        """)
        add_log("error", "缺少必要的依赖包：python-docx")
        return False

class CareerTest:
    """领导力测评类"""
    
    def __init__(self):
        """初始化测评系统"""
        if not check_dependencies():
            return
            
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
            # 检查依赖
            if not check_dependencies():
                return False
                
            # 检查必要的数据文件
            data_files = [
                "personality_questions.json",
                "leadership_principles.json",
                "mbti_descriptions.json",
                "career_suggestions.json"
            ]
            
            for file in data_files:
                file_path = Path("test/data") / file
                if not file_path.exists():
                    st.error(f"缺少必要的数据文件：{file}")
                    add_log("error", f"缺少必要的数据文件：{file}")
                    return False
            
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
            error_msg = f"领导力测评渲染失败: {str(e)}\n{traceback.format_exc()}"
            st.error(error_msg)
            add_log("error", error_msg)
            return False
