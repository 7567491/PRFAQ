"""报告生成和显示模块"""
import json
from pathlib import Path
from datetime import datetime
import traceback
import numpy as np
import streamlit as st
import pandas as pd
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import tempfile
import io
from modules.utils import add_log, load_config
from modules.api import APIClient
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def load_data():
    """加载所有必要的数据文件"""
    from modules.utils import add_log
    data_dir = Path(__file__).parent.parent / "data"
    
    try:
        add_log("info", f"开始加载数据文件，数据目录: {data_dir}")
        
        files_to_load = {
            "leadership": "leadership_principles.json",
            "careers": "career_suggestions.json",
            "mbti": "mbti_descriptions.json"
        }
        
        loaded_data = {}
        for key, filename in files_to_load.items():
            file_path = data_dir / filename
            if not file_path.exists():
                add_log("error", f"文件不存在: {file_path}")
                return {}, {}, {}
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    loaded_data[key] = json.load(f)
                add_log("info", f"成功加载 {filename}")
            except json.JSONDecodeError as e:
                add_log("error", f"JSON解析错误 {filename}: {str(e)}")
                return {}, {}, {}
            except Exception as e:
                add_log("error", f"加载 {filename} 失败: {str(e)}")
                return {}, {}, {}
        
        add_log("info", "所有数据文件加载成功")
        return loaded_data["leadership"], loaded_data["careers"], loaded_data["mbti"]
        
    except Exception as e:
        add_log("error", f"加载数据文件失败: {str(e)}\n{traceback.format_exc()}")
        return {}, {}, {}

def analyze_big5(scores):
    """分析大五人格结果"""
    # 维度映射表（使用中文键名）
    trait_names = {
        '开放性': '开放性',
        '尽责性': '尽责性',
        '外向性': '外向性',
        '宜人性': '宜人性',
        '情绪稳定性': '情绪稳定性'
    }
    
    interpretations = {
        '开放性': {
            'high': '富有创造力和想象力，善于接受新观念，勇于尝试新事物。',
            'low': '倾向于传统和实际的方法，重视稳定性。'
        },
        '尽责性': {
            'high': '做事有条理，负责任，值得信赖。工作认真细致，有很强的计划性。',
            'low': '比较随性，灵活，不拘泥于计划。更注重当下的体验。'
        },
        '外向性': {
            'high': '善于社交，充满活力，喜欢与人互动。在团队中往往能发挥积极影响力。',
            'low': '倾向于独处，深思熟虑，注重内在体验。善于独立工作。'
        },
        '宜人性': {
            'high': '富有同理心，善解人意，乐于助人。在团队合作中能很好地维护关系。',
            'low': '独立自主，直言不讳，注重实事求是。在决策时更看重客观事实。'
        },
        '情绪稳定性': {
            'high': '情绪稳定，能很好地控制压力和焦虑。在面对挑战时保持冷静。',
            'low': '情感丰富，对环境变化比较敏感。对周围的细微变化有敏锐感知。'
        }
    }
    
    analysis = {}
    for trait, score in scores.items():
        # 确保分数是数值类型
        if isinstance(score, (int, float)):
            score_val = float(score)
        else:
            score_val = float(score.get('score', 0) if isinstance(score, dict) else 0)
        
        # 判断高低倾向
        interpretation = interpretations[trait]['high'] if score_val > 5 else interpretations[trait]['low']
        
        # 保存分析结果
        analysis[trait] = {
            'score': score_val,
            'interpretation': interpretation
        }
    
    return analysis

