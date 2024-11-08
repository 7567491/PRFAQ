import json
from pathlib import Path
from datetime import datetime

def load_data():
    """加载所有必要的数据文件"""
    data_dir = Path(__file__).parent.parent / "data"
    
    try:
        with open(data_dir / "leadership_principles.json", 'r', encoding='utf-8') as f:
            leadership = json.load(f)
        with open(data_dir / "career_suggestions.json", 'r', encoding='utf-8') as f:
            careers = json.load(f)
        with open(data_dir / "mbti_descriptions.json", 'r', encoding='utf-8') as f:
            mbti = json.load(f)
        return leadership, careers, mbti
    except Exception as e:
        print(f"加载数据文件失败: {str(e)}")
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

def generate_report(results):
    """生成完整的测评报告"""
    try:
        # 加载必要的数据
        leadership, careers, mbti_data = load_data()
        
        # 分析各维度特征
        personality_traits = {
            'big5': analyze_big5(results['scores']['big5']),
            'mbti': {
                'type': results['mbti_type'],
                'description': mbti_data.get('types', {}).get(results['mbti_type'], {}).get('description', 
                    '暂无该类型的详细描述')
            },
            'holland': {
                'primary': {
                    'title': '实践型',  # 这里应该根据results['dominant_holland']来设置
                    'description': '喜欢动手操作，注重实际效果'
                },
                'secondary': {
                    'title': '研究型',
                    'description': '喜欢分析问题，追求逻辑性'
                }
            }
        }
        
        # 生成职业建议
        career_suggestions = [
            {
                'title': '技术研发',
                'positions': [
                    {
                        'name': '软件工程师',
                        'strengths': ['逻辑思维能力强', '善于解决问题'],
                        'improvements': '需要加强团队协作能力'
                    }
                ]
            }
        ]
        
        # 生成发展建议
        development_suggestions = {
            'short_term': {
                'strengths': '您的优势在于...',
                'improvements': '短期内可以重点提升...'
            },
            'long_term': {
                'career_path': '建议的职业发展路径...',
                'leadership': '领导力发展建议...'
            }
        }
        
        # 生成领导力分析
        leadership_analysis = {
            'sorted_scores': [
                ('创新精神', {'score': 85}),
                ('团队协作', {'score': 80})
            ],
            'top_analysis': [
                {
                    'name': '创新精神',
                    'score': 85,
                    'description': '善于创新思考',
                    'strength_analysis': '您在创新方面表现突出'
                }
            ]
        }
        
        return {
            'personality_traits': personality_traits,
            'career_suggestions': career_suggestions,
            'development_suggestions': development_suggestions,
            'leadership_analysis': leadership_analysis,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"生成报告失败: {str(e)}")
        return None