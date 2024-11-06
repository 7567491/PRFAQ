import json
import sqlite3
from datetime import datetime
from pathlib import Path
import streamlit as st
from user.logger import add_log

def get_rose_user_id() -> str:
    """获取Rose的user_id"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    c.execute('SELECT user_id FROM users WHERE username = ?', ('Rose',))
    result = c.fetchone()
    conn.close()
    
    if not result:
        raise Exception("未找到用户 Rose")
    return result[0]

def calculate_usage_stats(user_id: str) -> dict:
    """计算用户的使用统计"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 获取账单统计
    c.execute('''
        SELECT SUM(input_letters + output_letters) as total_chars,
               SUM(total_cost) as total_cost
        FROM bills
        WHERE user_id = ?
    ''', (user_id,))
    
    result = c.fetchone()
    conn.close()
    
    return {
        'total_chars': result[0] or 0,
        'total_cost': result[1] or 0.0
    }

def migrate_bills() -> dict:
    """将历史账单数据迁移到数据库"""
    COST_PER_CHAR = 0.0001  # 每字符0.0001元人民币
    
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    try:
        # 获取Rose的user_id
        user_id = get_rose_user_id()
        results['details'].append(f"找到用户 Rose (ID: {user_id})")
        
        # 连接数据库
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        
        # 读取历史账单数据
        try:
            with open('config/letters.json', 'r', encoding='utf-8') as f:
                letters_data = json.load(f)
                results['details'].append("成功读取 letters.json 文件")
        except FileNotFoundError:
            results['message'] = "未找到历史账单数据文件"
            return results
        
        # 迁移账单记录前先检查重复
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for record in letters_data.get('records', []):
            try:
                # 检查是否已存在相同记录
                c.execute('''
                    SELECT COUNT(*) FROM bills 
                    WHERE user_id = ? AND timestamp = ? AND api_name = ? 
                    AND operation = ? AND input_letters = ? AND output_letters = ?
                ''', (
                    user_id,
                    record['timestamp'],
                    record.get('api_name', 'unknown'),
                    record.get('operation', 'unknown'),
                    record.get('input_letters', 0),
                    record.get('output_letters', 0)
                ))
                
                if c.fetchone()[0] == 0:  # 如果不存在重复记录
                    # 计算新的费用
                    total_chars = (record.get('input_letters', 0) + 
                                 record.get('output_letters', 0))
                    total_cost = total_chars * COST_PER_CHAR
                    
                    c.execute('''
                        INSERT INTO bills (
                            user_id, timestamp, api_name, operation,
                            input_letters, output_letters, total_cost
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        record['timestamp'],
                        record.get('api_name', 'unknown'),
                        record.get('operation', 'unknown'),
                        record.get('input_letters', 0),
                        record.get('output_letters', 0),
                        total_cost
                    ))
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as e:
                error_count += 1
                results['details'].append(f"记录迁移错误: {str(e)}")
        
        results['details'].append(f"账单记录迁移: {success_count} 成功, {skip_count} 跳过, {error_count} 失败")
        
        # 更新Rose的使用统计
        stats = calculate_usage_stats(user_id)
        c.execute('''
            UPDATE users 
            SET total_chars = ?,
                total_cost = ?
            WHERE user_id = ?
        ''', (
            stats['total_chars'],
            stats['total_cost'],
            user_id
        ))
        results['details'].append("更新用户使用统计成功")
        results['details'].append(f"总字符数: {stats['total_chars']:,}")
        results['details'].append(f"总消费: ¥{stats['total_cost']:.4f}")
        
        conn.commit()
        results['success'] = True
        results['message'] = "账单数据迁移完成"
        
    except Exception as e:
        results['message'] = f"迁移过程出错: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()
    
    return results

def migrate_history() -> dict:
    """将历史记录数据迁移到数据库"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    try:
        # 获取Rose的user_id
        user_id = get_rose_user_id()
        results['details'].append(f"找到用户 Rose (ID: {user_id})")
        
        # 连接数据库
        conn = sqlite3.connect('db/users.db')
        c = conn.cursor()
        
        # 读取历史记录数据
        success_count = 0
        skip_count = 0
        error_count = 0
        
        history_file = Path('config/prfaqs.json')
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                results['details'].append("成功读取 prfaqs.json 文件")
                
            # 迁移历史记录前先检查重复
            for record in history_data:
                try:
                    # 检查是否已存在相同记录
                    c.execute('''
                        SELECT COUNT(*) FROM history 
                        WHERE user_id = ? AND timestamp = ? AND content = ?
                    ''', (
                        user_id,
                        record['timestamp'],
                        record['content']
                    ))
                    
                    if c.fetchone()[0] == 0:  # 如果不存在重复记录
                        c.execute('''
                            INSERT INTO history (user_id, timestamp, content, type)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            user_id,
                            record['timestamp'],
                            record['content'],
                            record.get('type', 'unknown')
                        ))
                        success_count += 1
                    else:
                        skip_count += 1
                except Exception as e:
                    error_count += 1
                    results['details'].append(f"记录迁移错误: {str(e)}")
        
        results['details'].append(f"历史记录迁移: {success_count} 成功, {skip_count} 跳过, {error_count} 失败")
        
        conn.commit()
        results['success'] = True
        results['message'] = "历史记录迁移完成"
        
    except Exception as e:
        results['message'] = f"迁移过程出错: {str(e)}"
    finally:
        if 'conn' in locals():
            conn.close()
    
    return results

def show_migrate_interface():
    """显示数据迁移界面"""
    st.markdown("### 数据迁移")
    
    # 添加警告信息
    st.warning("⚠️ 数据迁移将把旧的JSON文件数据导入到数据库中，并按新的计费标准（每字符0.0001元）重新计算费用。建议在迁移前先备份数据库！")
    
    # 显示可迁移的文件
    files_to_migrate = []
    if Path('config/letters.json').exists():
        files_to_migrate.append('账单数据 (letters.json)')
    if Path('config/prfaqs.json').exists():
        files_to_migrate.append('历史记录 (prfaqs.json)')
    
    if not files_to_migrate:
        st.info("没有找到可迁移的文件")
        return
    
    st.write("发现以下可迁移的文件：")
    for file in files_to_migrate:
        st.text(f"• {file}")
    
    # 添加确认步骤
    confirm = st.checkbox("我已备份数据库，并了解迁移操作的风险")
    
    if confirm:
        if st.button("开始迁移", use_container_width=True):
            # 显示进度信息
            progress_text = st.empty()
            
            # 迁移账单数据
            if Path('config/letters.json').exists():
                progress_text.text("正在迁移账单数据...")
                bills_result = migrate_bills()
                st.markdown("#### 账单迁移结果")
                st.write(bills_result['message'])
                for detail in bills_result['details']:
                    st.text(detail)
                
                if bills_result['success']:
                    st.success("账单数据迁移成功")
                else:
                    st.error("账单数据迁移失败")
            
            # 迁移历史记录
            if Path('config/prfaqs.json').exists():
                progress_text.text("正在迁移历史记录...")
                history_result = migrate_history()
                st.markdown("#### 历史记录迁移结果")
                st.write(history_result['message'])
                for detail in history_result['details']:
                    st.text(detail)
                
                if history_result['success']:
                    st.success("历史记录迁移成功")
                else:
                    st.error("历史记录迁移失败")
            
            progress_text.text("迁移完成！")
            add_log("info", "完成数据迁移")