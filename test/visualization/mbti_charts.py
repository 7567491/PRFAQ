"""MBTI可视化模块"""
import plotly.graph_objects as go
from typing import Dict, Any

class MBTIVisualizer:
    """MBTI图表可视化类"""
    
    def __init__(self):
        """初始化MBTI可视化器"""
        self.dimensions = [
            {
                'title': '外向-内向',
                'left': 'E (外向)',
                'right': 'I (内向)',
                'color': 'rgb(255, 127, 14)',  # 橙色
                'symbol': '👥'
            },
            {
                'title': '感知-直觉',
                'left': 'S (感知)',
                'right': 'N (直觉)', 
                'color': 'rgb(44, 160, 44)',  # 绿色
                'symbol': '👁️'
            },
            {
                'title': '思维-情感',
                'left': 'T (思维)',
                'right': 'F (情感)',
                'color': 'rgb(31, 119, 180)',  # 蓝色
                'symbol': '🧠'
            },
            {
                'title': '判断-知觉',
                'left': 'J (判断)',
                'right': 'P (知觉)',
                'color': 'rgb(214, 39, 40)',  # 红色
                'symbol': '⚖️'
            }
        ]

    def create_gauge_chart(self, mbti_scores: Dict[str, float], mbti_metadata: Dict[str, Any]) -> go.Figure:
        """创建MBTI仪表盘组合图"""
        # 创建子图布局
        fig = go.Figure()
        
        # 为每个维度创建仪表盘
        for i, dim in enumerate(self.dimensions):
            # 获取该维度的分数和强度
            pair_key = f"{dim['left'][0]}-{dim['right'][0]}"  # 例如: 'E-I'
            strength = mbti_metadata['preference_strengths'][pair_key]
            
            # 计算显示的得分
            left_letter = dim['left'][0]
            right_letter = dim['right'][0]
            
            if mbti_scores[left_letter] > mbti_scores[right_letter]:
                display_score = 50 + (strength * 50 / 20)
            else:
                display_score = 50 - (strength * 50 / 20)
            
            # 计算布局位置（增加垂直间距）
            row = i // 2
            col = i % 2
            x_pos = 0.25 + col * 0.5
            y_pos = 0.85 - row * 0.4  # 增加行间距
            
            # 添加仪表盘
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=display_score,
                domain={'x': [x_pos-0.2, x_pos+0.2], 'y': [y_pos-0.15, y_pos+0.15]},  # 调整仪表盘大小
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
                        'value': display_score
                    }
                }
            ))
            
            # 添加偏好强度标注（调整位置）
            fig.add_annotation(
                text=f"偏好强度: {strength:.1f}",
                x=x_pos,
                y=y_pos - 0.18,  # 调整标注位置
                showarrow=False,
                font={'size': 12}
            )
        
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
            height=700,  # 增加整体高度
            margin=dict(t=100, b=50, l=50, r=50),  # 调整边距
            showlegend=False
        )
        
        return fig 