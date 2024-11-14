import json
from pathlib import Path
from datetime import datetime
import traceback
import numpy as np

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
    trait_names = {
        'O': '开放性',
        'C': '尽责性',
        'E': '外向性',
        'A': '宜人性',
        'N': '情绪稳定性'
    }
    
    interpretations = {
        'O': {
            'high': '你对新体验持开放态度，富有创造力和想象力。善于接受新观念，勇于尝试新事物。',
            'low': '你倾向于传统和实际的方法，重视稳定性。更喜欢熟悉和可预测的环境。'
        },
        'C': {
            'high': '你做事有条理，负责任，值得信赖。工作认真细致，有很强的计划性和目标导向。',
            'low': '你比较随性，灵活，不拘泥于计划。更注重当下的体验，而非长期规划。'
        },
        'E': {
            'high': '你善于社交，充满活力，喜欢与人互动。在团队中往往能发挥积极的影响力。',
            'low': '你倾向于独处，深思熟虑，注重内在体验。善于独立工作和深度思考。'
        },
        'A': {
            'high': '你富有同理心，善解人意，乐于助人。在团队合作中能很好地维护人际关系。',
            'low': '你独立自主，直言不讳，注重实事求是。在决策时更看重客观事实而非情感因素。'
        },
        'N': {
            'high': '你情绪稳定，能很好地控制压力和焦虑。在面对挑战时保持冷静和理性。',
            'low': '你情感丰富，对环境变化比较敏感。对周围的细微变化有敏锐的感知能力。'
        }
    }
    
    analysis = {}
    for trait, score in scores.items():
        analysis[trait_names[trait]] = {
            'score': score,
            'interpretation': interpretations[trait]['high'] if score > 3 else interpretations[trait]['low']
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
        
        # 生成分析结果
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
        add_log("info", f"输入数据: {json.dumps(results, ensure_ascii=False)}")
        
        # 加载必要的数据
        leadership, careers, mbti_data = load_data()
        if not leadership or not careers or not mbti_data:
            add_log("error", "数据文件加载失败：一个或多个数据文件为空")
            raise ValueError("数据文件加载失败")
            
        add_log("info", "数据文件加载成功")
        
        # 获取Holland代码
        dominant_holland = results.get('dominant_holland', [])
        holland_primary = dominant_holland[0][0] if dominant_holland and len(dominant_holland) > 0 else 'R'
        holland_secondary = dominant_holland[1][0] if dominant_holland and len(dominant_holland) > 1 else 'I'
        
        add_log("info", f"Holland代码: 主要={holland_primary}, 次要={holland_secondary}")
        
        # 分析各维度特征
        try:
            personality_traits = {
                'big5': analyze_big5(results['scores']['big5']),
                'mbti': {
                    'type': results['mbti_type'],
                    'description': mbti_data.get('types', {}).get(results['mbti_type'], {}).get('description', 
                        '暂无该类型的详细描述')
                },
                'holland': {
                    'primary': {
                        'title': holland_primary,
                        'description': careers.get('holland_types', {}).get(holland_primary, {}).get('description', 
                            '喜欢分析问题，追求逻辑性')
                    },
                    'secondary': {
                        'title': holland_secondary,
                        'description': careers.get('holland_types', {}).get(holland_secondary, {}).get('description', 
                            '喜欢动手操作，注重实际效果')
                    }
                }
            }
            add_log("info", "个性特征分析完成")
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
            for holland_code in [holland_primary, holland_secondary]:
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