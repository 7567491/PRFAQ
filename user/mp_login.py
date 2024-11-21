import streamlit as st
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional
from user.logger import add_log
from user.user_process import UserManager
import sqlite3
import traceback

def load_marketplace_session(session_id: str) -> Optional[dict]:
    """加载AWS Marketplace会话信息"""
    try:
        session_file = Path("./config/mp_session.json")
        if not session_file.exists():
            return None
            
        with open(session_file, "r") as f:
            sessions = json.load(f)
            if session_id not in sessions:
                return None
                
            session = sessions[session_id]
            session_time = datetime.fromisoformat(session["timestamp"])
            current_time = datetime.now(timezone.utc)
            
            # 检查会话是否过期（5分钟）
            if (current_time - session_time).total_seconds() > 300:
                add_log("warning", f"Marketplace session {session_id} expired")
                return None
                
            return session
    except Exception as e:
        add_log("error", f"Error loading marketplace session: {str(e)}")
        return None

def register_marketplace_user(user_info: dict, setup_info: dict) -> bool:
    """注册AWS Marketplace用户到数据库"""
    try:
        customer_id = user_info["CustomerIdentifier"]
        aws_account = user_info["CustomerAWSAccountId"]
        product_code = user_info["ProductCode"]
        now = datetime.now(timezone.utc).isoformat()
        
        print(f"[DEBUG] 开始注册MP用户: {customer_id}")
        
        # 连接数据库
        conn = sqlite3.connect("db/users.db")
        c = conn.cursor()
        
        try:
            # 开始事务
            conn.execute("BEGIN")
            
            # 1. 检查用户是否已存在
            c.execute('SELECT user_id FROM users WHERE user_id = ?', (customer_id,))
            if c.fetchone():
                print(f"[DEBUG] MP用户已存在: {customer_id}")
                conn.commit()
                return True
            
            # 2. 插入users表
            total_points = 200000 + setup_info.get('extra_points', 0)
            user_data = (
                customer_id,          # user_id
                setup_info['username'],  # username
                setup_info['password'],  # password
                setup_info.get('email'),  # email
                setup_info.get('phone'),  # phone
                setup_info['org_name'],   # org_name
                'marketplace_user',   # role
                1,                    # is_active
                now,                  # created_at
                now,                  # last_login
                0,                    # total_chars
                0.0,                  # total_cost
                200000,              # daily_chars_limit
                0,                    # used_chars_today
                total_points         # points
            )
            
            c.execute('''
                INSERT INTO users (
                    user_id, username, password, email, phone, org_name,
                    role, is_active, created_at, last_login, total_chars,
                    total_cost, daily_chars_limit, used_chars_today, points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', user_data)
            
            # 3. 插入aws_customers表
            aws_customer_data = (
                customer_id,          # user_id
                customer_id,          # customer_identifier
                aws_account,          # aws_account_id
                product_code,         # product_code
                1,                    # subscription_status
                now,                  # created_at
                now                   # updated_at
            )
            
            c.execute('''
                INSERT INTO aws_customers (
                    user_id, customer_identifier, aws_account_id,
                    product_code, subscription_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', aws_customer_data)
            
            # 4. 添加积分交易记录
            # 4.1 基础积分
            c.execute('''
                INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance, description, operation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id, now, 'reward', 200000, 200000,
                'AWS Marketplace新用户奖励', None
            ))
            
            # 4.2 额外积分（如果有）
            if setup_info.get('extra_points', 0) > 0:
                desc = '完善信息奖励（' + '、'.join(setup_info['extra_points_desc']) + '）'
                c.execute('''
                    INSERT INTO point_transactions (
                        user_id, timestamp, type, amount, balance, description, operation_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    customer_id, now, 'reward', setup_info['extra_points'],
                    total_points, desc, None
                ))
            
            # 提交事务
            conn.commit()
            print(f"[DEBUG] 成功注册MP用户: {customer_id}")
            print(f"[DEBUG] 总积分: {total_points}")
            add_log("info", f"Registered new marketplace user: {customer_id} with {total_points} points")
            return True
            
        except Exception as e:
            # 回滚事务
            conn.rollback()
            raise e
            
        finally:
            conn.close()
            
    except Exception as e:
        print(f"[DEBUG] MP用户注册错误: {str(e)}")
        print(f"[DEBUG] 错误详情: {traceback.format_exc()}")
        add_log("error", f"Error registering marketplace user: {str(e)}")
        return False

def show_marketplace_login():
    """显示AWS Marketplace登录页面"""
    st.title("AWS Marketplace 用户登录")
    
    # 获取session_id
    session_id = st.query_params.get("session_id")
    if not session_id:
        st.error("无效的登录链接")
        st.markdown("""
            请通过 AWS Marketplace 访问本应用：
            1. 返回 AWS Marketplace 页面
            2. 点击 "Continue to Subscribe"
            3. 完成订阅后将自动登录
        """)
        return False
    
    # 加载会话信息
    session = load_marketplace_session(session_id)
    if not session:
        st.error("会话已过期或无效")
        st.markdown("""
            请重新通过 AWS Marketplace 访问本应用。
            如果问题持续存在，请联系支持团队。
        """)
        return False
    
    # 显示用户信息
    user_info = session["user_info"]
    st.success("AWS Marketplace 验证成功！")
    
    with st.expander("AWS账户信息", expanded=True):
        st.markdown(f"""
            - **AWS Account ID**: {user_info['CustomerAWSAccountId']}
            - **Customer ID**: {user_info['CustomerIdentifier']}
            - **Product**: {user_info['ProductCode']}
        """)

    # 检查用户是否已存在
    customer_id = user_info["CustomerIdentifier"]
    conn = sqlite3.connect("db/users.db")
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (customer_id,))
    user_exists = c.fetchone() is not None
    conn.close()

    if not user_exists:
        st.markdown("""
        ### 🎉 欢迎使用六页纸AI！
        
        作为 AWS Marketplace 新用户，您将获得：
        - 基础积分：200,000点
        - 每日字符限额：200,000字符
        - 专属技术支持
        
        请完成以下信息设置，每填写一项可选信息将额外获得10,000积分奖励！
        """)

        with st.form("mp_user_setup"):
            username = st.text_input("用户名 *", value=customer_id)
            password = st.text_input("密码 *", type="password")
            password_confirm = st.text_input("确认密码 *", type="password")
            
            # 可选信息
            st.markdown("### 可选信息（每项+10,000积分）")
            email = st.text_input("邮箱")
            phone = st.text_input("电话")
            org_name = st.text_input("工作单位")
            
            submitted = st.form_submit_button("完成注册", use_container_width=True)
            
            if submitted:
                if not password or not password_confirm:
                    st.error("请设置密码")
                    return False
                    
                if password != password_confirm:
                    st.error("两次输入的密码不一致")
                    return False
                
                # 计算额外积分
                extra_points = 0
                extra_points_desc = []
                if email:
                    extra_points += 10000
                    extra_points_desc.append("填写邮箱")
                if phone:
                    extra_points += 10000
                    extra_points_desc.append("填写电话")
                if org_name and org_name != user_info['CustomerAWSAccountId']:
                    extra_points += 10000
                    extra_points_desc.append("填写工作单位")
                
                # 注册用户
                if register_marketplace_user(user_info, {
                    'username': username,
                    'password': password,
                    'email': email,
                    'phone': phone,
                    'org_name': org_name or user_info['CustomerAWSAccountId'],
                    'extra_points': extra_points,
                    'extra_points_desc': extra_points_desc
                }):
                    st.success(f"""
                        🎉 注册成功！
                        
                        您获得了：
                        - 基础积分：200,000点
                        - 额外奖励：{extra_points}点
                        - 总计积分：{200000 + extra_points}点
                        
                        正在跳转到主页面...
                    """)
                    
                    # 设置登录状态
                    st.session_state.user = username
                    st.session_state.authenticated = True
                    st.session_state.user_role = "marketplace_user"
                    
                    st.rerun()
                    return True
                else:
                    st.error("注册失败，请重试或联系支持团队")
                    return False
    else:
        # 已注册用户直接登录
        st.success("您已是注册用户，正在跳转到主页面...")
        st.session_state.user = customer_id
        st.session_state.authenticated = True
        st.session_state.user_role = "marketplace_user"
        st.rerun()
        return True
    
    return False 
    # 登录按钮
    if st.button("进入应用", type="primary", use_container_width=True):
        if register_marketplace_user(user_info):
            # 设置登录状态
            st.session_state.user = user_info["CustomerIdentifier"]
            st.session_state.authenticated = True
            st.session_state.user_role = "marketplace_user"
            
            # 更新最后登录时间
            user_mgr = UserManager()
            user_mgr.update_last_login(user_info["CustomerIdentifier"])
            
            add_log("info", f"Marketplace user {user_info['CustomerIdentifier']} logged in")
            st.rerun()
            return True
        else:
            st.error("登录失败，请重试")
            return False
    
    return False 