def calculate_leadership_scores(results, leadership_principles):
    """根据MBTI、Big5和Holland代码计算14条领导力准则的得分"""
    try:
        from modules.utils import add_log
        
        # 获取用户的测评结果
        mbti_type = results.get('mbti_type', '')
        big5_scores = results.get('scores', {}).get('big5', {})
        holland_scores = results.get('scores', {}).get('holland', {})
        
        # 获取主导和次要Holland类型
        dominant_holland = results.get('dominant_holland', [])
        if isinstance(dominant_holland, list) and len(dominant_holland) > 0:
            holland_primary = dominant_holland[0][0] if isinstance(dominant_holland[0], list) else ''
            holland_secondary = dominant_holland[1][0] if len(dominant_holland) > 1 and isinstance(dominant_holland[1], list) else ''
        else:
            holland_primary = ''
            holland_secondary = ''
        
        add_log("info", f"开始计算领导力得分，MBTI={mbti_type}, Big5={big5_scores}, Holland={holland_primary}/{holland_secondary}")
        
        # 收集所有初始得分
        initial_scores = []
        principle_names = []
        
        # 首先计算原始得分
        for principle in leadership_principles['principles']:
            score = 0
            matches = 0
            related_dims = principle.get('related_dimensions', {})
            
            # MBTI匹配度计算 (0-1范围)
            if 'mbti' in related_dims:
                mbti_matches = sum(1 for letter in related_dims['mbti'] if letter in mbti_type)
                score += (mbti_matches / len(related_dims['mbti'])) * 0.4
                matches += 1
            
            # Big5匹配度计算 (0-1范围)
            if 'big5' in related_dims:
                big5_total = 0
                big5_count = 0
                for trait in related_dims['big5']:
                    if trait in big5_scores:
                        trait_score = float(big5_scores[trait])
                        normalized_score = min(max(trait_score / 10.0, 0), 1)
                        big5_total += normalized_score
                        big5_count += 1
                if big5_count > 0:
                    score += (big5_total / big5_count) * 0.35
                    matches += 1
            
            # Holland匹配度计算 (0-1范围)
            if 'holland' in related_dims:
                holland_matches = 0
                holland_dims = related_dims['holland']
                for dim in holland_dims:
                    if dim in holland_scores:
                        holland_score = float(holland_scores[dim])
                        normalized_score = min(max(holland_score / 10.0, 0), 1)
                        holland_matches += normalized_score
                score += (holland_matches / len(holland_dims)) * 0.25
                matches += 1
            
            # 计算初始得分
            if matches > 0:
                initial_score = score / matches
            else:
                initial_score = 0.5  # 默认中间值
                
            initial_scores.append(initial_score)
            principle_names.append(principle['name'])
        
        # 转换为numpy数组进行标准化
        scores_array = np.array(initial_scores)
        
        # 计算z-scores
        z_scores = (scores_array - np.mean(scores_array)) / np.std(scores_array)
        
        # 将z-scores转换到50-100范围，使用sigmoid函数
        def sigmoid_transform(z, min_score=50, max_score=100):
            sigmoid = 1 / (1 + np.exp(-z))  # sigmoid函数将值压缩到0-1范围
            return min_score + (max_score - min_score) * sigmoid
        
        final_scores = sigmoid_transform(z_scores)
        
        # 创建得分字典并排序
        principle_scores = {
            name: round(score, 1) 
            for name, score in zip(principle_names, final_scores)
        }
        
        # 按得分排序
        sorted_scores = sorted(
            [(name, score) for name, score in principle_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # 生成析结果
        analysis_results = []
        for principle_name, score in sorted_scores:
            principle_info = next(
                (p for p in leadership_principles['principles'] if p['name'] == principle_name),
                {}
            )
            analysis_results.append({
                'name': principle_name,
                'score': score,
                'description': principle_info.get('description', ''),
                'strength_analysis': (
                    f"您在{principle_name}方面表现突出，这与您的"
                    f"{principle_info.get('related_dimensions', {}).get('mbti', [])}型人格特征、"
                    f"较高的{', '.join(principle_info.get('related_dimensions', {}).get('big5', []))}得分、"
                    f"以及{', '.join(principle_info.get('related_dimensions', {}).get('holland', []))}的职业兴趣相匹配。"
                ) if score >= 85 else ''
            })
        
        add_log("info", "领导力准则得分计算完成")
        return sorted_scores, analysis_results
        
    except Exception as e:
        error_msg = f"计算领导力得分时出错: {str(e)}\n{traceback.format_exc()}"
        add_log("error", error_msg)
        raise

def generate_report(results):
    """生成完整的测评报告"""
    try:
        from modules.utils import add_log
        add_log("info", "=== 开始生成报告 ===")
        add_log("info", f"输入数据: {json.dumps(results, ensure_ascii=False, indent=2)}")
        
        # 加载必要的数据
        leadership, careers, mbti_data = load_data()
        if not leadership or not careers or not mbti_data:
            raise ValueError("数据文件加载失败")
            
        add_log("info", "数据文件加载成功")
        
        # 分析各维度特征
        try:
            add_log("info", "开始分析个性特征")
            add_log("info", f"Big5分数: {json.dumps(results['scores']['big5'], ensure_ascii=False)}")
            add_log("info", f"MBTI类型: {results['mbti_type']}")
            add_log("info", f"Holland数据: {json.dumps(results.get('dominant_holland', []), ensure_ascii=False)}")
            
            personality_traits = {
                'big5': analyze_big5(results['scores']['big5']),
                'mbti': {
                    'type': results['mbti_type'],
                    'description': mbti_data.get('types', {}).get(results['mbti_type'], {}).get('description', 
                        '暂无该类型的详细描述')
                },
                'holland': {
                    'primary': {
                        'title': results.get('dominant_holland', [['R', 0]])[0][0],
                        'description': careers.get('holland_types', {}).get(
                            results.get('dominant_holland', [['R', 0]])[0][0], 
                            {}
                        ).get('description', '喜欢分析问题，追求逻辑性')
                    },
                    'secondary': {
                        'title': results.get('dominant_holland', [['R', 0], ['I', 0]])[1][0],
                        'description': careers.get('holland_types', {}).get(
                            results.get('dominant_holland', [['R', 0], ['I', 0]])[1][0], 
                            {}
                        ).get('description', '喜欢动手操作，注重实际效果')
                    }
                }
            }
            add_log("info", f"个性特征分析结果: {json.dumps(personality_traits, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            add_log("error", f"分析个性特征失败: {str(e)}\n{traceback.format_exc()}")
            raise
        
        # 计算领导力准则得分
        try:
            leadership_scores, leadership_analysis = calculate_leadership_scores(
                results, 
                leadership
            )
            add_log("info", f"领导力得分计算完成: {json.dumps(leadership_scores, ensure_ascii=False)}")
        except Exception as e:
            add_log("error", f"计算领导力得分失败: {str(e)}")
            raise
        
        # 生成领导力分析报告
        leadership_report = {
            'sorted_scores': leadership_scores,
            'top_analysis': leadership_analysis[:3],
            'bottom_analysis': leadership_analysis[-2:],
            'all_analysis': leadership_analysis
        }
        
        # 生成职业建议
        try:
            career_suggestions = []
            for holland_code in [results.get('dominant_holland', [['R', 0]])[0][0], results.get('dominant_holland', [['R', 0], ['I', 0]])[1][0]]:
                if holland_code in careers.get('suggestions', {}):
                    career_suggestions.extend(careers['suggestions'][holland_code])
            
            if not career_suggestions:
                career_suggestions = [{
                    'title': '技术发',
                    'positions': [
                        {
                            'name': '软件工程师',
                            'strengths': ['逻辑思维能力强', '善于解决问题'],
                            'improvements': '需要加强团队协作能力'
                        }
                    ]
                }]
            add_log("info", "职业建议生成完成")
        except Exception as e:
            add_log("error", f"生成职业建议失败: {str(e)}")
            raise
        
        # 生成发展建议
        try:
            development_suggestions = {
                'short_term': {
                    'strengths': '您的优势包括：\n- 分析问题能力强\n- 逻辑思维清晰\n- 善于独立思考',
                    'improvements': '短期内建议重点提升：\n- 团队协作能力\n- 沟通表达技巧\n- 项目管理能力'
                },
                'long_term': {
                    'career_path': '建议的职业发展路径：\n1. 初期专注于技术能力的提升\n2. 逐步承担项目管理职责\n3. 未来可以向技术总监方向发展',
                    'leadership': '领导力发展建议：\n1. 主动参与跨部门项目\n2. 培养团队管理能力\n3. 提升决策和判断能力'
                }
            }
            add_log("info", "发展建议生成完成")
        except Exception as e:
            add_log("error", f"生成发展建议失败: {str(e)}")
            raise
        
        # 生成最终报告
        final_report = {
            'personality_traits': personality_traits,
            'career_suggestions': career_suggestions,
            'development_suggestions': development_suggestions,
            'leadership_analysis': leadership_report,
            'scores': results['scores'],  # 添加原始分数
            'mbti_metadata': results.get('mbti_metadata', {}),  # 添加MBTI元数据
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        add_log("info", "=== 报告生成成功 ===")
        return final_report
        
    except Exception as e:
        error_msg = (
            f"\n=== 生成报告失败 ===\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"错误位置: {traceback.format_exc()}\n"
            f"输入数据: {json.dumps(results, ensure_ascii=False)}"
        )
        add_log("error", error_msg)
        return None

class ReportDisplayer:
    """报告显示类"""
    
    def __init__(self, visualizers):
        """初始化报告显示器
        
        Args:
            visualizers: 包含各种可视化器的字典
        """
        self.mbti_viz = visualizers['mbti']
        self.big5_viz = visualizers['big5']
        self.holland_viz = visualizers['holland']
        self.lp_viz = visualizers['lp']

    def display_personality_traits(self, report):
        """显示个性特质分析"""
        try:
            # 大五人格分析
            st.subheader("大五人格分析")
            
            # 获取大五人格数据
            big5_data = report['personality_traits']['big5']
            
            # 创建并显示双向条形图
            dual_bar_fig = self.big5_viz.create_dual_bar_chart({
                trait: data['score'] for trait, data in big5_data.items()
            })
            st.plotly_chart(dual_bar_fig, use_container_width=True, key="big5_dual_bar")
            
            # 创建大五人格表格数据
            table_data = []
            for trait, data in big5_data.items():
                score = data['score']
                # 根据分数确定水平
                if score >= 7:
                    level = "高"
                elif score >= 4:
                    level = "中"
                else:
                    level = "低"
                    
                table_data.append({
                    "特质维度": trait,
                    "得分": score,
                    "水平": level,
                    "特质说明": data['interpretation']
                })
                
            # 显示表格
            st.write("### 特质说明")
            df = pd.DataFrame(table_data)
            st.dataframe(
                df,
                column_config={
                    "特质维度": st.column_config.TextColumn("特质维度", width="medium"),
                    "得分": st.column_config.NumberColumn("得分", format="%.1f", width="small"),
                    "水平": st.column_config.TextColumn("水平", width="small"),
                    "特质说明": st.column_config.TextColumn("特质说明", width="large"),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # MBTI分析
            st.subheader("MBTI类型")
            mbti_data = report['personality_traits']['mbti']
            mbti_scores = report['scores']['mbti']
            mbti_metadata = report.get('mbti_metadata', {})
            
            # 创建并显示MBTI仪表盘
            mbti_gauge = self.mbti_viz.create_gauge_chart(
                mbti_scores,
                mbti_metadata
            )
            st.plotly_chart(mbti_gauge, use_container_width=True, key="mbti_gauge")
            
            # MBTI类型说明
            st.write(f"### 您的MBTI类型是：**{mbti_data['type']}**")
            
            # 显示类型详细信息
            st.write(mbti_data['description'])
            
            # 显示维度偏好强度
            st.write("\n**维度偏好强度：** " + 
                     " | ".join([f"{dim}: {strength:.1f}" for dim, strength in mbti_metadata['preference_strengths'].items()]))
            
            # 添加简化的MBTI分数和偏好强度的解释
            st.write("\n#### MBTI分数说明")
            st.write("""
            仪表盘显示分数（0-100）表示偏好方向：50分以上偏向左侧特质（E/S/T/J），50分以下偏向右侧特质（I/N/F/P）。
            
            偏好强度（0-20）表示特质倾向的程度：0-5为轻微，6-10为中等，11-15为明显，16-20为强烈。
            """)
            
            st.divider()
            
            # 霍兰德职业兴趣分析
            st.subheader("霍兰德职业兴趣")
            career_map = self.holland_viz.create_career_map(report['scores']['holland'])
            st.plotly_chart(career_map, use_container_width=True, key="holland_career_map")
            
            # 显示匹配职业表格
            match_data = self.holland_viz.create_match_table(report['scores']['holland'])
            df = pd.DataFrame(match_data)
            st.dataframe(df, use_container_width=True)
            
        except Exception as e:
            st.error(f"显示个性特质分析失败: {str(e)}")
            add_log("error", f"显示个性特质分析失败: {str(e)}")

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
        
        # 主要和次要发展方向
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

    def display_leadership_analysis(self, report):
        """显示领导力分析"""
        st.subheader("领导力准则得分")
        
        # 获取领导力准则数据
        scores_data = report['leadership_analysis']['sorted_scores']
        top_analysis = report['leadership_analysis']['top_analysis']
        bottom_analysis = report['leadership_analysis']['bottom_analysis']
        
        # 创建并显示玫瑰图
        rose_fig = self.lp_viz.create_rose_chart(scores_data)
        st.plotly_chart(rose_fig, use_container_width=True, key="lp_rose_chart")
        
        # 创建并显示准则分析表格
        table_data = self.lp_viz.create_principle_table(top_analysis, bottom_analysis)
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

    def display_development_suggestions(self, report):
        """显示发展建议"""
        try:
            config = load_config()
            if not config:
                st.error("配置文件加载失败")
                add_log("error", "配置文件加载失败")
                return
            
            # 准备提示词所需的数据
            big5_analysis = "\n".join([
                f"{trait}: 得分 {data['score']:.1f}\n{data['interpretation']}"
                for trait, data in report['personality_traits']['big5'].items()
            ])
            
            mbti_data = report['personality_traits']['mbti']
            holland_data = report['personality_traits']['holland']
            leadership_scores = report['leadership_analysis']['sorted_scores']
            leadership_analysis = "\n".join([
                f"{analysis['name']} (得分: {analysis['score']:.1f})\n{analysis['description']}"
                for analysis in report['leadership_analysis']['all_analysis']
            ])
            
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

3. 霍兰德职业兴趣：
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
1. 结合所有测评维度，分析此人的核心优势和潜在挑战
2. 基于领导力准则评估结果，就如何发挥优势、提升短板给出具体建议
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
                
                for chunk in api_client.generate_content_stream(prompt, "claude"):
                    if chunk:
                        full_response += chunk
                        st.write(full_response)
                        
                if not full_response:
                    st.error("生成发展建议时出错")
                else:
                    st.session_state.final_result = full_response
                    
        except Exception as e:
            st.error(f"生成发展建议失败: {str(e)}")
            add_log("error", f"生成发展建议失败: {str(e)}")

    def export_report(self, report):
        """导出完整报告为PDF"""
        try:
            # 创建PDF内存对象
            pdf_buffer = io.BytesIO()
            
            # 创建PDF文档
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # 注册中文字体（假设使用系统字体）
            try:
                pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
            except:
                # 如果找不到系统字体，使用默认字体
                pass
            
            # 创建样式
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(
                name='Chinese',
                fontName='SimSun' if 'SimSun' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
                fontSize=10,
                leading=14
            ))
            
            # 准备内容
            story = []
            
            # 添加标题
            title = Paragraph(
                f"六页纸领导力测评报告 - {st.session_state.user}",
                styles['Title']
            )
            story.append(title)
            
            # 添加时间
            story.append(Paragraph(
                f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles['Normal']
            ))
            story.append(Spacer(1, 12))
            
            # 保存当前页面上的所有图表
            figures = {}
            
            # 保存大五人格图
            big5_fig = self.big5_viz.create_dual_bar_chart({
                trait: data['score'] for trait, data in report['personality_traits']['big5'].items()
            })
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                big5_fig.write_image(tmp_file.name)
                figures['big5'] = tmp_file.name
            
            # 保存MBTI图
            mbti_fig = self.mbti_viz.create_gauge_chart(
                report['scores']['mbti'],
                report.get('mbti_metadata', {})
            )
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                mbti_fig.write_image(tmp_file.name)
                figures['mbti'] = tmp_file.name
            
            # 保存霍兰德图
            holland_fig = self.holland_viz.create_career_map(report['scores']['holland'])
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                holland_fig.write_image(tmp_file.name)
                figures['holland'] = tmp_file.name
            
            # 保存领导力准则图
            lp_fig = self.lp_viz.create_rose_chart(report['leadership_analysis']['sorted_scores'])
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                lp_fig.write_image(tmp_file.name)
                figures['leadership'] = tmp_file.name
            
            # 添加各部分内容和图表
            sections = [
                ("个性特质分析", ['big5', 'mbti']),
                ("霍兰德职业兴趣", ['holland']),
                ("领导力准则分析", ['leadership'])
            ]
            
            for section_title, section_figures in sections:
                story.append(Paragraph(section_title, styles['Heading1']))
                story.append(Spacer(1, 12))
                
                # 添加该部分的图表
                for fig_name in section_figures:
                    if fig_name in figures:
                        img = Image(figures[fig_name], width=450, height=300)
                        story.append(img)
                        story.append(Spacer(1, 12))
            
            # 添加发展建议
            if st.session_state.final_result:
                story.append(Paragraph("发展建议", styles['Heading1']))
                story.append(Spacer(1, 12))
                story.append(Paragraph(st.session_state.final_result, styles['Chinese']))
            
            # 生成PDF
            doc.build(story)
            
            # 准备下载
            pdf_buffer.seek(0)
            filename = f"六页纸领导力测评-{st.session_state.user}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # 触发下载
            st.download_button(
                label="💾 保存PDF报告",
                data=pdf_buffer,
                file_name=filename,
                mime="application/pdf",
                key="save_report"
            )
            
        except Exception as e:
            st.error(f"生成PDF报告失败: {str(e)}")
            add_log("error", f"生成PDF报告失败: {str(e)}")