import streamlit as st
from urllib.parse import urlencode
import logging

def init_mp_session():
    """初始化MP用户会话状态"""
    if "mp_authenticated" not in st.session_state:
        st.session_state.mp_authenticated = False

def main():
    init_mp_session()
    
    # 如果已登录，重定向到主页
    if st.session_state.mp_authenticated:
        st.switch_page("app.py")
        return
    
    st.title("AWS Marketplace 用户登录")
    
    # 获取URL参数
    mp_user = st.query_params.get("user")
    aws_account = st.query_params.get("account")
    product_code = st.query_params.get("product")
    
    if not all([mp_user, aws_account, product_code]):
        st.error("登录信息不完整")
        return
    
    # 显示用户信息
    st.info(f"欢迎 AWS Marketplace 用户")
    st.markdown("""
    ### 您的AWS Marketplace账户信息
    系统已自动识别您的身份：
    """)
    
    st.text(f"用户名: {mp_user}")
    st.text(f"AWS账号: {aws_account}")
    st.text(f"产品代码: {product_code}")
    
    # 自动登录按钮
    if st.button("确认登录"):
        # 处理MP用户登录
        st.session_state.mp_authenticated = True
        st.session_state.user = mp_user
        st.session_state.aws_account = aws_account
        st.session_state.product_code = product_code
        st.success("登录成功！")
        st.switch_page("app.py")

if __name__ == "__main__":
    main() 