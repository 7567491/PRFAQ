import json
from pathlib import Path

def process_test_results(answers):
    """处理测评答案，计算各维度分数"""
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
    
    try:
        # 修改数据文件路径，使用绝对路径
        data_dir = Path(__file__).parent.parent / "data"
        with open(data_dir / "personality_questions.json", 'r', encoding='utf-8') as f:
            questions = json.load(f)['questions']
        
        # 处理情境选择题（1-9题）
        for i in range(1, 10):
            answer = answers.get(i)
            if answer:
                question = questions[i-1]
                option = question['options'][answer]
                dimensions = option['dimensions']
                
                # 更新MBTI分数
                for dim in dimensions['mbti']:
                    mbti_scores[dim] += 1
                
                # 更新大五人格分数
                for dim in dimensions['big5']:
                    big5_scores[dim] += 1
                    
                # 更新霍兰德代码分数
                for dim in dimensions['holland']:
                    holland_scores[dim] += 1
        
        # 处理量表题（10-17题）
        for i in range(10, 18):
            score = answers.get(i, 3)  # 默认值为3
            question = questions[i-1]
            dimensions = question['dimensions']
            
            # 根据量表分数更新各维度
            weight = (score - 3) / 2  # 将1-5转换为-1到1的权重
            
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
        
        # 处理排序题（18-20题）
        for i in range(18, 21):
            question = questions[i-1]
            options = question['options']
            
            # 获取当前题目的所有答案
            current_answers = {
                k: v for k, v in answers.items() 
                if isinstance(k, str) and k.startswith(f"{i}_")
            }
            
            # 处理每个选项的排序
            for key, rank in current_answers.items():
                opt = key.split('_')[1]  # 获取选项（A/B/C/D）
                dimensions = options[opt]['dimensions']
                weight = (5 - rank) / 2  # 将1-4的排序转换为权重
                
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
        
        # 标准化分数
        def normalize_scores(scores, scale=5):
            total = sum(scores.values())
            if total == 0:
                return scores
            return {k: round(v/total * scale, 2) for k, v in scores.items()}
        
        # 计算MBTI类型
        def get_mbti_type():
            type_pairs = [
                ('E', 'I'), ('S', 'N'), ('T', 'F'), ('J', 'P')
            ]
            mbti_type = ''
            for a, b in type_pairs:
                mbti_type += a if mbti_scores[a] >= mbti_scores[b] else b
            return mbti_type
        
        normalized_scores = {
            'mbti': normalize_scores(mbti_scores),
            'big5': normalize_scores(big5_scores),
            'holland': normalize_scores(holland_scores)
        }
        
        return {
            'scores': normalized_scores,
            'mbti_type': get_mbti_type(),
            'dominant_holland': sorted(
                holland_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:2]
        }
    
    except Exception as e:
        print(f"处理测评结果时发生错误: {str(e)}")
        raise
