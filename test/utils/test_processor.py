import json
from pathlib import Path

def custom_sigmoid(x, steepness=5):
    """自定义sigmoid函数，steepness控制曲线陡度"""
    import math
    return 1 / (1 + math.exp(-steepness * x))

def process_mbti_scores(answers, questions):
    """Enhanced MBTI scoring system"""
    # Initialize detailed scoring structure
    mbti_detailed = {
        'E-I': {'E': {'raw': 0, 'weighted': 0}, 'I': {'raw': 0, 'weighted': 0}},
        'S-N': {'S': {'raw': 0, 'weighted': 0}, 'N': {'raw': 0, 'weighted': 0}},
        'T-F': {'T': {'raw': 0, 'weighted': 0}, 'F': {'raw': 0, 'weighted': 0}},
        'J-P': {'J': {'raw': 0, 'weighted': 0}, 'P': {'raw': 0, 'weighted': 0}}
    }
    
    # Question type weights
    weights = {
        'situational': 2.0,  # 情境题权重
        'scale': 1.5,       # 量表题权重
        'ranking': 1.0      # 排序题权重
    }
    
    # Process each question
    for i, answer in answers.items():
        try:
            # 处理题号
            if isinstance(i, str) and '_' in i:
                # 排序题的情况（如"18_A"）
                q_num = int(i.split('_')[0])
                q_idx = q_num - 1
            else:
                # 普通题目的情况
                q_idx = int(i) - 1
                
            if q_idx < 0 or q_idx >= len(questions):
                continue
                
            question = questions[q_idx]
            q_type = question.get('type', 'situational')
            
            if q_idx < 9:  # 情境选择题
                if isinstance(answer, str) and answer in question['options']:
                    dims = question['options'][answer]['dimensions'].get('mbti', [])
                    weight = weights['situational']
                    for dim in dims:
                        for pair in mbti_detailed.values():
                            if dim in pair:
                                pair[dim]['raw'] += 1
                                pair[dim]['weighted'] += weight
                                
            elif q_idx < 17:  # 量表题
                if isinstance(answer, (int, float)):
                    dims = question['dimensions'].get('mbti', [])
                    weight = weights['scale'] * (answer - 3)  # 转换1-5分为-2到2分
                    for dim in dims:
                        for pair in mbti_detailed.values():
                            if dim in pair:
                                pair[dim]['raw'] += abs(weight)
                                pair[dim]['weighted'] += weight
                                
            else:  # 排序题
                if isinstance(i, str) and '_' in i:
                    _, opt = i.split('_')
                    if opt in question['options']:
                        dims = question['options'][opt]['dimensions'].get('mbti', [])
                        rank = float(answer)
                        weight = weights['ranking'] * (4.5 - rank)  # 转换1-4排序为3.5到0.5分
                        for dim in dims:
                            for pair in mbti_detailed.values():
                                if dim in pair:
                                    pair[dim]['raw'] += abs(weight)
                                    pair[dim]['weighted'] += weight
                                    
        except (ValueError, TypeError) as e:
            print(f"处理题目 {i} 时出错: {str(e)}")
            continue
    
    # Calculate final scores and preferences
    mbti_results = {}
    mbti_type = ''
    
    for dimension, pair in mbti_detailed.items():
        dim1, dim2 = dimension.split('-')
        total_raw = pair[dim1]['raw'] + pair[dim2]['raw']
        total_weighted = abs(pair[dim1]['weighted']) + abs(pair[dim2]['weighted'])
        
        if total_weighted > 0:
            # Calculate preference strength (0-1)
            strength = abs(pair[dim1]['weighted'] - pair[dim2]['weighted']) / total_weighted
            # Apply sigmoid for smoother distribution
            preference = custom_sigmoid(strength * 3)  # 调整系数以获得更好的分布
            
            # Determine dominant preference
            if pair[dim1]['weighted'] >= pair[dim2]['weighted']:
                mbti_type += dim1
                mbti_results[dim1] = preference
                mbti_results[dim2] = 1 - preference
            else:
                mbti_type += dim2
                mbti_results[dim2] = preference
                mbti_results[dim1] = 1 - preference
        else:
            # Default slight preference if no clear direction
            mbti_type += dim1
            mbti_results[dim1] = 0.51
            mbti_results[dim2] = 0.49
    
    # Add confidence intervals and metadata
    mbti_metadata = {
        'raw_scores': mbti_detailed,
        'preference_strengths': {
            'E-I': abs(mbti_detailed['E-I']['E']['weighted'] - mbti_detailed['E-I']['I']['weighted']),
            'S-N': abs(mbti_detailed['S-N']['S']['weighted'] - mbti_detailed['S-N']['N']['weighted']),
            'T-F': abs(mbti_detailed['T-F']['T']['weighted'] - mbti_detailed['T-F']['F']['weighted']),
            'J-P': abs(mbti_detailed['J-P']['J']['weighted'] - mbti_detailed['J-P']['P']['weighted'])
        }
    }
    
    return mbti_results, mbti_type, mbti_metadata

