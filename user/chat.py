import streamlit as st
from modules.api import APIClient
from user.logger import add_log

def show_chat_interface(api_client: APIClient):
    """显示聊天界面"""
    st.markdown("### AI聊天测试")
    
    # 创建一个聊天历史容器
    chat_container = st.container()
    
    # 创建输入框和发送按钮
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("请输入您的问题:", height=100)
        submitted = st.form_submit_button("发送")
    
    # 初始化聊天历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 处理用户输入
    if submitted and user_input:
        # 添加用户消息到历史
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        add_log("user", f"发送消息: {user_input[:50]}...")
        
        # 创建一个空白占位符用于显示AI回复
        response_placeholder = st.empty()
        content = ""
        
        try:
            # 记录输入字符数
            input_letters = len(user_input)
            content = ""
            
            # 流式生成回复
            for chunk in api_client.generate_content_stream(user_input):
                content += chunk
                response_placeholder.markdown(content)
            
            # 记录输出字符数并更新使用量
            output_letters = len(content)
            if not add_letters_record(input_letters, output_letters, "chat", "AI对话"):
                st.error("记录使用量失败")
                add_log("error", "记录使用量失败")
            else:
                # 添加AI回复到历史
                st.session_state.chat_history.append({"role": "assistant", "content": content})
                add_log("info", "AI回复完成")
            
        except Exception as e:
            error_msg = f"生成回复时出错: {str(e)}"
            add_log("error", error_msg)
            st.error(error_msg)
    
    # 在聊天容器中显示历史消息
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"**👤 您:** {message['content']}")
            else:
                st.markdown(f"**🤖 AI:** {message['content']}")
                st.markdown("---")

def clear_chat_history():
    """清除聊天历史"""
    if 'chat_history' in st.session_state:
        st.session_state.chat_history = []
        add_log("info", "聊天历史已清除") 