import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

def load_config():
    """Load configuration with environment variable override support"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    
    # Override API keys with environment variables if available
    for api_name in config["api_keys"]:
        env_key = f"{api_name.upper()}_API_KEY"
        if env_key in os.environ:
            config["api_keys"][api_name] = os.environ[env_key]
            
    return config

def load_templates():
    """Load UI templates"""
    template_path = Path(__file__).parent.parent / "templates.json"
    with open(template_path, encoding='utf-8') as f:
        return json.load(f)

def load_prompts():
    """Load prompts from prompt.json"""
    try:
        with open('prompt.json', 'r', encoding='utf-8') as f:
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
    """Load generation history"""
    history_path = Path(__file__).parent.parent / "prfaqs.json"
    if not history_path.exists():
        return []
    with open(history_path, encoding='utf-8') as f:
        return json.load(f)

def save_history(item):
    """Save generation result to history"""
    history_path = Path(__file__).parent.parent / "prfaqs.json"
    history = load_history()
    
    # Add timestamp to item
    item['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add to history
    history.append(item)
    
    # Keep only latest 100 items
    if len(history) > 100:
        history = history[-100:]
    
    # Save to file
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_letters_record(input_letters: int, output_letters: int, api_name: str, operation: str) -> bool:
    """Add a new letters record"""
    try:
        # 计算费用 (每1000字符)
        input_cost_usd = (input_letters / 1000) * 0.001  # $0.001 per 1K chars
        output_cost_usd = (output_letters / 1000) * 0.002  # $0.002 per 1K chars
        total_cost_usd = input_cost_usd + output_cost_usd
        
        input_cost_rmb = input_cost_usd * 7.2  # 汇率转换
        output_cost_rmb = output_cost_usd * 7.2
        total_cost_rmb = total_cost_usd * 7.2
        
        # 读取当前记录
        letters_path = Path(__file__).parent.parent / "letters.json"
        if not letters_path.exists():
            letters_data = {
                "total": {
                    "input_letters": 0,
                    "output_letters": 0,
                    "cost_usd": 0.0,
                    "cost_rmb": 0.0
                },
                "records": []
            }
        else:
            try:
                with open(letters_path, encoding='utf-8') as f:
                    letters_data = json.load(f)
            except Exception as e:
                return False
        
        # 更新总计
        letters_data["total"]["input_letters"] += input_letters
        letters_data["total"]["output_letters"] += output_letters
        letters_data["total"]["cost_usd"] = float(letters_data["total"]["cost_usd"]) + total_cost_usd
        letters_data["total"]["cost_rmb"] = float(letters_data["total"]["cost_rmb"]) + total_cost_rmb
        
        # 添加新记录
        record = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "api_name": api_name,
            "operation": operation,
            "input_letters": input_letters,
            "output_letters": output_letters,
            "input_cost_usd": input_cost_usd,
            "output_cost_usd": output_cost_usd,
            "total_cost_usd": total_cost_usd,
            "input_cost_rmb": input_cost_rmb,
            "output_cost_rmb": output_cost_rmb,
            "total_cost_rmb": total_cost_rmb
        }
        letters_data["records"].append(record)
        
        # 保存更新后的记录
        try:
            with open(letters_path, 'w', encoding='utf-8') as f:
                json.dump(letters_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
            
    except Exception as e:
        return False

def load_letters():
    """Load letters statistics"""
    letters_path = Path(__file__).parent.parent / "letters.json"
    if not letters_path.exists():
        initial_letters = {
            "total": {
                "input_letters": 0,
                "output_letters": 0,
                "cost_usd": 0.0,
                "cost_rmb": 0.0
            },
            "records": []
        }
        with open(letters_path, 'w', encoding='utf-8') as f:
            json.dump(initial_letters, f, ensure_ascii=False, indent=2)
        return initial_letters
    
    try:
        with open(letters_path, encoding='utf-8') as f:
            letters_data = json.load(f)
            return letters_data
    except Exception as e:
        return {
            "total": {
                "input_letters": 0,
                "output_letters": 0,
                "cost_usd": 0.0,
                "cost_rmb": 0.0
            },
            "records": []
        }

def add_log(level: str, message: str):
    """Add a log entry to session state"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    log_entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    }
    
    st.session_state.logs.append(log_entry)
    
    # Keep only latest 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]