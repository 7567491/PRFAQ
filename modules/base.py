"""
基础模块，包含核心功能和共享组件
用于避免循环依赖并提供基础服务
"""

import streamlit as st
import sqlite3
from datetime import datetime
from pathlib import Path
import json
import traceback
from typing import Optional, Dict, Any, List, Union
from .logger import add_log

class BaseManager:
    """基础管理器类，提供数据库连接和基本操作"""
    
    def __init__(self):
        self.db_path = 'db/users.db'
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[tuple]]:
        """执行数据库查询"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            conn.commit()
            return result
        except Exception as e:
            add_log("error", f"数据库查询失败: {str(e)}", include_trace=True)
            return None
        finally:
            if 'conn' in locals():
                conn.close()

class ConfigManager:
    """配置管理器，处理所有配置文件的加载"""
    
    @staticmethod
    def load_config() -> Optional[Dict[str, Any]]:
        """加载主配置文件"""
        try:
            config_path = Path("config/config.json")
            with open(config_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            add_log("error", f"加载配置文件失败: {str(e)}", include_trace=True)
            return None

    @staticmethod
    def load_templates() -> Optional[Dict[str, Any]]:
        """加载模板配置"""
        try:
            template_path = Path("config/templates.json")
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            add_log("error", f"加载模板文件失败: {str(e)}", include_trace=True)
            return None

    @staticmethod
    def load_prompts() -> Dict[str, Any]:
        """加载提示词配置"""
        try:
            with open('config/prompt.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            add_log("error", "未找到 prompt.json 配置文件")
            return {}
        except json.JSONDecodeError:
            add_log("error", "prompt.json 格式错误")
            return {}
        except Exception as e:
            add_log("error", f"加载提示词配置时发生错误: {str(e)}", include_trace=True)
            return {}

class HistoryManager(BaseManager):
    """历史记录管理器"""
    
    def load_history(self, user_id: str) -> List[Dict[str, Any]]:
        """加载用户历史记录"""
        try:
            records = self.execute_query(
                "SELECT user_id, timestamp, type, content FROM history WHERE user_id = ? ORDER BY timestamp DESC",
                (user_id,)
            )
            
            if not records:
                return []
                
            formatted_records = []
            for record in records:
                try:
                    content = json.loads(record[3]) if record[3] else {}
                    history_item = {
                        'user_id': record[0],
                        'timestamp': record[1],
                        'type': record[2],
                        'input': content.get('input', ''),
                        'output': content.get('output', ''),
                        'test_results': content.get('test_results', None)
                    }
                    formatted_records.append(history_item)
                except Exception as e:
                    add_log("error", f"解析历史记录失败: {str(e)}", include_trace=True)
                    continue
                    
            return formatted_records
            
        except Exception as e:
            add_log("error", f"加载历史记录失败: {str(e)}", include_trace=True)
            return []

    def save_history(self, data: Union[Dict[str, Any], str], history_type: str = "unknown") -> bool:
        """保存历史记录"""
        try:
            if isinstance(data, str):
                content = json.dumps({'output': data}, ensure_ascii=False)
            elif isinstance(data, dict):
                if 'content' in data:
                    content = data['content']
                else:
                    content = json.dumps({
                        'input': data.get('input_text', ''),
                        'output': data.get('output_text', ''),
                        'test_results': data.get('test_results', None)
                    }, ensure_ascii=False)
            else:
                raise ValueError(f"无效的数据类型: {type(data)}")

            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_id = data.get('user_id', st.session_state.get('user'))

            self.execute_query(
                "INSERT INTO history (user_id, timestamp, type, content) VALUES (?, ?, ?, ?)",
                (user_id, timestamp, history_type, content)
            )
            return True
            
        except Exception as e:
            add_log("error", f"保存历史记录失败: {str(e)}", include_trace=True)
            return False

def get_user_manager():
    """延迟导入并获取用户管理器实例"""
    from user.user_process import UserManager
    return UserManager()

def get_bill_manager():
    """延迟导入并获取账单管理器实例"""
    from bill.bill import BillManager
    return BillManager()

def update_sidebar_points():
    """更新侧边栏积分显示"""
    try:
        if 'user' in st.session_state and st.session_state.user:
            user_mgr = get_user_manager()
            bill_mgr = get_bill_manager()
            user_info = user_mgr.get_user_info(st.session_state.user)
            if user_info:
                st.session_state.sidebar_points = bill_mgr.get_user_points(user_info['user_id'])
    except Exception as e:
        add_log("error", f"更新侧边栏积分显示失败: {str(e)}", include_trace=True) 