def process_test_results(answers):
    """处理测评答案，计算各维度分数"""
    try:
        from modules.utils import add_log
        
        # 加载题目数据
        data_dir = Path(__file__).parent.parent / "data"
        with open(data_dir / "personality_questions.json", 'r', encoding='utf-8') as f:
            questions = json.load(f)['questions']
        
        # 处理MBTI得分
        mbti_results, mbti_type, mbti_metadata = process_mbti_scores(answers, questions)
        
        # 初始化大五人格分数（使用中文键名）
        big5_scores = {
            '开放性': 0,  # O
            '尽责性': 0,  # C
            '外向性': 0,  # E
            '宜人性': 0,  # A
            '情绪稳定性': 0  # N
        }
        
        # 维度映射表
        big5_mapping = {
            'O': '开放性',
            'C': '尽责性',
            'E': '外向性',
            'A': '宜人性',
            'N': '情绪稳定性'
        }
        
        # 标准化Big5和Holland分数到1-10范围
        def normalize_to_range(scores, min_val=1, max_val=10):
            values = list(scores.values())
            if not values:
                return scores
            old_min, old_max = min(values), max(values)
            if old_min == old_max:
                return {k: (min_val + max_val) / 2 for k in scores}
            return {
                k: min_val + (v - old_min) * (max_val - min_val) / (old_max - old_min)
                for k, v in scores.items()
            }
        
        holland_scores = {
            'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0
        }
        
        # 处理所有题目的得分
        for i in range(1, 21):
            if i <= 9:  # 情境选择题
                answer = answers.get(i)
                if answer:
                    question = questions[i-1]
                    option = question['options'][answer]
                    dimensions = option['dimensions']
                    
                    # 更新Big5分数（使用映射）
                    for dim in dimensions.get('big5', []):
                        if dim in big5_mapping:
                            big5_scores[big5_mapping[dim]] += 2
                    
                    # 更新Holland分数
                    for dim in dimensions['holland']:
                        holland_scores[dim] += 2
                        
            elif i <= 17:  # 量表题
                score = answers.get(i, 3)
                question = questions[i-1]
                dimensions = question['dimensions']
                weight = score - 3  # 转换为-2到2的权重
                
                for dim_type, dims in dimensions.items():
                    if dim_type == 'big5':
                        for dim in dims:
                            if dim in big5_mapping:
                                big5_scores[big5_mapping[dim]] += weight
                    elif dim_type == 'holland':
                        for dim in dims:
                            holland_scores[dim] += weight
                            
            else:  # 排序题
                for opt in ['A', 'B', 'C', 'D']:
                    key = f"{i}_{opt}"
                    rank = answers.get(key)
                    if rank:
                        dimensions = questions[i-1]['options'][opt]['dimensions']
                        weight = 2.5 - rank  # 转换为1.5到-1.5的权重
                        
                        for dim_type, dims in dimensions.items():
                            if dim_type == 'big5':
                                for dim in dims:
                                    if dim in big5_mapping:
                                        big5_scores[big5_mapping[dim]] += weight
                            elif dim_type == 'holland':
                                for dim in dims:
                                    holland_scores[dim] += weight
        
        # 标准化Big5分数到1-10范围
        big5_normalized = normalize_to_range(big5_scores)
        
        # 标准化Holland分数到1-10范围
        holland_normalized = normalize_to_range(holland_scores)
        
        # 记录处理结果
        add_log("info", f"Big5得分: {json.dumps(big5_normalized, ensure_ascii=False)}")
        add_log("info", f"Holland得分: {json.dumps(holland_normalized, ensure_ascii=False)}")
        
        return {
            'scores': {
                'mbti': mbti_results,
                'big5': big5_normalized,
                'holland': holland_normalized
            },
            'mbti_type': mbti_type,
            'mbti_metadata': mbti_metadata,  # 添加详细的MBTI数据
            'dominant_holland': sorted(
                holland_normalized.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:2],
            'answers': answers
        }
        
    except Exception as e:
        print(f"处理测评结果时发生错误: {str(e)}")
        raise
