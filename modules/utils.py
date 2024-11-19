import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
import sqlite3
from bill.bill import BillManager
from user.user_process import UserManager
from user.logger import add_log, display_logs
import traceback
import requests
import platform
import socket

def load_config():
    """Load configuration from config.json"""
    config_path = Path("config/config.json")
    with open(config_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_templates():
    """Load UI templates"""
    template_path = Path("config/templates.json")
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompts():
    """Load prompts from prompt.json"""
    try:
        with open('config/prompt.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("未找到 prompt.json 配置文件")
        return {}
    except json.JSONDecodeError:
        st.error("prompt.json 格式错误")
        return {}
    except Exception as e:
        st.error(f"加载提示词配置时发生错误: {str(e)}")
        return {}

def load_history():
    """从数据库加载历史记录"""
    try:
        print("\n=== 开始加载历史记录 ===")
        
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(history)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"当前表结构: {columns}")
        
        try:
            # 获取当前用户的历史记录
            cursor.execute('''
                SELECT user_id, timestamp, type, content
                FROM history
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (st.session_state.user,))
            
            records = cursor.fetchall()
            print(f"\n=== 查询到 {len(records)} 条历史记录 ===")
            
            formatted_records = []
            for record in records:
                try:
                    # 解析content字段
                    content = json.loads(record[3]) if record[3] else {}
                    
                    # 构建历史记录项
                    history_item = {
                        'user_id': record[0],
                        'timestamp': record[1],
                        'type': record[2],
                        'input': content.get('input', ''),
                        'output': content.get('output', ''),
                        'test_results': content.get('test_results', None)
                    }
                    
                    formatted_records.append(history_item)
                    
                except json.JSONDecodeError as e:
                    print(f"解析记录内容失败: {str(e)}")
                    print(f"问题记录: {record}")
                    continue
                    
                except Exception as e:
                    print(f"处理记录时发生错误: {str(e)}")
                    print(f"问题记录: {record}")
                    continue
            
            print("\n=== 历史记录加载成功 ===")
            print(f"格式化后的记录: {json.dumps(formatted_records, ensure_ascii=False, indent=2)}")
            
            return formatted_records
            
        except sqlite3.Error as e:
            error_msg = (
                f"\n=== 数据库查询错误 ===\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}"
            )
            print(error_msg)
            return []
            
    except Exception as e:
        error_msg = (
            f"\n=== 加载历史记录失败 ===\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"错误位置: {traceback.format_exc()}"
        )
        print(error_msg)
        return []
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n=== 数据库连接已关闭 ===")

def save_history(*args, **kwargs):
    """保存历史记录到数据库
    支持多种调用方式：
    1. save_history(history_data) - history_data 包含所有必要字段
    2. save_history(history_data, content=content) - 直接传入content
    3. save_history({'type': type, 'input_text': input, 'output_text': output}) - PR方式
    4. save_history(content=content) - 只传入content的方式
    """
    try:
        print("\n=== 开始保存历史记录 ===")
        print(f"接收到的参数: {args}")
        print(f"接收到的关键字参数: {json.dumps(kwargs, ensure_ascii=False, indent=2)}")
        
        # 验证和准备数据
        try:
            # 处理只传入content的情况
            if not args and 'content' in kwargs:
                content = kwargs['content']
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False)
                final_data = {
                    'user_id': st.session_state.user,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': kwargs.get('type', 'unknown'),
                    'content': content
                }
            # 处理PR方式的调用
            elif args and all(key in args[0] for key in ['type', 'input_text', 'output_text']):
                history_data = args[0]
                content = {
                    'input': history_data['input_text'],
                    'output': history_data['output_text']
                }
                final_data = {
                    'user_id': history_data.get('user_id', st.session_state.user),
                    'timestamp': history_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'type': history_data['type'],
                    'content': json.dumps(content, ensure_ascii=False)
                }
            # 处理完整history_data的情况
            elif args:
                history_data = args[0]
                if 'content' in history_data and isinstance(history_data['content'], str):
                    content = history_data['content']
                else:
                    content = {
                        'input': history_data.get('input_text', ''),
                        'output': history_data.get('output_text', ''),
                        'test_results': history_data.get('test_results', None)
                    }
                    content = json.dumps(content, ensure_ascii=False)
                
                final_data = {
                    'user_id': history_data.get('user_id', st.session_state.user),
                    'timestamp': history_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'type': history_data.get('type', 'unknown'),
                    'content': content
                }
            else:
                raise ValueError("无效的调用方式：缺少必要参数")
            
            # 验证必要字段
            for field in ['user_id', 'timestamp', 'type', 'content']:
                if not final_data.get(field):
                    error_msg = f"缺少必要字段: {field}"
                    print(error_msg)
                    raise ValueError(error_msg)
                    
            print("\n=== 最终数据 ===")
            print(json.dumps(final_data, ensure_ascii=False, indent=2))
            
        except Exception as e:
            error_msg = (
                f"\n=== 数据准备失败 ===\n"
                f"错误类型: {type(e).__name__}\n"
                f"错误信息: {str(e)}\n"
                f"原始参数: {args}\n"
                f"关键字参数: {json.dumps(kwargs, ensure_ascii=False)}"
            )
            print(error_msg)
            raise
        
        # 连接数据库
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        try:
            # 插入数据
            cursor.execute('''
                INSERT INTO history 
                (user_id, timestamp, type, content)
                VALUES (?, ?, ?, ?)
            ''', (
                final_data['user_id'],
                final_data['timestamp'],
                final_data['type'],
                final_data['content']
            ))
            
            # 提交事务
            conn.commit()
            print("\n=== 历史记录保存成功 ===")
            return True
            
        except sqlite3.Error as e:
            error_msg = (
                f"\n=== 数据库错误 ===\n"
                f"错误信息: {str(e)}\n"
                f"最终数据: {json.dumps(final_data, ensure_ascii=False)}"
            )
            print(error_msg)
            raise
            
    except Exception as e:
        error_msg = (
            f"\n=== 保存历史记录失败 ===\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"错误位置: {traceback.format_exc()}\n"
            f"原始参数: {args}\n"
            f"关键字参数: {json.dumps(kwargs, ensure_ascii=False)}"
        )
        print(error_msg)
        st.error(f"保存历史记录失败: {str(e)}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n=== 数据库连接已关闭 ===")

def add_letters_record(input_letters: int, output_letters: int, api_name: str, operation: str) -> bool:
    """Add a new letters record"""
    try:
        # 获取当前用户ID
        user_mgr = UserManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        if not user_info:
            return False
        
        # 检查用户是否达到每日限制
        if not user_mgr.check_daily_limit(st.session_state.user):
            st.error("已达到每日字符用限制")
            return False
        
        # 检查积分是否足够
        points_needed = input_letters + output_letters
        bill_mgr = BillManager()
        current_points = bill_mgr.get_user_points(user_info['user_id'])
        
        if current_points < points_needed:
            st.error(f"积分不足，需要 {points_needed} 积分，当前剩余 {current_points} 积分")
            return False
        
        # 添加账单记录
        success = bill_mgr.add_bill_record(
            user_id=user_info['user_id'],
            api_name=api_name,
            operation=operation,
            input_letters=input_letters,
            output_letters=output_letters
        )
        
        if not success:
            st.error("记录使用量失败")
            return False
        
        # 在侧边栏更新积分显示
        if 'sidebar_points' in st.session_state:
            st.session_state.sidebar_points = bill_mgr.get_user_points(user_info['user_id'])
        
        return True
            
    except Exception as e:
        st.error(f"记录使用量时出错: {str(e)}")
        return False

def load_letters():
    """从数据库加载账单数据"""
    bill_mgr = BillManager()
    return bill_mgr.get_all_bills()

def update_sidebar_points():
    """更新侧边栏积分显示"""
    if 'user' in st.session_state and st.session_state.user:
        user_mgr = UserManager()
        bill_mgr = BillManager()
        user_info = user_mgr.get_user_info(st.session_state.user)
        if user_info:
            st.session_state.sidebar_points = bill_mgr.get_user_points(user_info['user_id'])

def load_config():
    """加载配置文件"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        return None

def get_client_ip():
    """获取客户端IP"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip
    except:
        return "未知IP"

def get_client_os():
    """获取客户端操作系统信息"""
    try:
        return f"{platform.system()} {platform.release()}"
    except:
        return "未知系统"

def send_wecom_message(message_type, username, **kwargs):
    """统一的企业微信消息发送函数
    
    Args:
        message_type: 消息类型 ('login' 或 'action')
        username: 用户名
        **kwargs: 额外参数，可包含：
            - ip: 用户IP
            - os: 操作系统
            - action: 用户动作
            - details: 动作详情
    """
    try:
        # 获取企业微信配置
        webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=519108aa-7f3f-4f09-b54e-682adc52240d"
        
        if message_type == 'login':
            message = (
                f"用户登录通知\n"
                f"用户：{username}\n"
                f"IP：{kwargs.get('ip', '未知')}\n"
                f"系统：{kwargs.get('os', '未知')}\n"
                f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:  # action
            message = (
                f"用户操作通知\n"
                f"用户：{username}\n"
                f"动作：{kwargs.get('action', '未知')}\n"
                f"详情：{kwargs.get('details', '无')}\n"
                f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # 发送消息到企业微信
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()
        
    except Exception as e:
        print(f"发送企业微信消息失败: {str(e)}")
