import streamlit as st
from datetime import datetime
import os
import sqlite3
from db.backup_db import backup_database
from db.db_init import init_database
from db.read_db import read_database
from db.db_restore import show_restore_interface
from db.migrate_data import show_migrate_interface
from user.logger import add_log
import pandas as pd
from db.db_upgrade import upgrade_database
from db.db_table import show_table_info

def check_column_mapping(conn: sqlite3.Connection) -> dict:
    """检查列映射关系"""
    c = conn.cursor()
    
    # 获取当前表结构
    c.execute("PRAGMA table_info(users)")
    current_columns = {row[1]: row[2] for row in c.fetchall()}
    
    # 定义新旧列名映射
    column_mapping = {
        'daily_limit': 'daily_chars_limit',
        'used_today': 'used_chars_today',
        'api_calls': 'total_chars'  # 如果存在这个旧列
    }
    
    # 检查实际存在的列
    existing_mappings = {}
    for old_col, new_col in column_mapping.items():
        if old_col in current_columns:
            existing_mappings[old_col] = new_col
    
    return existing_mappings

def get_current_columns(conn: sqlite3.Connection) -> list:
    """获取当前表的所有列名"""
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    return [row[1] for row in c.fetchall()]

def generate_migration_sql(conn: sqlite3.Connection, mappings: dict) -> str:
    """生成迁移SQL语句"""
    current_columns = get_current_columns(conn)
    
    # 基本列（新表中的所有列）
    new_columns = [
        'user_id', 'username', 'password', 'email', 'phone', 
        'org_name', 'role', 'is_active', 'created_at', 'last_login',
        'total_chars', 'total_cost', 'daily_chars_limit', 'used_chars_today'
    ]
    
    # 构建SELECT部分
    select_parts = []
    for col in new_columns:
        if col in current_columns:  # 如果列已存在
            select_parts.append(col)
        elif col in mappings.values():  # 如果是需要重命名的列
            old_col = [k for k, v in mappings.items() if v == col][0]
            select_parts.append(f"{old_col} as {col}")
        else:  # 如果是新列，使用默认值
            if col in ['total_chars', 'used_chars_today']:
                select_parts.append("0 as " + col)
            elif col == 'daily_chars_limit':
                select_parts.append("100000 as " + col)
            elif col == 'total_cost':
                select_parts.append("0.0 as " + col)
            else:
                select_parts.append("NULL as " + col)
    
    return f"""
    INSERT INTO users_new (
        {', '.join(new_columns)}
    )
    SELECT 
        {', '.join(select_parts)}
    FROM users
    """

def cleanup_temp_tables(conn: sqlite3.Connection) -> None:
    """清理临时表"""
    c = conn.cursor()
    try:
        c.execute("DROP TABLE IF EXISTS users_new")
        conn.commit()
    except sqlite3.Error as e:
        add_log("error", f"清理临时表失败: {str(e)}")

def check_upgrade_needed(conn: sqlite3.Connection) -> bool:
    """检查是否需要升级"""
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in c.fetchall()}
    
    # 检查是否已经是新结构
    new_columns = {
        'daily_chars_limit',
        'used_chars_today',
        'total_chars',
        'total_cost'
    }
    
    return not new_columns.issubset(columns)

