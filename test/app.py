import streamlit as st
import json
import random
from utils.test_processor import process_test_results
from utils.result_generator import generate_report
from utils.db_manager import DatabaseManager
import pandas as pd
from datetime import datetime
import plotly.express as px

# 初始化数据库管理器
db = DatabaseManager()

def load_data():
    """加载所有必要的数据文件"""
    try:
        with open('data/personality_questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)['questions']
    except Exception as e:
        st.error(f"加载题目数据失败: {str(e)}")
        questions = []

    try:
        with open('data/leadership_principles.json', 'r', encoding='utf-8') as f:
            leadership = json.load(f)['principles']
    except Exception as e:
        st.error(f"加载领导力准则数据失败: {str(e)}")
        leadership = []

    return questions, leadership

def initialize_session_state():
    """初始化session state"""
    if 'current_answers' not in st.session_state:
        st.session_state.current_answers = {}
    if 'test_submitted' not in st.session_state:
        st.session_state.test_submitted = False
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'user_name' not in st.session_state:
        st.session_state.user_name = ""

def display_intro():
    """显示首页内容"""
    st.title("职业测评系统")
    st.write("""
    欢迎使用职业测评系统！本系统将从以下几个维度对您进行全面的职业倾向评估：
    
    1. 大五人格测评
    2. MBTI性格类型
    3. 霍兰德职业兴趣
    4. 领导力准则匹配度
    
    测评完成后，您将获得：
    - 个性特征分析报告
    - 职业发展建议
    - 能力提升计划
    
    点击侧边栏的"开始测评"即可开始您的职业探索之旅！
    """)

def display_theory_intro(theory_type):
    """显示理论介绍页面"""
    if theory_type == "大五人格介绍":
        st.title("大五人格理论介绍")
        st.write("""
        大五人格理论是当代人格心理学最具影响力的理论之一，包括以下五个维度：
        
        1. 开放性 (Openness)：对新体验的接受程度
        2. 尽责性 (Conscientiousness)：做事的条理性和责任心
        3. 外向性 (Extraversion)：与他人交往的倾向
        4. 宜人性 (Agreeableness)：对他人的友善程度
        5. 情绪稳定性 (Neuroticism)：情绪的稳定程度
        """)
    
    elif theory_type == "MBTI介绍":
        st.title("MBTI性格类型理论介绍")
        st.write("""
        MBTI (Myers-Briggs Type Indicator) 是一个广泛使用的性格类型评估工具，包括四个维度：
        
        1. 能量来源：外向 (E) vs 内向 (I)
        2. 信息获取：感知 (S) vs 直觉 (N)
        3. 决策方式：思考 (T) vs 情感 (F)
        4. 生活方式：判断 (J) vs 知觉 (P)
        """)
    
    elif theory_type == "霍兰德代码介绍":
        st.title("霍兰德职业兴趣理论介绍")
        st.write("""
        霍兰德职业兴趣理论将职业兴趣分为六种类型：
        
        1. 实际型 (Realistic)：喜欢动手操作
        2. 研究型 (Investigative)：喜欢研究分析
        3. 艺术型 (Artistic)：具有创造力
        4. 社会型 (Social)：喜欢与人交往
        5. 企业型 (Enterprising)：具有领导才能
        6. 常规型 (Conventional)：喜欢按规则办事
        """)
    
    elif theory_type == "14条领导力准则":
        st.title("14条领导力则介绍")
        _, leadership = load_data()
        for principle in leadership:
            st.subheader(f"{principle['name']}")
            st.write(principle['description'])

def generate_random_answers():
    """生成随机答案"""
    answers = {}
    # 情境选择题（1-9题）
    for i in range(1, 10):
        answers[i] = random.choice(['A', 'B', 'C', 'D'])
    
    # 量表题（10-17题）
    for i in range(10, 18):
        answers[i] = random.randint(1, 5)
    
    # 排序题（18-20题）
    for i in range(18, 21):
        ranks = list(range(1, 5))
        random.shuffle(ranks)
        for j, rank in enumerate(['A', 'B', 'C', 'D']):
            answers[f"{i}_{rank}"] = ranks[j]
    
    return answers

def display_situation_question(q, index, current_answers):
    """显示情境选择题"""
    st.write(f"**第{index}题**")
    st.write(q['question'])
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    # 在左列显示选项A和B
    with col1:
        st.write("A. " + q['options']['A']['text'])
        st.write("B. " + q['options']['B']['text'])
    
    # 在右列显示选项C和D
    with col2:
        st.write("C. " + q['options']['C']['text'])
        st.write("D. " + q['options']['D']['text'])
    
    # 使用radio按钮进行选择
    answer = st.radio(
        "您的选择：",
        ['A', 'B', 'C', 'D'],
        key=f"q_{index}",
        index=['A', 'B', 'C', 'D'].index(current_answers.get(index, 'A')),
        horizontal=True
    )
    
    st.divider()
    return answer

def display_scale_question(q, index, current_answers):
    """显示量表题"""
    st.write(f"**第{index}题**")
    st.write(q['question'])
    
    # 使用columns让滑块和数值显示在同一行
    col1, col2 = st.columns([4, 1])
    
    with col1:
        value = st.slider(
            "符合程度：",
            1, 5,
            current_answers.get(index, 3),
            key=f"q_{index}"
        )
    
    with col2:
        st.write(
            {
                1: "完全不符合",
                2: "比较不符合",
                3: "一般",
                4: "比较符合",
                5: "完全符合"
            }[value]
        )
    
    st.divider()
    return value

def display_rank_question(q, index, current_answers):
    """显示排序题"""
    st.write(f"**第{index}题**")
    st.write(q['question'])
    
    # 创建一个表格式布局
    col1, col2 = st.columns(2)
    
    ranks = {}
    used_ranks = set()
    
    with col1:
        st.write("请为每个选项分配1-4的排序（1为最偏好，4为最不偏好）：")
        
        # 显示所有选项
        for opt in ['A', 'B', 'C', 'D']:
            st.write(f"{opt}. {q['options'][opt]['text']}")
    
    with col2:
        # 为每个选项创建一个数字输入框
        for opt in ['A', 'B', 'C', 'D']:
            key = f"{index}_{opt}"
            current_rank = current_answers.get(key, len(used_ranks) + 1)
            
            rank = st.number_input(
                f"选项{opt}的排序",
                min_value=1,
                max_value=4,
                value=int(current_rank),
                key=f"q_{key}"
            )
            
            ranks[key] = rank
            used_ranks.add(rank)
    
    # 检查排序是否有效
    if len(used_ranks) != 4:
        st.error("请确保每个选项的排序不重复，且都在1-4之间")
    
    st.divider()
    return ranks

def display_test():
    """显示测评页面"""
    try:
        questions, _ = load_data()
        if not questions:
            st.error("无法加载测评题目，请检查数据文件")
            return
        
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.header("职业测评")
            
            # 添加姓名输入框
            user_name = st.text_input(
                "请输入您的姓名：",
                value=st.session_state.user_name,
                key="name_input"
            )
            st.session_state.user_name = user_name
            
            # 创建标签页
            tab1, tab2, tab3 = st.tabs([
                "情境选择题 (1-9题)", 
                "行为频率量表题 (10-17题)", 
                "工作偏好排序题 (18-20题)"
            ])
            
            # 随机生成答案按钮
            if st.button("随机生成答案", key="random_btn"):
                st.session_state.current_answers = generate_random_answers()
                st.session_state.user_name = "Joe"  # 设置默认用户名
                st.rerun()
            
            with tab1:
                st.subheader("情境选择题")
                # 显示情境选择题（1-9题）
                for i in range(9):
                    q = questions[i]
                    st.session_state.current_answers[i+1] = display_situation_question(
                        q, i+1, st.session_state.current_answers
                    )
            
            with tab2:
                st.subheader("行为频率量表题")
                # 显示量表题（10-17题）
                for i in range(9, 17):
                    q = questions[i]
                    st.session_state.current_answers[i+1] = display_scale_question(
                        q, i+1, st.session_state.current_answers
                    )
            
            with tab3:
                st.subheader("工作偏好排序题")
                # 显示排序题（18-20题）
                for i in range(17, 20):
                    q = questions[i]
                    rank_answers = display_rank_question(
                        q, i+1, st.session_state.current_answers
                    )
                    st.session_state.current_answers.update(rank_answers)
            
            # 修改提交按钮部
            submit_col1, submit_col2 = st.columns([1, 4])
            with submit_col1:
                if st.button("提交测评", type="primary"):
                    if not st.session_state.user_name:
                        st.error("请输入您的姓名")
                    elif validate_answers(st.session_state.current_answers):
                        results = process_test_results(st.session_state.current_answers)
                        st.session_state.current_results = results
                        st.session_state.test_submitted = True
                        # 保存结果时包含用户名
                        db.save_result(results, user_id=st.session_state.user_name)
                    else:
                        st.error("请确保所有题目都已完成作答")
            
            with submit_col2:
                if not validate_answers(st.session_state.current_answers):
                    st.warning("⚠️ 还有未完成的题目")
        
        with col2:
            display_results()
    except Exception as e:
        st.error(f"显示测评页面时发生错误: {str(e)}")

def validate_answers(answers):
    """证答案是否完整"""
    # 检查情境选择题（1-9题）
    for i in range(1, 10):
        if i not in answers:
            return False
    
    # 检查量表题（10-17题）
    for i in range(10, 18):
        if i not in answers:
            return False
    
    # 检查排序题（18-20题）
    for i in range(18, 21):
        ranks = set()
        for opt in ['A', 'B', 'C', 'D']:
            key = f"{i}_{opt}"
            if key not in answers:
                return False
            ranks.add(answers[key])
        if ranks != {1, 2, 3, 4}:
            return False
    
    return True

def display_results():
    """显示测评结果"""
    st.header("测评结果")
    if st.session_state.test_submitted and st.session_state.current_results:
        report = generate_report(st.session_state.current_results)
        
        # 使用expander组件展示各部分结果
        with st.expander("个性特质分析", expanded=True):
            # 大五人格
            st.subheader("大五人格得分")
            big5_df = pd.DataFrame([
                {
                    '维度': k,
                    '得分': v['score'],
                    '解释': v['interpretation']
                }
                for k, v in report['personality_traits']['big5'].items()
            ])
            st.dataframe(big5_df, use_container_width=True)
            
            # MBTI
            st.subheader("MBTI类型")
            st.write(f"您的类型是：**{report['personality_traits']['mbti']['type']}**")
            st.write(report['personality_traits']['mbti']['description'])
            
            # 霍兰德代码
            st.subheader("霍兰德职业兴趣")
            st.write(f"主要类型：{report['personality_traits']['holland']['primary']['description']}")
            st.write(f"次要类型：{report['personality_traits']['holland']['secondary']['description']}")
        
        with st.expander("职业建议", expanded=True):
            for suggestion in report['career_suggestions']:
                st.subheader(f"推荐职业方向：{suggestion['title']}")
                for pos in suggestion['positions']:
                    st.write(f"- **{pos['name']}**")
                    st.write(f"  优势：{', '.join(pos['strengths'])}")
                    st.write(f"  需要提升：{pos['improvements']}")
        
        with st.expander("发展建议", expanded=True):
            # 短期发展建议
            st.subheader("短期发展建议")
            st.write(report['development_suggestions']['short_term']['strengths'])
            st.write(report['development_suggestions']['short_term']['improvements'])
            
            # 长期发展建议
            st.subheader("长期发展建议")
            st.write(report['development_suggestions']['long_term']['career_path'])
            st.write(report['development_suggestions']['long_term']['leadership'])
        
        # 添加领导力培养部分
        with st.expander("领导力培养", expanded=True):
            st.subheader("领导力准则得分")
            
            # 显示所有准则得分
            scores_df = pd.DataFrame([
                {
                    '准则': name,
                    '得分': data['score']
                }
                for name, data in report['leadership_analysis']['sorted_scores']
            ])
            st.dataframe(scores_df, use_container_width=True)
            
            # 显示高分准则分析
            st.subheader("优势准则分析")
            for analysis in report['leadership_analysis']['top_analysis']:
                with st.container():
                    st.write(f"**{analysis['name']}** (得分: {analysis['score']})")
                    st.write(analysis['description'])
                    st.write(analysis['strength_analysis'])
                    st.divider()
            
            # 显示低分准则分析
            st.subheader("需要提升的准则")
            for analysis in report['leadership_analysis']['bottom_analysis']:
                with st.container():
                    st.write(f"**{analysis['name']}** (得分: {analysis['score']})")
                    st.write(analysis['description'])
                    st.write(analysis['improvement_suggestions'])
                    st.divider()
        
        # 下载报告按钮
        st.download_button(
            label="下载完整报告",
            data=json.dumps(report, ensure_ascii=False, indent=2),
            file_name="career_assessment_report.json",
            mime="application/json"
        )
    else:
        st.info("请完成左侧测评后查看结果")

def display_history():
    """显示历史数据页面"""
    st.title("历史测评记录")
    
    try:
        # 创建左右两栏
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.subheader("测评记录概览")
            
            # 获取统计数据
            stats = db.get_statistics()
            
            # 显示统计信息
            total_tests = stats.get('total_tests', 0)
            st.metric("总测评次数", total_tests)
            
            if total_tests > 0:
                # 获取历史记录
                history = db.get_history()
                if history:
                    st.subheader("历史测评记录")
                    # 为每条记录创建一个卡片式显示
                    for record in history:
                        with st.container():
                            st.markdown("""
                            <style>
                            .record-card {
                                padding: 10px;
                                border: 1px solid #ddd;
                                border-radius: 5px;
                                margin: 10px 0;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                            
                            cols = st.columns([3, 1])
                            with cols[0]:
                                st.markdown(f"""
                                <div class='record-card'>
                                👤 <b>{record['user_name']}</b><br>
                                📅 {record['timestamp']}<br>
                                🎯 MBTI: <b>{record['mbti_type']}</b><br>
                                💼 推荐: {record.get('recommended_position', '未记录')}
                                </div>
                                """, unsafe_allow_html=True)
                            with cols[1]:
                                if st.button("查看详情", key=f"view_{record['id']}"):
                                    st.session_state.selected_record = record['id']
                                    st.session_state.current_record = record
                
                # 显示MBTI分布统计
                if stats.get('mbti_distribution'):
                    st.subheader("MBTI类型分布")
                    mbti_dist = pd.DataFrame(
                        list(stats['mbti_distribution'].items()),
                        columns=['MBTI类型', '数量']
                    ).sort_values('数量', ascending=False)
                    
                    # 使用条形图显示分布
                    fig = px.bar(mbti_dist, 
                                x='MBTI类型', 
                                y='数量',
                                title='MBTI类型分布')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无历史记录")
        
        with col2:
            st.subheader("测评结果详情")
            if 'selected_record' in st.session_state:
                try:
                    # 获取选中的记录
                    record = db.get_result(st.session_state.selected_record)
                    if record:
                        # 重建结果数据结构
                        holland_scores = json.loads(record['holland_scores']) if isinstance(record['holland_scores'], str) else record['holland_scores']
                        
                        # 计算dominant_holland
                        dominant_holland = sorted(
                            holland_scores.items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:2]
                        
                        results = {
                            'scores': {
                                'mbti': json.loads(record['mbti_scores']) if isinstance(record['mbti_scores'], str) else record['mbti_scores'],
                                'big5': json.loads(record['big5_scores']) if isinstance(record['big5_scores'], str) else record['big5_scores'],
                                'holland': holland_scores
                            },
                            'mbti_type': record['mbti_type'],
                            'dominant_holland': dominant_holland
                        }
                        
                        # 生成报告
                        report = generate_report(results)
                        
                        # 使用tabs组织内容
                        tab1, tab2, tab3, tab4 = st.tabs([
                            "个性特质", "职业建议", "发展建议", "领导力分析"
                        ])
                        
                        with tab1:
                            # 大五人格
                            st.subheader("大五人格得分")
                            big5_df = pd.DataFrame([
                                {
                                    '维度': k,
                                    '得分': v['score'],
                                    '解释': v['interpretation']
                                }
                                for k, v in report['personality_traits']['big5'].items()
                            ])
                            
                            # 使用雷达图显示大五人格得分
                            fig = px.line_polar(
                                big5_df, 
                                r='得分', 
                                theta='维度', 
                                line_close=True,
                                title='大五人格分析'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 显示详细解释
                            st.dataframe(big5_df, use_container_width=True)
                            
                            # MBTI
                            st.subheader("MBTI类型")
                            st.write(f"类型：**{report['personality_traits']['mbti']['type']}**")
                            st.write(report['personality_traits']['mbti']['description'])
                            
                            # 霍兰德代码
                            st.subheader("霍兰德职业兴趣")
                            st.write(f"主要类型：{report['personality_traits']['holland']['primary']['description']}")
                            st.write(f"次要类型：{report['personality_traits']['holland']['secondary']['description']}")
                        
                        with tab2:
                            for suggestion in report['career_suggestions']:
                                st.subheader(f"推荐职业方向：{suggestion['title']}")
                                for pos in suggestion['positions']:
                                    with st.expander(pos['name']):
                                        st.write("**优势：**")
                                        for strength in pos['strengths']:
                                            st.write(f"- {strength}")
                                        st.write("**需要提升：**")
                                        st.write(f"- {pos['improvements']}")
                        
                        with tab3:
                            # 短期发展建议
                            st.subheader("短期发展建议")
                            st.write(report['development_suggestions']['short_term']['strengths'])
                            st.write(report['development_suggestions']['short_term']['improvements'])
                            st.write(report['development_suggestions']['short_term']['action_plan'])
                            
                            # 长期发展建议
                            st.subheader("长期发展建议")
                            st.write(report['development_suggestions']['long_term']['career_path'])
                            st.write(report['development_suggestions']['long_term']['capability'])
                            st.write(report['development_suggestions']['long_term']['leadership'])
                        
                        with tab4:
                            st.subheader("领导力准则分析")
                            if 'leadership_analysis' in report:
                                # 显示所有准则得分
                                scores_df = pd.DataFrame([
                                    {
                                        '准则': name,
                                        '得分': data['score']
                                    }
                                    for name, data in report['leadership_analysis']['sorted_scores']
                                ]).sort_values('得分', ascending=False)
                                
                                # 使用条形图显示得分分布
                                fig = px.bar(scores_df, 
                                           x='准则', 
                                           y='得分',
                                           title='领导力准则得分分布')
                                fig.update_layout(
                                    xaxis_tickangle=-45,
                                    height=500
                                )
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # 显示详细分析
                                st.subheader("详细分析")
                                
                                # 高分准则分析
                                st.write("#### 优势准则")
                                for analysis in report['leadership_analysis']['top_analysis']:
                                    with st.expander(f"{analysis['name']} (得分: {analysis['score']})"):
                                        st.write("**准则描述：**")
                                        st.write(analysis['description'])
                                        st.write("**优势分析：**")
                                        st.write(analysis['strength_analysis'])
                                
                                # 低分准则分析
                                st.write("#### 待提升准则")
                                for analysis in report['leadership_analysis']['bottom_analysis']:
                                    with st.expander(f"{analysis['name']} (得分: {analysis['score']})"):
                                        st.write("**准则描述：**")
                                        st.write(analysis['description'])
                                        st.write("**提升建议：**")
                                        st.write(analysis['improvement_suggestions'])
                                
                                # 添加雷达图
                                top_principles = scores_df.head(6)  # 取前6个准则
                                fig_radar = px.line_polar(
                                    top_principles, 
                                    r='得分', 
                                    theta='准则',
                                    line_close=True,
                                    title='领导力准则雷达图（前6项）'
                                )
                                st.plotly_chart(fig_radar, use_container_width=True)
                                
                                # 添加统计信息
                                st.subheader("统计概要")
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    avg_score = scores_df['得分'].mean()
                                    st.metric("平均得分", f"{avg_score:.1f}")
                                with col2:
                                    max_score = scores_df['得分'].max()
                                    st.metric("最高得分", f"{max_score:.1f}")
                                with col3:
                                    min_score = scores_df['得分'].min()
                                    st.metric("最低得分", f"{min_score:.1f}")
                            else:
                                st.info("未找到领导力分析数据")
                                
                        # 下载报告按钮移到这里
                        st.download_button(
                            label="下载完整报告",
                            data=json.dumps(report, ensure_ascii=False, indent=2),
                            file_name=f"career_assessment_report_{record['timestamp']}.json",
                            mime="application/json"
                        )
                    else:
                        st.info("请在左侧选择要查看的测评记录")
                except Exception as e:
                    st.error(f"加载测评结果时发生错误: {str(e)}")
                    if st.checkbox("显示详细错误信息"):
                        st.exception(e)
            else:
                st.info("请在左侧选择要查看的测评记录")
    
    except Exception as e:
        st.error(f"显示历史记录时发生错误: {str(e)}")
        if st.checkbox("显示详细错误信息"):
            st.exception(e)

def main():
    st.set_page_config(layout="wide", page_title="职业测评系统")
    
    initialize_session_state()
    
    # 侧边栏
    with st.sidebar:
        st.title("职业测评系统")
        page = st.radio(
            "导航",
            ["首页", "大五人格介绍", "MBTI介绍", 
             "霍兰德代码介绍", "14条领导力准则", 
             "开始测评", "历史数据"]
        )
    
    # 主页面内容
    if page == "首页":
        display_intro()
    elif page == "开始测评":
        display_test()
    elif page == "历史数据":
        display_history()
    else:
        display_theory_intro(page)

if __name__ == "__main__":
    main() 