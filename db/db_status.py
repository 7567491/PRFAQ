import streamlit as st
import sqlite3
from pathlib import Path
from user.logger import add_log
import pandas as pd

def get_table_schemas() -> dict:
    """获取所有表的CREATE TABLE语句"""
    try:
        conn = sqlite3.connect('db/users.db')
        cursor = conn.cursor()
        
        # 获取所有表的CREATE语句
        cursor.execute("""
            SELECT name, sql 
            FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        
        schemas = {}
        for table_name, create_sql in cursor.fetchall():
            if create_sql:  # 排除系统表
                schemas[table_name] = create_sql
                
        return schemas
        
    except Exception as e:
        add_log("error", f"获取表结构失败: {str(e)}")
        return {}
    finally:
        if 'conn' in locals():
            conn.close()

def show_db_status():
    """显示数据库状态"""
    st.markdown("### 数据库结构")
    
    try:
        # 获取表结构
        schemas = get_table_schemas()
        
        if not schemas:
            st.error("无法获取数据库表结构")
            return
            
        # 显示每个表的结构
        for table_name, create_sql in schemas.items():
            with st.expander(f"📋 {table_name}", expanded=True):
                st.code(create_sql, language="sql")
        
        # 显示数据库统计信息
        st.markdown("### 数据库统计")
        
        conn = sqlite3.connect('db/users.db')
        stats = []
        
        for table_name in schemas.keys():
            try:
                # 获取表的记录数
                count = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", conn).iloc[0]['count']
                
                # 获取表的大小（近似值）
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA page_count, page_size, table_info({table_name})")
                table_info = cursor.fetchall()
                
                stats.append({
                    "表名": table_name,
                    "记录数": count,
                    "字段数": len(table_info)
                })
            except Exception as e:
                add_log("error", f"获取表 {table_name} 统计信息失败: {str(e)}")
        
        if stats:
            st.dataframe(
                pd.DataFrame(stats),
                column_config={
                    "表名": st.column_config.TextColumn("表名", width="medium"),
                    "记录数": st.column_config.NumberColumn("记录数", width="small"),
                    "字段数": st.column_config.NumberColumn("字段数", width="small")
                },
                hide_index=True,
                use_container_width=True
            )
        
    except Exception as e:
        error_msg = f"显示数据库状态失败: {str(e)}"
        st.error(error_msg)
        add_log("error", error_msg) 