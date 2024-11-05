import streamlit as st
import requests
from datetime import datetime

def show_project_history():
    """显示项目历史记录"""
    st.header("生成历史")
    
    try:
        # 获取项目的PRFAQ历史
        response = requests.get(
            f"{st.session_state.API_URL}/prfaq/{st.session_state.current_project['id']}/list",
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        
        if response.status_code == 200:
            history = response.json()
            
            # 按类型分组显示
            pr_list = [h for h in history if h['type'] == 'pr']
            faq_list = [h for h in history if h['type'] == 'faq']
            internal_list = [h for h in history if h['type'] == 'internal_faq']
            mlp_list = [h for h in history if h['type'] == 'mlp']
            
            # 创建标签页
            tab1, tab2, tab3, tab4 = st.tabs(["新闻稿", "客户FAQ", "内部FAQ", "MLP"])
            
            with tab1:
                show_history_list("新闻稿历史", pr_list)
            with tab2:
                show_history_list("客户FAQ历史", faq_list)
            with tab3:
                show_history_list("内部FAQ历史", internal_list)
            with tab4:
                show_history_list("MLP历史", mlp_list)
                
        else:
            st.error(response.json()["detail"])
            
    except Exception as e:
        st.error(f"获取历史记录失败: {str(e)}")

def show_history_list(title: str, items: list):
    """显示历史记录列表"""
    st.subheader(title)
    
    if not items:
        st.info("暂无记录")
        return
        
    for item in items:
        with st.expander(f"{datetime.fromisoformat(item['created_at']).strftime('%Y-%m-%d %H:%M:%S')}"):
            st.markdown(item['content']) 