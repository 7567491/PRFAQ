import sqlite3
import streamlit as st
import pandas as pd
from pathlib import Path
from user.logger import add_log

def get_table_info():
    """获取数据库表的基本信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        # 扩展的表说明字典
        table_descriptions = {
            'users': '用户信息表',
            'bills': '账单记录表',
            'history': '历史记录表',
            'points': '积分记录表',
            'chat_history': '聊天历史表',
            'logs': '系统日志表',
            'aws_customers': 'AWS客户信息表',
            'aws_notifications': 'AWS通知记录表',
            'aws_subscriptions': 'AWS订阅信息表',
            'aws_usage': 'AWS使用记录表',
            'aws_billing': 'AWS计费记录表',
            'templates': '模板配置表',
            'settings': '系统设置表',
            'feedback': '用户反馈表'
        }
        
        # 时间字段映射
        time_fields = {
            'users': ['last_login', 'created_at', 'updated_at'],
            'bills': ['created_at'],
            'history': ['created_at'],
            'points': ['created_at'],
            'chat_history': ['timestamp'],
            'logs': ['timestamp'],
            'aws_customers': ['created_at', 'updated_at'],
            'aws_notifications': ['notification_time'],
            'aws_subscriptions': ['start_date', 'end_date'],
            'aws_usage': ['usage_date'],
            'aws_billing': ['billing_date'],
            'feedback': ['submit_time']
        }
        
        table_info = []
        for table in tables:
            table_name = table[0]
            try:
                # 使用参数化查询获取记录数
                cursor.execute("SELECT COUNT(*) FROM `" + table_name + "`")
                count = cursor.fetchone()[0]
                
                # 获取表的结构信息
                cursor.execute(f"PRAGMA table_info(`{table_name}`)")
                columns = cursor.fetchall()
                column_count = len(columns)
                
                # 获取最后更新时间
                last_update = '无记录'
                if table_name in time_fields:
                    column_names = [col[1] for col in columns]
                    existing_time_fields = [
                        field for field in time_fields[table_name]
                        if field in column_names
                    ]
                    
                    if existing_time_fields:
                        # 使用简单的MAX查询获取最新时间
                        time_field = existing_time_fields[0]  # 只使用第一个有效的时间字段
                        cursor.execute(
                            f"SELECT MAX(`{time_field}`) FROM `{table_name}`"
                        )
                        result = cursor.fetchone()[0]
                        if result:
                            last_update = result
                
                table_info.append({
                    '表名': table_name,
                    '说明': table_descriptions.get(table_name, '未知表'),
                    '记录数': count,
                    '字段数': column_count,
                    '最后更新': last_update
                })
                
            except sqlite3.Error as e:
                # 只记录关键错误信息
                add_log("error", f"表 {table_name} 查询失败: {str(e)}")
                table_info.append({
                    '表名': table_name,
                    '说明': table_descriptions.get(table_name, '未知表'),
                    '记录数': 0,
                    '字段数': 0,
                    '最后更新': '查询错误'
                })
        
        return pd.DataFrame(table_info)
    except sqlite3.Error as e:
        add_log("error", f"数据库连接失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def get_index_info():
    """获取数据库索引的基本信息"""
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 获取所有索引
        cursor.execute("""
            SELECT name, tbl_name 
            FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        indexes = cursor.fetchall()
        
        index_info = []
        for index in indexes:
            index_name, table_name = index
            
            # 获取索引的记录数（通过关联表的记录数）
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # 获取索引的中文解释（可以根据实际情况扩展）
            description = {
                'idx_users_username': '用户名索引',
                'idx_bills_user_id': '账单用户ID索引',
                'idx_history_user_id': '历史记录用户ID索引',
                'idx_points_user_id': '积分用户ID索引',
                'idx_chat_history_user_id': '聊天历史用户ID索引',
                'idx_logs_timestamp': '日志时间戳索引'
            }.get(index_name, '未知索引')
            
            index_info.append({
                '索引名': index_name,
                '所属表': table_name,
                '说明': description,
                '记录数': count
            })
        
        return pd.DataFrame(index_info)
    except Exception as e:
        add_log("error", f"获取索引信息失败: {str(e)}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

def show_db_overview():
    """显示数据库概览界面"""
    st.markdown("### 数据库概览")
    
    # 显示表信息
    st.markdown("#### 数据表信息")
    table_info = get_table_info()
    if table_info is not None and not table_info.empty:
        st.dataframe(table_info, use_container_width=True)
    else:
        st.error("无法获取数据表信息")
    
    # 显示索引信息
    st.markdown("#### 索引信息")
    index_info = get_index_info()
    if index_info is not None and not index_info.empty:
        st.dataframe(index_info, use_container_width=True)
    else:
        st.warning("数据库中没有自定义索引") 