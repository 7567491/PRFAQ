import streamlit as st
from user.user_base import UserManager
from modules.notifier import send_wecom_message
from user.analysis import show_user_analytics

def show_user_management():
    """显示用户管理界面"""
    st.subheader("用户管理")
    
    user_mgr = UserManager()
    users = user_mgr.list_users()
    
    # 添加新用户按钮
    if st.button("➕ 添加新用户"):
        st.session_state.show_add_user = True
    
    # 添加新用户表单
    if st.session_state.get('show_add_user', False):
        with st.form("add_user_form"):
            st.subheader("添加新用户")
            new_username = st.text_input("用户名")
            new_password = st.text_input("密码", type="password")
            new_role = st.selectbox("角色", ["user", "admin"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("确认添加"):
                    if new_username and new_password:
                        success, message = user_mgr.create_user(new_username, new_password, new_role)
                        if success:
                            st.success(f"用户 {new_username} 创建成功")
                            send_wecom_message('action', st.session_state.user,
                                action="创建新用户",
                                details=f"创建用户: {new_username}, 角色: {new_role}"
                            )
                            st.session_state.show_add_user = False
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("用户名和密码不能为空")
            with col2:
                if st.form_submit_button("取消"):
                    st.session_state.show_add_user = False
                    st.rerun()
    
    # 显示用户列表
    if users:
        # 创建用户数据表格
        user_data = []
        for user in users:
            user_data.append({
                "ID": user['user_id'],
                "用户名": user['username'],
                "角色": user['role'],
                "状态": "启用" if user['is_active'] else "禁用",
                "创建时间": user['created_at'],
                "最后登录": user['last_login'] or "从未登录"
            })
        
        # 使用 st.dataframe 显示用户列表
        st.dataframe(
            user_data,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "用户名": st.column_config.TextColumn("用户名", width="medium"),
                "角色": st.column_config.TextColumn("角色", width="small"),
                "状态": st.column_config.TextColumn("状态", width="small"),
                "创建时间": st.column_config.DatetimeColumn("创建时间", width="medium"),
                "最后登录": st.column_config.DatetimeColumn("最后登录", width="medium")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # 用户操作部分
        st.subheader("用户操作")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_user = st.selectbox(
                "选择用户",
                [user['username'] for user in users if user['username'] != st.session_state.user]
            )
        
        with col2:
            action = st.selectbox(
                "选择操作",
                ["更改密码", "启用/禁用", "更改角色"]
            )
        
        if st.button("执行操作", use_container_width=True):
            if action == "更改密码":
                new_password = st.text_input("新密码", type="password")
                if new_password:
                    success, message = user_mgr.change_password(selected_user, new_password)
                    if success:
                        st.success(message)
                        send_wecom_message('action', st.session_state.user,
                            action="更改用户密码",
                            details=f"更改用户 {selected_user} 的密码"
                        )
                    else:
                        st.error(message)
            
            elif action == "启用/禁用":
                success, message = user_mgr.toggle_user_status(selected_user)
                if success:
                    st.success(message)
                    send_wecom_message('action', st.session_state.user,
                        action="更改用户状态",
                        details=f"更改用户 {selected_user} 的状态: {message}"
                    )
                else:
                    st.error(message)
            
            elif action == "更改角色":
                new_role = st.selectbox("新角色", ["user", "admin"])
                if st.button("确认更改角色"):
                    # 这里需要在 UserManager 中添加更改角色的方法
                    success, message = user_mgr.change_role(selected_user, new_role)
                    if success:
                        st.success(message)
                        send_wecom_message('action', st.session_state.user,
                            action="更改用户角色",
                            details=f"更改用户 {selected_user} 的角色为 {new_role}"
                        )
                    else:
                        st.error(message)
    else:
        st.info("暂无用户数据")

def show_admin_panel():
    """显示管理员面板"""
    st.title("管理员面板")
    
    # 使用选项卡组织不同功能
    tab1, tab2 = st.tabs(["用户管理", "数据分析"])
    
    with tab1:
        # 用户管理功能
        show_user_management()
    
    with tab2:
        # 用户分析功能
        show_user_analytics()

# 初始化会话状态
if 'show_add_user' not in st.session_state:
    st.session_state.show_add_user = False