def upgrade_bills_table(conn: sqlite3.Connection) -> dict:
    """升级账单表结构"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    c = conn.cursor()
    try:
        # 1. 创建新的账单表
        c.execute('''
        CREATE TABLE IF NOT EXISTS bills_new (
            bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            api_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            input_letters INTEGER NOT NULL,
            output_letters INTEGER NOT NULL,
            total_cost REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        results['details'].append("创建新账单表成功")
        
        # 2. 检查旧表是否存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bills'")
        if c.fetchone():
            # 3. 迁移数据
            c.execute('''
            INSERT INTO bills_new (
                user_id, timestamp, api_name, operation,
                input_letters, output_letters, total_cost
            )
            SELECT 
                user_id, timestamp, api_name, operation,
                input_letters, output_letters,
                COALESCE(total_cost_rmb, (input_letters + output_letters) * 0.0001) as total_cost
            FROM bills
            ''')
            results['details'].append("数据迁移成功")
            
            # 4. 删除旧表
            c.execute('DROP TABLE bills')
            results['details'].append("删除旧账单表成功")
        
        # 5. 重命名新表
        c.execute('ALTER TABLE bills_new RENAME TO bills')
        results['details'].append("重命名新账单表成功")
        
        results['success'] = True
        results['message'] = "账单表升级成功"
        
    except Exception as e:
        results['message'] = f"账单表升级失败: {str(e)}"
        results['details'].append(f"错误详情: {str(e)}")
        raise
    
    return results

def upgrade_database() -> dict:
    """升级数据库结构"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    conn = sqlite3.connect('db/users.db')
    
    try:
        # 0. 检查是否需要升级
        if not check_upgrade_needed(conn):
            results['success'] = True
            results['message'] = "数据库已是最新版本，无需升级"
            results['details'].append("检测到当前数据库结构已经是最新的")
            return results
        
        # 1. 清理可能存在的临时表
        cleanup_temp_tables(conn)
        results['details'].append("清理临时表成功")
        
        # 2. 检查当前表结构
        c = conn.cursor()
        column_mappings = check_column_mapping(conn)
        current_columns = get_current_columns(conn)
        results['details'].append(f"当前表列: {current_columns}")
        results['details'].append(f"需要迁移的列: {column_mappings}")
        
        # 3. 创建临时表
        c.execute('''
        CREATE TABLE users_new (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            org_name TEXT,
            role TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT,
            total_chars INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            daily_chars_limit INTEGER DEFAULT 100000,
            used_chars_today INTEGER DEFAULT 0
        )
        ''')
        results['details'].append("创建临时表成功")
        
        # 4. 生成并执行迁移SQL
        migration_sql = generate_migration_sql(conn, column_mappings)
        results['details'].append("生成迁移SQL成功")
        results['details'].append(f"SQL: {migration_sql}")
        
        try:
            c.execute(migration_sql)
            results['details'].append("数据迁移成功")
        except sqlite3.Error as e:
            raise DatabaseError(f"数据迁移失败: {str(e)}")
        
        # 5. 验证迁移的数据
        c.execute("SELECT COUNT(*) FROM users")
        old_count = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM users_new")
        new_count = c.fetchone()[0]
        
        if old_count != new_count:
            raise DatabaseError(f"数据数量不匹配: 原表 {old_count} 条, 新表 {new_count} 条")
        
        results['details'].append(f"数据验证成功: {new_count} 条记录")
        
        # 6. 删除旧表
        c.execute('DROP TABLE users')
        results['details'].append("删除旧表成功")
        
        # 7. 重命名新表
        c.execute('ALTER TABLE users_new RENAME TO users')
        results['details'].append("重命名新表成功")
        
        # 2. 升级账单表
        bills_results = upgrade_bills_table(conn)
        results['details'].extend(bills_results['details'])
        
        if not bills_results['success']:
            raise DatabaseError(bills_results['message'])
        
        conn.commit()
        results['success'] = True
        results['message'] = "数据库升级成功"
        add_log("info", "数据库升级成功")
        
    except Exception as e:
        conn.rollback()
        # 确保清理临时表
        cleanup_temp_tables(conn)
        results['message'] = f"数据库升级失败: {str(e)}"
        add_log("error", results['message'])
        results['details'].append(f"错误详情: {str(e)}")
    
    finally:
        conn.close()
    
    return results

class DatabaseError(Exception):
    """自定义数据库错误"""
    pass

def fix_bill_associations(conn: sqlite3.Connection) -> dict:
    """修复账单关联"""
    results = {
        'success': False,
        'message': '',
        'details': []
    }
    
    c = conn.cursor()
    try:
        # 获取 Rose 的 user_id
        c.execute("SELECT user_id FROM users WHERE username = ?", ('Rose',))
        rose_id = c.fetchone()
        
        if not rose_id:
            results['message'] = "未找到用户 Rose"
            return results
        
        rose_id = rose_id[0]
        
        # 查找未关联的账单
        c.execute("""
            SELECT COUNT(*)
            FROM bills b
            LEFT JOIN users u ON b.user_id = u.user_id
            WHERE u.user_id IS NULL
        """)
        orphaned_count = c.fetchone()[0]
        
        if orphaned_count > 0:
            # 将未关联的账单关联到 Rose
            c.execute("""
                UPDATE bills
                SET user_id = ?
                WHERE user_id NOT IN (SELECT user_id FROM users)
            """, (rose_id,))
            
            conn.commit()
            results['success'] = True
            results['message'] = f"成功修复 {orphaned_count} 条未关联账单"
            results['details'].append(f"已将 {orphaned_count} 条账单关联到用户 Rose")
        else:
            results['success'] = True
            results['message'] = "所有账单关联正常"
            
    except Exception as e:
        conn.rollback()
        results['message'] = f"修复账单关联失败: {str(e)}"
        results['details'].append(f"错误详情: {str(e)}")
    
    return results

