import streamlit as st
import sqlite3
from datetime import datetime
from user.user_process import UserManager
from user.logger import add_log
import json
import traceback

def show_user_history():
    """显示用户历史记录"""
    try:
        print("\n=== 开始加载用户历史记录 ===")
        
        # 连接数据库
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        try:
            # 获取当前用户的历史记录
            cursor.execute('''
                SELECT history_id, user_id, timestamp, type, content
                FROM history
                WHERE user_id = ?
                ORDER BY timestamp DESC
            ''', (st.session_state.user,))
            
            records = cursor.fetchall()
            print(f"\n=== 查询到 {len(records)} 条历史记录 ===")
            
            if not records:
                st.info("暂无历史记录")
                return
            
            # 显示历史记录
            for record in records:
                try:
                    history_id, user_id, timestamp, record_type, content = record
                    
                    # 解析content字段
                    try:
                        content_data = json.loads(content)
                        print(f"解析content成功: {json.dumps(content_data, ensure_ascii=False, indent=2)}")
                    except json.JSONDecodeError as e:
                        print(f"解析content失败: {str(e)}")
                        content_data = {'input': '', 'output': content}
                    
                    # 构建显示标题
                    title = f"[{timestamp}] {record_type}"
                    if isinstance(content_data, dict):
                        preview = content_data.get('input', '')[:50] or content_data.get('output', '')[:50]
                        if preview:
                            title += f" - {preview}..."
                    
                    # 使用expander显示详细内容
                    with st.expander(title):
                        st.write(f"**记录ID**: {history_id}")
                        st.write(f"**类型**: {record_type}")
                        st.write(f"**时间**: {timestamp}")
                        
                        # 根据记录类型显示不同的内容
                        if record_type == 'career_test':
                            # 显示职业测评结果
                            if isinstance(content_data, dict):
                                if 'test_results' in content_data:
                                    try:
                                        test_results = json.loads(content_data['test_results'])
                                        st.write("**测评结果**:")
                                        st.json(test_results)
                                    except Exception as e:
                                        print(f"解析测评结果失败: {str(e)}")
                                st.write("**输出内容**:")
                                st.markdown(content_data.get('output', ''))
                        else:
                            # 显示其他类型的记录
                            if isinstance(content_data, dict):
                                if content_data.get('input'):
                                    st.write("**输入内容**:")
                                    st.text(content_data['input'])
                                if content_data.get('output'):
                                    st.write("**输出内容**:")
                                    st.markdown(content_data['output'])
                            else:
                                st.write("**内容**:")
                                st.markdown(str(content_data))
                        
                except Exception as e:
                    error_msg = (
                        f"\n=== 显示记录失败 ===\n"
                        f"错误类型: {type(e).__name__}\n"
                        f"错误信息: {str(e)}\n"
                        f"记录内容: {record}\n"
                        f"错误位置: {traceback.format_exc()}"
                    )
                    print(error_msg)
                    st.error(f"显示记录时发生错误: {str(e)}")
                    continue
            
            print("=== 历史记录显示完成 ===")
            
        except sqlite3.Error as e:
            error_msg = (
                f"\n=== 数据库查询错误 ===\n"
                f"错误信息: {str(e)}\n"
                f"错误位置: {traceback.format_exc()}"
            )
            print(error_msg)
            st.error(f"加载历史记录失败: {str(e)}")
            
    except Exception as e:
        error_msg = (
            f"\n=== 显示历史记录失败 ===\n"
            f"错误类型: {type(e).__name__}\n"
            f"错误信息: {str(e)}\n"
            f"错误位置: {traceback.format_exc()}"
        )
        print(error_msg)
        st.error(f"显示历史记录失败: {str(e)}")
        
    finally:
        if 'conn' in locals():
            conn.close()
            print("\n=== 数据库连接已关闭 ===")