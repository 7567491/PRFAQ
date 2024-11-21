import streamlit as st
from datetime import datetime, timezone
import sqlite3
from user.logger import add_log
from user.user_process import UserManager

def register_marketplace_user(customer_id: str, aws_account: str, product_code: str, setup_info: dict) -> bool:
    """注册AWS Marketplace用户到数据库"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect("db/users.db")
        c = conn.cursor()
        
        try:
            conn.execute("BEGIN")
            
            # 1. 检查用户是否已存在
            c.execute('SELECT user_id FROM users WHERE user_id = ?', (customer_id,))
            if c.fetchone():
                conn.commit()
                return True
            
            # 2. 插入users表
            total_points = 200000 + setup_info.get('extra_points', 0)
            c.execute('''
                INSERT INTO users (
                    user_id, username, password, email, phone, org_name,
                    role, is_active, created_at, last_login, total_chars,
                    total_cost, daily_chars_limit, used_chars_today, points
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                customer_id, setup_info['username'], setup_info['password'],
                setup_info.get('email'), setup_info.get('phone'),
                setup_info['org_name'], 'marketplace_user', 1, now, now,
                0, 0.0, 200000, 0, total_points
            ))
            
            # 3. 插入aws_customers表
            c.execute('''
                INSERT INTO aws_customers (
                    user_id, customer_identifier, aws_account_id,
                    product_code, subscription_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, customer_id, aws_account, product_code, 1, now, now))
            
            # 4. 添加积分记录
            c.execute('''
                INSERT INTO point_transactions (
                    user_id, timestamp, type, amount, balance, description
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (customer_id, now, 'reward', total_points, total_points,
                  'AWS Marketplace新用户奖励'))
            
            conn.commit()
            add_log("info", f"Registered marketplace user: {customer_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except Exception as e:
        add_log("error", f"Error registering marketplace user: {str(e)}")
        return False

def show_marketplace_login():
    """显示AWS Marketplace登录页面"""
    st.title("AWS Marketplace 用户注册")
    
    # 从URL参数获取客户信息
    customer_id = st.query_params.get("customer_id")
    aws_account_id = st.query_params.get("aws_account_id")
    product_code = st.query_params.get("product_code")
    
    if not all([customer_id, aws_account_id, product_code]):
        st.error("无效的注册链接")
        return False
    
    # 显示AWS账户信息
    st.success("AWS Marketplace 验证成功！")
    with st.expander("AWS账户信息", expanded=True):
        st.markdown(f"""
            - **AWS Account ID**: {aws_account_id}
            - **Customer ID**: {customer_id}
            - **Product**: {product_code}
        """)

    # 检查用户是否已存在
    conn = sqlite3.connect("db/users.db")
    c = conn.cursor()
    c.execute('SELECT user_id FROM users WHERE user_id = ?', (customer_id,))
    user_exists = c.fetchone() is not None
    conn.close()

    if user_exists:
        st.success("您已是注册用户，正在跳转到主页面...")
        st.session_state.user = customer_id
        st.session_state.authenticated = True
        st.session_state.user_role = "marketplace_user"
        st.rerun()
        return True

    # 新用户注册表单
    with st.form("mp_user_setup"):
        st.markdown("### 🎉 欢迎使用！请完成以下信息设置")
        username = st.text_input("用户名 *", value=customer_id)
        password = st.text_input("密码 *", type="password")
        password_confirm = st.text_input("确认密码 *", type="password")
        
        st.markdown("### 可选信息（每项+10,000积分）")
        email = st.text_input("邮箱")
        phone = st.text_input("电话")
        org_name = st.text_input("工作单位")
        
        if st.form_submit_button("完成注册", use_container_width=True):
            if not password or password != password_confirm:
                st.error("密码输入有误")
                return False
            
            # 计算额外积分
            extra_points = sum(10000 for x in [email, phone, org_name] if x)
            
            # 注册用户
            if register_marketplace_user(
                customer_id, 
                aws_account_id, 
                product_code,
                {
                    'username': username,
                    'password': password,
                    'email': email,
                    'phone': phone,
                    'org_name': org_name or aws_account_id,
                    'extra_points': extra_points
                }
            ):
                st.success(f"注册成功！总计积分：{200000 + extra_points}点")
                st.session_state.user = username
                st.session_state.authenticated = True
                st.session_state.user_role = "marketplace_user"
                st.rerun()
                return True
            
            st.error("注册失败，请重试")
            return False

    return False