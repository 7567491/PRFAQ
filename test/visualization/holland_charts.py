"""霍兰德职业兴趣可视化模块"""
import plotly.graph_objects as go
from typing import Dict, List, Any

class HollandVisualizer:
    """霍兰德代码图表可视化类"""
    
    def __init__(self):
        """初始化霍兰德可视化器"""
        self.dimension_names = {
            'R': 'Realistic (实践型)',
            'I': 'Investigative (研究型)',
            'A': 'Artistic (艺术型)',
            'S': 'Social (社会型)',
            'E': 'Enterprising (企业型)',
            'C': 'Conventional (常规型)'
        }
        
        # 定义类型之间的关联度（0-1）
        self.type_relations = {
            ('R', 'I'): 0.8, ('I', 'A'): 0.6, ('A', 'S'): 0.8,
            ('S', 'E'): 0.8, ('E', 'C'): 0.8, ('C', 'R'): 0.6,
            ('R', 'C'): 0.6, ('I', 'R'): 0.8, ('A', 'I'): 0.6,
            ('S', 'A'): 0.8, ('E', 'S'): 0.8, ('C', 'E'): 0.8
        }
        
        # 定义每个类型在平面上的位置（六边形布局）
        self.type_positions = {
            'R': (0, -1),      # 下
            'I': (0.87, -0.5), # 右下
            'A': (0.87, 0.5),  # 右上
            'S': (0, 1),       # 上
            'E': (-0.87, 0.5), # 左上
            'C': (-0.87, -0.5) # 左下
        }
        
        self.colors = {
            'R': 'rgb(99, 110, 250)',   # 明亮的蓝色
            'I': 'rgb(239, 85, 59)',    # 明亮的红色
            'A': 'rgb(0, 204, 150)',    # 明亮的绿色
            'S': 'rgb(171, 99, 250)',   # 明亮的紫色
            'E': 'rgb(255, 161, 90)',   # 明亮的橙色
            'C': 'rgb(0, 182, 235)'     # 明亮的青色
        }
        
        # 预定义的职业类型及其霍兰德代码
        self.career_codes = {
            '软件工程师': {'primary': 'I', 'secondary': 'R', 'tertiary': 'C'},
            '数据分析师': {'primary': 'I', 'secondary': 'C', 'tertiary': 'E'},
            '产品经理': {'primary': 'E', 'secondary': 'S', 'tertiary': 'I'},
            '用户体验设计师': {'primary': 'A', 'secondary': 'I', 'tertiary': 'S'},
            '人力资源经理': {'primary': 'S', 'secondary': 'E', 'tertiary': 'C'},
            '市场营销经理': {'primary': 'E', 'secondary': 'S', 'tertiary': 'A'},
            '财务分析师': {'primary': 'C', 'secondary': 'I', 'tertiary': 'E'},
            '项目经理': {'primary': 'E', 'secondary': 'C', 'tertiary': 'S'},
            '研究员': {'primary': 'I', 'secondary': 'R', 'tertiary': 'A'},
            '艺术总监': {'primary': 'A', 'secondary': 'E', 'tertiary': 'S'},
            '技术支持': {'primary': 'R', 'secondary': 'S', 'tertiary': 'C'},
            '培训讲师': {'primary': 'S', 'secondary': 'A', 'tertiary': 'E'},
            '运维工程师': {'primary': 'R', 'secondary': 'C', 'tertiary': 'I'},
            '创业者': {'primary': 'E', 'secondary': 'I', 'tertiary': 'S'},
            '质量工程师': {'primary': 'C', 'secondary': 'R', 'tertiary': 'I'}
        }

    def create_career_map(self, holland_scores: Dict[str, float]) -> go.Figure:
        """创建职业兴趣地图"""
        fig = go.Figure()
        
        # 添加连接线
        for (type1, type2), relation in self.type_relations.items():
            x1, y1 = self.type_positions[type1]
            x2, y2 = self.type_positions[type2]
            
            # 计算线条粗细（基于两个类型的得分和关联度）
            score1 = holland_scores[type1]
            score2 = holland_scores[type2]
            line_width = (((score1 + score2) / 20) * relation) * 6  # 增加线条粗细
            
            # 添加连接线
            fig.add_trace(go.Scatter(
                x=[x1, x2],
                y=[y1, y2],
                mode='lines',
                line=dict(
                    width=line_width,
                    color='rgba(200,200,200,0.25)'  # 降低线条不透明度
                ),
                hoverinfo='skip'
            ))
        
        # 添加圆点
        for type_code, pos in self.type_positions.items():
            score = holland_scores[type_code]
            
            # 计算圆点大小（基于得分）
            marker_size = score * 12  # 增加圆点基础大小
            
            # 添加发光效果的大圆
            fig.add_trace(go.Scatter(
                x=[pos[0]],
                y=[pos[1]],
                mode='markers',
                marker=dict(
                    size=marker_size * 1.5,  # 外圈比实心圆大
                    color=self.colors[type_code],
                    opacity=0.2,  # 半透明
                    line=dict(width=0)
                ),
                hoverinfo='skip'
            ))
            
            # 添加实心圆和文字
            fig.add_trace(go.Scatter(
                x=[pos[0]],
                y=[pos[1]],
                mode='markers+text',
                marker=dict(
                    size=marker_size,
                    color=self.colors[type_code],
                    opacity=0.9,
                    line=dict(
                        color='white',
                        width=2
                    ),
                    symbol='circle'
                ),
                text=f"{self.dimension_names[type_code]}<br>{score:.1f}",
                textposition="middle center",
                textfont=dict(
                    color='white',
                    size=14,
                    family="Arial Black"
                ),
                hovertemplate=(
                    f"<b>{self.dimension_names[type_code]}</b><br>"
                    f"得分: {score:.1f}<br>"
                    "<extra></extra>"
                )
            ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=(
                    "<b>霍兰德职业兴趣地图</b><br>"
                    "<span style='font-size:12px'>圆的大小表示各类型得分，连线粗细表示类型间的关联程度</span>"
                ),
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(
                    size=24,
                    color='white',
                    family="Arial Black"
                )
            ),
            showlegend=False,
            xaxis=dict(
                range=[-1.8, 1.8],  # 扩大显示范围
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                range=[-1.8, 1.8],  # 扩大显示范围
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            plot_bgcolor='rgb(25, 25, 35)',  # 深色背景
            paper_bgcolor='rgb(25, 25, 35)',  # 深色背景
            height=800,  # 增加图表高度
            margin=dict(l=50, r=50, t=100, b=50),
            shapes=[  # 添加六边形轮廓
                dict(
                    type="path",
                    path=f"M 0 -1 L 0.87 -0.5 L 0.87 0.5 L 0 1 L -0.87 0.5 L -0.87 -0.5 Z",
                    line=dict(
                        color='rgba(200,200,200,0.2)',
                        width=1
                    ),
                    fillcolor='rgba(0,0,0,0)'
                )
            ]
        )
        
        return fig

    def create_match_table(self, holland_scores: Dict[str, float], top_careers: int = 8) -> List[Dict[str, Any]]:
        """创建职业匹配度表格数据"""
        # 计算每个职业的匹配度
        career_matches = []
        for career, codes in self.career_codes.items():
            # 计算匹配分数
            match_score = (
                holland_scores[codes['primary']] * 0.5 +
                holland_scores[codes['secondary']] * 0.3 +
                holland_scores[codes['tertiary']] * 0.2
            )
            
            career_matches.append({
                '职业名称': career,
                '霍兰德代码': f"{codes['primary']}{codes['secondary']}{codes['tertiary']}",
                '匹配度': f"{match_score:.1f}",
                '主要特征': f"{self.dimension_names[codes['primary']]}",
                '次要特征': f"{self.dimension_names[codes['secondary']]}"
            })
        
        # 按匹配度排序并返回前N个
        return sorted(career_matches, key=lambda x: float(x['匹配度']), reverse=True)[:top_careers] 