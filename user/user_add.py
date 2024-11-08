import streamlit as st
import uuid
from datetime import datetime
from user.user_base import UserManager
from user.logger import add_log
from bill.bill_base import BillManager

class UserRegistration:
    def __init__(self):
        self.user_mgr = UserManager()
        self.bill_mgr = BillManager()
        self.INITIAL_POINTS = 10000  # 新用户初始积分
        self.DAILY_LOGIN_POINTS = 2000  # 每日登录奖励积分
        self.COMPLETE_INFO_POINTS = 5000  # 完整信息奖励积分
    
    def create_user(self, username: str, password: str, email: str = None, 
                   phone: str = None, org_name: str = None) -> bool:
        """创建新用户"""
        try:
            conn = self.user_mgr.get_db_connection()
            c = conn.cursor()
            
            # 检查用户名是否已存在
            c.execute('SELECT username FROM users WHERE username = ?', (username,))
            if c.fetchone():
                raise ValueError("用户名已存在")
            
            # 生成用户ID
            user_id = str(uuid.uuid4())
            
            # 密码加密
            hashed_password = self.user_mgr.hash_password(password)
            
            # 计算初始积分
            has_complete_info = all([email, phone, org_name])
            
            # 插入新用户记录，初始积分设为0
            c.execute('''
                INSERT INTO users (
                    user_id, username, password, email, phone, org_name,
                    role, is_active, created_at, points, daily_chars_limit,
                    used_chars_today, total_chars, total_cost
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, username, hashed_password, email, phone, org_name,
                'user', 1, datetime.now().isoformat(), 0,  # 初始积分设为0
                100000, 0, 0, 0.0
            ))
            
            conn.commit()
            
            # 添加新用户奖励积分
            self.bill_mgr.add_points(
                user_id=user_id,
                amount=self.INITIAL_POINTS,
                type='reward',
                description='新用户注册奖励'
            )
            
            # 如果提供了完整信息，添加额外奖励
            if has_complete_info:
                self.bill_mgr.add_points(
                    user_id=user_id,
                    amount=self.COMPLETE_INFO_POINTS,
                    type='reward',
                    description='完整信息奖励'
                )
            
            add_log("info", f"新用户 {username} 创建成功")
            return True
            
        except Exception as e:
            add_log("error", f"创建用户失败: {str(e)}")
            return False
        finally:
            conn.close()
    
    def award_daily_login(self, user_id: str, username: str):
        """发放每日登录奖励"""
        try:
            conn = self.user_mgr.get_db_connection()
            c = conn.cursor()
            
            # 检查今天是否已经领取过奖励
            today = datetime.now().date()
            c.execute('''
                SELECT timestamp FROM point_transactions 
                WHERE user_id = ? AND type = 'daily_login' 
                AND date(timestamp) = date(?)
            ''', (user_id, today.isoformat()))
            
            if not c.fetchone():  # 今天还没有领取奖励
                # 发放登录奖励
                success = self.bill_mgr.add_points(
                    user_id=user_id,
                    amount=self.DAILY_LOGIN_POINTS,
                    type='daily_login',
                    description='每日登录奖励'
                )
                
                if success:
                    add_log("info", f"用户 {username} 获得每日登录奖励 {self.DAILY_LOGIN_POINTS} 积分")
                    return True
            
            return False
            
        except Exception as e:
            add_log("error", f"发放每日登录奖励失败: {str(e)}")
            return False
        finally:
            conn.close()

def show_registration_form():
    """显示用户注册表单"""
    st.title("新用户注册")
    
    # 显示积分规则
    st.info("""
    ### 🎁 积分规则说明
    1. 新用户注册即可获得 10,000 积分
    2. 填写完整信息（邮箱、电话、组织）可额外获得 5,000 积分
    3. 每日首次登录可获得 2,000 积分
    4. 积分可用于生成内容，1字符=1积分
    """)
    
    registration = UserRegistration()
    
    with st.form("registration_form"):
        # 必填项标记星号
        username = st.text_input("用户名 *", placeholder="请输入用户名")
        password = st.text_input("密码 *", type="password", placeholder="请输入密码")
        password_confirm = st.text_input("确认密码 *", type="password", placeholder="请再次输入密码")
        
        # 可选项（完整信息奖励）
        st.markdown("#### 完善以下信息可额外获得 5,000 积分")
        email = st.text_input("邮箱", placeholder="请输入邮箱")
        phone = st.text_input("电话", placeholder="请输入电话")
        org_name = st.text_input("组织名称", placeholder="请输入组织名称")
        
        # 添加一个隐藏的返回登录选项
        return_to_login = st.form_submit_button("注册并返回登录")
        
        if return_to_login:
            if not username or not password:
                st.error("用户名和密码为必填项")
                return
            
            if password != password_confirm:
                st.error("两次输入的密码不一致")
                return
            
            if len(password) < 6:
                st.error("密码长度不能少于6位")
                return
            
            try:
                if registration.create_user(
                    username=username,
                    password=password,
                    email=email if email else None,
                    phone=phone if phone else None,
                    org_name=org_name if org_name else None
                ):
                    # 计算实际获得的积分
                    total_points = registration.INITIAL_POINTS
                    points_detail = [f"- 新用户奖励：{registration.INITIAL_POINTS:,} 积分"]
                    
                    if all([email, phone, org_name]):
                        total_points += registration.COMPLETE_INFO_POINTS
                        points_detail.append(f"- 完整信息奖励：{registration.COMPLETE_INFO_POINTS:,} 积分")
                    
                    success_message = f"""
                    ### ✅ 注册成功！
                    
                    您获得的奖励：
                    {chr(10).join(points_detail)}
                    
                    总计：{total_points:,} 积分
                    
                    每日登录还可获得 {registration.DAILY_LOGIN_POINTS:,} 积分奖励
                    """
                    
                    st.success(success_message)
                    
                    # 保存注册信息到session state用于自动登录
                    st.session_state.show_registration = False
                    st.session_state.new_registered_user = {
                        'username': username,
                        'password': password
                    }
                    st.rerun()
                else:
                    st.error("注册失败，请稍后重试")
            except ValueError as e:
                st.error(str(e)) 