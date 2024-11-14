import json
from pathlib import Path

def custom_sigmoid(x, steepness=5):
    """自定义sigmoid函数，steepness控制曲线陡度"""
    import math
    return 1 / (1 + math.exp(-steepness * x))

def process_test_results(answers):
    """处理测评答案，计算各维度分数"""
    try:
        from modules.utils import add_log
        add_log("info", "\n=== 开始处理测评结果 ===")
        
        # 初始化各维度的分数
        mbti_scores = {
            'E': 0, 'I': 0, 'S': 0, 'N': 0,
            'T': 0, 'F': 0, 'J': 0, 'P': 0
        }
        
        big5_scores = {
            'O': 0, 'C': 0, 'E': 0, 'A': 0, 'N': 0
        }
        
        holland_scores = {
            'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0
        }
        
        # 加载题目数据
        data_dir = Path(__file__).parent.parent / "data"
        with open(data_dir / "personality_questions.json", 'r', encoding='utf-8') as f:
            questions = json.load(f)['questions']
        
        # 处理所有题目的得分
        for i in range(1, 21):
            if i <= 9:  # 情境选择题
                answer = answers.get(i)
                if answer:
                    question = questions[i-1]
                    option = question['options'][answer]
                    dimensions = option['dimensions']
                    
                    # 更新MBTI分数
                    for dim in dimensions['mbti']:
                        mbti_scores[dim] += 2
                    
                    # 更新Big5分数
                    for dim in dimensions['big5']:
                        big5_scores[dim] += 2
                    
                    # 更新Holland分数
                    for dim in dimensions['holland']:
                        holland_scores[dim] += 2
                        
            elif i <= 17:  # 量表题
                score = answers.get(i, 3)
                question = questions[i-1]
                dimensions = question['dimensions']
                weight = score - 3  # 转换为-2到2的权重
                
                for dim_type, dims in dimensions.items():
                    if dim_type == 'mbti':
                        for dim in dims:
                            mbti_scores[dim] += weight
                    elif dim_type == 'big5':
                        for dim in dims:
                            big5_scores[dim] += weight
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
                            if dim_type == 'mbti':
                                for dim in dims:
                                    mbti_scores[dim] += weight
                            elif dim_type == 'big5':
                                for dim in dims:
                                    big5_scores[dim] += weight
                            elif dim_type == 'holland':
                                for dim in dims:
                                    holland_scores[dim] += weight
        
        # 标准化MBTI分数
        mbti_pairs = [('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')]
        mbti_normalized = {}
        for pair in mbti_pairs:
            score_a = mbti_scores[pair[0]]
            score_b = mbti_scores[pair[1]]
            total = abs(score_a) + abs(score_b)
            
            if total > 0:
                diff = (score_a - score_b) / (max(abs(score_a), abs(score_b)))
                normalized_a = custom_sigmoid(diff)
                mbti_normalized[pair[0]] = round(normalized_a, 3)
                mbti_normalized[pair[1]] = round(1 - normalized_a, 3)
            else:
                mbti_normalized[pair[0]] = 0.51
                mbti_normalized[pair[1]] = 0.49
        
        # 确定MBTI类型
        mbti_type = ''
        for a, b in mbti_pairs:
            mbti_type += a if mbti_normalized[a] >= mbti_normalized[b] else b
        
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
        
        big5_normalized = normalize_to_range(big5_scores)
        holland_normalized = normalize_to_range(holland_scores)
        
        # 记录处理结果
        add_log("info", f"Big5得分: {json.dumps(big5_normalized, ensure_ascii=False)}")
        add_log("info", f"Holland得分: {json.dumps(holland_normalized, ensure_ascii=False)}")
        
        return {
            'scores': {
                'mbti': mbti_normalized,
                'big5': big5_normalized,
                'holland': holland_normalized
            },
            'mbti_type': mbti_type,
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
