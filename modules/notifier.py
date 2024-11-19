import requests
from datetime import datetime
import platform
import socket

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