def show_db_admin():
    """显示数据库管理界面"""
    if st.session_state.get('user_role') != 'admin':
        st.error("无权限访问此页面")
        return
    
    st.title("数据库管理")
    
    # 使用选项卡来组织不同功能
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 数据库状态",
        "🔧 初始化",
        "💾 备份",
        "♻️ 恢复",
        "📥 数据迁移",
        "⚡ 升级",
        "📋 表结构"
    ])
    
    with tab1:
        st.markdown("### 数据库查看")
        if st.button("刷新数据库信息", use_container_width=True):
            try:
                if os.path.exists('db/users.db'):
                    # 获取数据库信息
                    db_info = read_database()
                    
                    # 检查是否有未关联的账单
                    if db_info.get('orphaned_bills'):
                        st.warning(f"发现 {len(db_info['orphaned_bills'])} 个未关联的账单记录")
                        if st.button("修复账单关联"):
                            conn = sqlite3.connect('db/users.db')
                            results = fix_bill_associations(conn)
                            conn.close()
                            
                            if results['success']:
                                st.success(results['message'])
                                for detail in results['details']:
                                    st.text(f"✓ {detail}")
                            else:
                                st.error(results['message'])
                    
                    # 显示表结构
                    st.markdown("#### 表结构")
                    st.code(db_info['schema'])
                    
                    # 显示用户数据
                    st.markdown("#### 用户数据")
                    st.dataframe(db_info['users'])
                    
                    # 显示数据库统计
                    st.markdown("#### 数据库统计")
                    
                    # 账单统计
                    st.markdown("##### 账单记录")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("总账单数", f"{db_info['bills_stats']['total_count']:,}")
                    with col2:
                        st.metric("总输入字符", f"{db_info['bills_stats']['total_input']:,}")
                    with col3:
                        st.metric("总输出字符", f"{db_info['bills_stats']['total_output']:,}")
                    with col4:
                        st.metric("使用天数", f"{db_info['bills_stats']['unique_days']:,}")
                    
                    # 历史记录统计
                    st.markdown("##### 历史记录")
                    col5, col6, col7, col8 = st.columns(4)
                    with col5:
                        st.metric("总记录数", f"{db_info['history_stats']['total_count']:,}")
                    with col6:
                        st.metric("记录类型数", f"{db_info['history_stats']['unique_types']:,}")
                    with col7:
                        st.metric("活跃用户数", f"{db_info['history_stats']['unique_users']:,}")
                    with col8:
                        st.metric("记录天数", f"{db_info['history_stats']['unique_days']:,}")
                    
                    st.info("""
                        说明：
                        - 账单记录：每次调用API时产生的使用记录（包括字符统计和费用）
                        - 历史记录：完整的生成内容（如PR文档、FAQ等）
                    """)
                    
                    add_log("info", "查看数据库信息")
                else:
                    st.error("数据库文件不存在")
                    add_log("error", "尝试查看时发现数据库文件不存在")
            except Exception as e:
                error_msg = f"查看数据库失败: {str(e)}"
                st.error(error_msg)
                add_log("error", error_msg)
    
    with tab2:
        st.markdown("### 数据库初始化")
        st.warning("⚠️ 初始化操作会影响数据库结构，请谨慎操作！")
        if st.button("初始化数据库", use_container_width=True):
            try:
                if not os.path.exists('db/users.db'):
                    init_database()
                    st.success("数据库初始化成功")
                    add_log("info", "数据库初始化成功")
                else:
                    confirm = st.checkbox("数据库已存在，确定要重新初始化吗？这可能会影响现有数据")
                    if confirm and st.button("确认重新初始化"):
                        # 先备份现有数据库
                        backup_database()
                        init_database()
                        st.success("数据库重新初始化成功")
                        add_log("info", "数据库重新初始化成功")
            except Exception as e:
                error_msg = f"数据库初始化失败: {str(e)}"
                st.error(error_msg)
                add_log("error", error_msg)
    
    with tab3:
        st.markdown("### 数据库备份")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("创建备份", use_container_width=True):
                try:
                    if os.path.exists('db/users.db'):
                        backup_database()
                        st.success("数据库备份成功")
                        add_log("info", "数据库备份成功")
                        st.rerun()  # 刷新备份列表
                    else:
                        st.error("数据库文件不存在")
                        add_log("error", "尝试备份时发现数据库文件不存在")
                except Exception as e:
                    error_msg = f"数据备份失败: {str(e)}"
                    st.error(error_msg)
                    add_log("error", error_msg)
        
        with col2:
            st.markdown("#### 现有备份")
            backup_dir = 'db/backups'
            if os.path.exists(backup_dir):
                backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
                if backups:
                    for backup in sorted(backups, reverse=True):
                        st.text(backup)
                else:
                    st.info("暂无备份文件")
            else:
                st.info("备份目录不存在")
    
    with tab4:
        show_restore_interface()
    
    with tab5:
        show_migrate_interface()
    
    with tab6:
        st.markdown("### 数据库升级")
        st.warning("⚠️ 升级操作将更新数据库结构。建议在升级前先备份数据库！")
        
        # 显示当前版本信息
        st.info("""
        当前更新内容：
        1. 重命名 daily_limit 为 daily_chars_limit
        2. 重命名 used_today 为 used_chars_today
        3. 优化字符统计相关字段
        4. 更新账单表结构
        """)
        
        # 添加确认步骤
        confirm = st.checkbox("我已了解升级操作的风险")
        
        if confirm:
            if st.button("开始升级", use_container_width=True):
                with st.spinner("正在升级数据库..."):
                    results = upgrade_database()
                
                if results['success']:
                    st.success(results['message'])
                    with st.expander("查看升级详情"):
                        for detail in results['details']:
                            st.text(f"✓ {detail}")
                else:
                    st.error(results['message'])
                    with st.expander("查看错误详情"):
                        for detail in results['details']:
                            st.text(f"⚠ {detail}")
    
    with tab7:
        show_table_info()