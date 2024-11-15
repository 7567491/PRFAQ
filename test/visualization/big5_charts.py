"""大五人格可视化模块"""
import plotly.graph_objects as go
from typing import Dict, Any

class Big5Visualizer:
    """大五人格图表可视化类"""
    
    def __init__(self):
        """初始化大五人格可视化器"""
        self.dimensions = [
            '开放性',
            '尽责性', 
            '外向性',
            '宜人性',
            '情绪稳定性'
        ]
        
        # 定义每个维度的两极特征
        self.dimension_traits = {
            '开放性': {
                'high': {
                    'traits': '创新探索、想象丰富、追求新知',
                    'color': 'rgb(88, 180, 255)'  # 明亮的蓝色
                },
                'low': {
                    'traits': '务实稳重、专注深入、重视经验',
                    'color': 'rgb(255, 123, 0)'  # 明亮的橙色
                }
            },
            '尽责性': {
                'high': {
                    'traits': '有序规划、目标明确、注重效率',
                    'color': 'rgb(0, 210, 150)'  # 翡翠绿
                },
                'low': {
                    'traits': '灵活机动、随机应变、自然随性',
                    'color': 'rgb(255, 182, 0)'  # 金色
                }
            },
            '外向性': {
                'high': {
                    'traits': '活力充沛、善于社交、乐于表达',
                    'color': 'rgb(190, 75, 255)'  # 亮紫色
                },
                'low': {
                    'traits': '独立思考、专注内省、深度思维',
                    'color': 'rgb(255, 105, 180)'  # 粉红色
                }
            },
            '宜人性': {
                'high': {
                    'traits': '善解人意、乐于合作、重视和谐',
                    'color': 'rgb(0, 210, 255)'  # 天蓝色
                },
                'low': {
                    'traits': '独立自主、客观理性、重视效果',
                    'color': 'rgb(255, 85, 85)'  # 珊瑚红
                }
            },
            '情绪稳定性': {
                'high': {
                    'traits': '冷静理性、抗压坚韧、情绪稳定',
                    'color': 'rgb(50, 220, 50)'  # 鲜绿色
                },
                'low': {
                    'traits': '敏锐感知、丰富情感、细腻体察',
                    'color': 'rgb(255, 215, 0)'  # 亮金色
                }
            }
        }
        
        self.colors = {
            'text': 'rgb(240, 240, 240)',  # 更亮的文字颜色
            'line': 'rgb(80, 80, 80)',     # 稍亮的线条
            'background': 'rgb(25, 25, 35)' # 深蓝黑色背景
        }

    def create_dual_bar_chart(self, scores: Dict[str, float]) -> go.Figure:
        """创建双向条形图"""
        # 创建图表
        fig = go.Figure()
        
        # 计算归一化分数（转换为-1到1范围）
        normalized_scores = {
            dim: (score - 5.5) / 4.5  # 将1-10分转换为-1到1
            for dim, score in scores.items()
        }
        
        # 添加中轴线
        fig.add_shape(
            type="line",
            x0=0, x1=0,
            y0=-0.5, y1=4.5,
            line=dict(
                color=self.colors['line'],
                width=2,
                dash="dot"
            )
        )
        
        # 为每个维度添加条形和文字
        for i, dim in enumerate(self.dimensions):
            score = normalized_scores[dim]
            traits = self.dimension_traits[dim]
            
            # 根据得分选择颜色和特征文本
            if score > 0:
                color = traits['high']['color']
                traits_text = traits['high']['traits']
            else:
                color = traits['low']['color']
                traits_text = traits['low']['traits']
            
            # 添加条形
            fig.add_trace(go.Bar(
                x=[score],
                y=[i],
                orientation='h',
                marker=dict(
                    color=color,
                    opacity=0.85
                ),
                width=0.65,
                showlegend=False,
                hoverinfo='none'
            ))
            
            # 添加维度标签（居中）
            fig.add_annotation(
                x=0,
                y=i,
                text=f"<b>{dim}</b>",
                showarrow=False,
                font=dict(
                    size=16,
                    color=self.colors['text'],
                    family="Arial Black"
                ),
                xanchor='center',
                yanchor='middle',
                bgcolor='rgba(25,25,35,0.8)',
                borderpad=4
            )
            
            # 在条形内部添加特征文本
            if abs(score) > 0.3:  # 只有当条形足够长时才在内部显示
                fig.add_annotation(
                    x=score/2,  # 放在条形中间
                    y=i,
                    text=traits_text,
                    showarrow=False,
                    font=dict(
                        size=12,
                        color=self.colors['text'],
                        family="Arial"
                    ),
                    xanchor='center',
                    yanchor='middle'
                )
            
            # 添加得分标签
            fig.add_annotation(
                x=score,  # 放在条形末端
                y=i,
                text=f"{scores[dim]:.1f}",
                showarrow=False,
                font=dict(
                    size=14,
                    color=self.colors['text'],
                    family="Arial"
                ),
                xanchor='left' if score > 0 else 'right',
                yanchor='middle',
                bgcolor=f"rgba{tuple(int(x) for x in color.strip('rgb()').split(',')) + (0.3,)}",
                borderpad=2
            )
        
        # 添加图表标题和说明
        fig.add_annotation(
            text=(
                "<b>大五人格特质分析</b><br>"
                "<span style='font-size:12px'>条形长度和颜色表示特质倾向和强度</span>"
            ),
            x=0.5,
            y=1.1,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(
                size=24,
                color=self.colors['text'],
                family="Arial Black"
            ),
            align="center"
        )
        
        # 更新布局
        fig.update_layout(
            xaxis=dict(
                range=[-1.2, 1.2],
                zeroline=False,
                showgrid=False,
                showticklabels=False,
                showline=False
            ),
            yaxis=dict(
                range=[-0.5, 4.5],
                showgrid=False,
                showticklabels=False,
                showline=False
            ),
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            height=500,
            margin=dict(l=50, r=50, t=100, b=50),
            showlegend=False
        )
        
        return fig 