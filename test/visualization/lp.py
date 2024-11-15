"""领导力准则可视化模块"""
import plotly.graph_objects as go
from typing import Dict, List, Any, Tuple

class LeadershipVisualizer:
    """领导力准则图表可视化类"""
    
    def __init__(self):
        """初始化领导力准则可视化器"""
        self.colors = {
            'text': 'rgb(240, 240, 240)',      # 浅色文字
            'background': 'rgb(25, 25, 35)',    # 深色背景
            'grid': 'rgba(255, 255, 255, 0.1)', # 网格线
            'polar_bg': 'rgb(240, 240, 245)'    # 圆盘背景色（浅灰白色）
        }
    
    def create_rose_chart(self, scores_data: List[Tuple[str, float]]) -> go.Figure:
        """创建领导力准则玫瑰图
        
        Args:
            scores_data: 准则得分列表，每项为(准则名称, 得分)的元组
            
        Returns:
            plotly图表对象
        """
        # 准备数据
        names = [score[0] for score in scores_data]
        scores = [score[1] for score in scores_data]
        
        # 创建玫瑰图
        fig = go.Figure()
        
        # 添加极坐标条形图
        fig.add_trace(go.Barpolar(
            r=scores,
            theta=names,
            width=0.8,
            marker_color=scores,
            marker_colorscale='Viridis',  # 使用Viridis配色方案
            marker_showscale=True,
            marker_colorbar=dict(
                title="得分",
                titleside="right",
                thickness=15,
                len=0.7,
                tickfont=dict(
                    color=self.colors['text']
                ),
                title_font=dict(
                    color=self.colors['text']
                ),
                bgcolor='rgba(255,255,255,0.1)'  # 给颜色条添加半透明背景
            ),
            hovertemplate="准则: %{theta}<br>得分: %{r:.1f}<extra></extra>"
        ))
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text="领导力准则得分分布",
                y=0.95,
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(
                    size=24,
                    color=self.colors['text'],
                    family="Arial Black"
                )
            ),
            polar=dict(
                radialaxis=dict(
                    range=[50, 100],
                    showticklabels=True,
                    tickmode='array',
                    ticktext=['50', '60', '70', '80', '90', '100'],
                    tickvals=[50, 60, 70, 80, 90, 100],
                    tickfont=dict(
                        size=10,
                        color=self.colors['text']
                    ),
                    tickangle=45,
                    gridcolor=self.colors['grid'],
                    linecolor=self.colors['grid']  # 添加轴线颜色
                ),
                angularaxis=dict(
                    tickfont=dict(
                        size=10,
                        color=self.colors['text']
                    ),
                    rotation=90,
                    direction="clockwise",
                    gridcolor=self.colors['grid'],
                    linecolor=self.colors['grid']  # 添加轴线颜色
                ),
                bgcolor=self.colors['polar_bg']  # 使用稍浅的背景色
            ),
            plot_bgcolor=self.colors['background'],
            paper_bgcolor=self.colors['background'],
            height=700,
            margin=dict(t=100, b=50, l=50, r=50),
            showlegend=False
        )
        
        return fig
    
    def create_principle_table(self, top_analysis: List[Dict[str, Any]], bottom_analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """创建领导力准则分析表格数据
        
        Args:
            top_analysis: 优势准则分析列表
            bottom_analysis: 待提升准则分析列表
            
        Returns:
            表格数据列表
        """
        table_data = []
        
        # 添加优势准则（前3项）
        for analysis in top_analysis:
            table_data.append({
                "准则类型": "🌟 优势准则",
                "准则名称": analysis['name'],
                "得分": f"{analysis['score']:.1f}",
                "特点描述": analysis['description']
            })
        
        # 添加需要提升的准则（后2项）
        for analysis in bottom_analysis:
            table_data.append({
                "准则类型": "📈 待提升准则",
                "准则名称": analysis['name'],
                "得分": f"{analysis['score']:.1f}",
                "特点描述": analysis['description']
            })
            
        return table_data 