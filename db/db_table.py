import sqlite3
import streamlit as st
import pandas as pd
from typing import Dict, List, Any

def get_all_tables() -> List[str]:
    """获取所有表名"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table'
        ORDER BY name
    """)
    
    tables = [row[0] for row in c.fetchall()]
    conn.close()
    
    return tables

def get_table_schema(table_name: str) -> str:
    """获取表的创建SQL"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    c.execute(f"""
        SELECT sql 
        FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    
    schema = c.fetchone()[0]
    conn.close()
    
    return schema

def get_table_info(table_name: str) -> List[Dict[str, Any]]:
    """获取表的详细信息"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    c.execute(f"PRAGMA table_info({table_name})")
    
    columns = []
    for row in c.fetchall():
        columns.append({
            'cid': row[0],
            'name': row[1],
            'type': row[2],
            'notnull': bool(row[3]),
            'default': row[4],
            'pk': bool(row[5])
        })
    
    conn.close()
    return columns

def get_table_stats(table_name: str) -> Dict[str, Any]:
    """获取表的统计信息"""
    conn = sqlite3.connect('db/users.db')
    c = conn.cursor()
    
    # 获取记录数
    c.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = c.fetchone()[0]
    
    # 获取表大小（近似值）
    c.execute(f"PRAGMA page_count")
    page_count = c.fetchone()[0]
    c.execute(f"PRAGMA page_size")
    page_size = c.fetchone()[0]
    size = page_count * page_size
    
    conn.close()
    
    return {
        'record_count': count,
        'size_bytes': size,
        'size_kb': size / 1024,
        'size_mb': size / (1024 * 1024)
    }

def show_table_info():
    """显示表信息界面"""
    st.markdown("### 数据库表结构")
    
    try:
        # 获取所有表
        tables = get_all_tables()
        
        if not tables:
            st.warning("数据库中没有找到任何表")
            return
        
        # 显示表数量
        st.info(f"数据库中共有 {len(tables)} 个表")
        
        # 为每个表创��一个展开区域
        for table_name in tables:
            with st.expander(f"表: {table_name}"):
                # 创建三个标签页
                tab1, tab2, tab3 = st.tabs(["表结构", "统计信息", "示例数据"])
                
                with tab1:
                    # 显示表结构
                    st.markdown("#### 创建语句")
                    st.code(get_table_schema(table_name), language='sql')
                    
                    st.markdown("#### 列信息")
                    columns = get_table_info(table_name)
                    df_columns = pd.DataFrame(columns)
                    df_columns['notnull'] = df_columns['notnull'].map({True: '是', False: '否'})
                    df_columns['pk'] = df_columns['pk'].map({True: '是', False: '否'})
                    df_columns.columns = ['序号', '列名', '类型', '非空', '默认值', '主键']
                    st.dataframe(df_columns, use_container_width=True)
                
                with tab2:
                    # 显示统计信息
                    stats = get_table_stats(table_name)
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("记录数", f"{stats['record_count']:,}")
                    with col2:
                        st.metric("表大小", f"{stats['size_kb']:.2f} KB")
                    with col3:
                        if stats['size_mb'] >= 1:
                            st.metric("表大小(MB)", f"{stats['size_mb']:.2f} MB")
                
                with tab3:
                    # 显示示例数据
                    conn = sqlite3.connect('db/users.db')
                    try:
                        # 只显示前5条记录
                        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
                        if not df.empty:
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.info("表中没有数据")
                    except Exception as e:
                        st.error(f"读取数据时出错: {str(e)}")
                    finally:
                        conn.close()
                
                # 显示外键关系
                try:
                    conn = sqlite3.connect('db/users.db')
                    c = conn.cursor()
                    c.execute(f"PRAGMA foreign_key_list({table_name})")
                    foreign_keys = c.fetchall()
                    conn.close()
                    
                    if foreign_keys:
                        st.markdown("#### 外键关系")
                        for fk in foreign_keys:
                            st.text(f"• {fk[3]} -> {fk[2]}({fk[4]})")
                except Exception as e:
                    st.error(f"读取外键信息时出错: {str(e)}")
        
    except Exception as e:
        st.error(f"读取数据库结构时出错: {str(e)}") 