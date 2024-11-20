import streamlit as st
import sqlite3
from pathlib import Path
from user.logger import add_log
from db.db_connection import get_db_connection
from datetime import datetime
import shutil
import os
import pandas as pd

def get_orphaned_data_stats():
    """统计数据库中的孤立数据
    
    返回:
        dict: 包含各类孤立数据的统计信息
    """
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        stats = {}
        
        # 检查孤立的账单记录（没有对应用户的账单）
        cursor.execute("""
            SELECT COUNT(*) FROM bills 
            WHERE user_id NOT IN (SELECT user_id FROM users)
        """)
        stats['orphaned_bills'] = cursor.fetchone()[0]
        
        # 检查孤立的日志记录
        cursor.execute("""
            SELECT COUNT(*) FROM logs 
            WHERE user_id NOT IN (SELECT user_id FROM users)
        """)
        stats['orphaned_logs'] = cursor.fetchone()[0]
        
        # 检查孤立的AWS客户记录（没有对应用户的记录）
        cursor.execute("""
            SELECT COUNT(*) FROM aws_customers 
            WHERE user_id NOT IN (SELECT user_id FROM users)
        """)
        stats['orphaned_aws_customers'] = cursor.fetchone()[0]
        
        # 获取孤立的AWS客户ID列表
        cursor.execute("""
            SELECT aws_customer_id FROM aws_customers 
            WHERE user_id NOT IN (SELECT user_id FROM users)
        """)
        orphaned_customer_ids = [row[0] for row in cursor.fetchall()]
        
        # 检查与孤立AWS客户关联的通知记录
        if orphaned_customer_ids:
            cursor.execute("""
                SELECT COUNT(*) FROM aws_notifications 
                WHERE aws_customer_id IN ({})
            """.format(','.join('?' * len(orphaned_customer_ids))), 
            orphaned_customer_ids)
        else:
            cursor.execute("SELECT 0")
        stats['orphaned_aws_notifications'] = cursor.fetchone()[0]
        
        # 检查与孤立AWS客户关联的订阅记录
        if orphaned_customer_ids:
            cursor.execute("""
                SELECT COUNT(*) FROM aws_subscriptions 
                WHERE aws_customer_id IN ({})
            """.format(','.join('?' * len(orphaned_customer_ids))), 
            orphaned_customer_ids)
        else:
            cursor.execute("SELECT 0")
        stats['orphaned_aws_subscriptions'] = cursor.fetchone()[0]
        
        # 计算总的孤立数据数量
        stats['total_orphaned'] = sum(stats.values())
        
        # 添加时间戳
        stats['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn.close()
        add_log("info", f"成功统计孤立数据: 共发现 {stats['total_orphaned']} 条")
        return stats
        
    except Exception as e:
        add_log("error", f"获取孤立数据统计失败: {str(e)}")
        st.error(f"获取孤立数据统计失败: {str(e)}")
        return None

def backup_database():
    """备份数据库
    
    返回:
        str: 备份文件路径，如果失败则返回None
    """
    try:
        # 创建备份目录
        backup_dir = Path("db/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"users_db_backup_{timestamp}.db"
        
        # 复制数据库文件
        shutil.copy2('db/users.db', backup_path)
        
        add_log("info", f"数据库已备份到: {backup_path}")
        return str(backup_path)
    except Exception as e:
        add_log("error", f"数据库备份失败: {str(e)}")
        return None

def clear_orphaned_data():
    """清理数据库中的孤立数据
    
    返回:
        dict: 清理结果统计信息，失败返回None
    """
    try:
        # 首先进行数据库备份
        backup_path = backup_database()
        if not backup_path:
            st.error("数据库备份失败，为确保安全，清理操作已取消")
            return None
            
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        # 开始事务
        conn.execute("BEGIN TRANSACTION")
        
        try:
            results = {
                'deleted_subscriptions': 0,
                'deleted_notifications': 0,
                'deleted_customers': 0,
                'deleted_bills': 0,
                'deleted_logs': 0
            }
            
            # 1. 首先获取孤立的AWS客户ID
            cursor.execute("""
                SELECT id FROM aws_customers 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)
            orphaned_customer_ids = [row[0] for row in cursor.fetchall()]
            
            # 2. 删除关联的订阅记录
            if orphaned_customer_ids:
                cursor.execute("""
                    DELETE FROM aws_subscriptions 
                    WHERE customer_id IN ({})
                    RETURNING id
                """.format(','.join('?' * len(orphaned_customer_ids))), 
                orphaned_customer_ids)
                results['deleted_subscriptions'] = len(cursor.fetchall())
            
            # 3. 删除关联的通知记录
            if orphaned_customer_ids:
                cursor.execute("""
                    DELETE FROM aws_notifications 
                    WHERE customer_id IN ({})
                    RETURNING id
                """.format(','.join('?' * len(orphaned_customer_ids))), 
                orphaned_customer_ids)
                results['deleted_notifications'] = len(cursor.fetchall())
            
            # 4. 删除孤立的AWS客户记录
            cursor.execute("""
                DELETE FROM aws_customers 
                WHERE user_id NOT IN (SELECT id FROM users)
                RETURNING id
            """)
            results['deleted_customers'] = len(cursor.fetchall())
            
            # 5. 删除孤立的账单记录
            cursor.execute("""
                DELETE FROM bills 
                WHERE user_id NOT IN (SELECT id FROM users)
                RETURNING id
            """)
            results['deleted_bills'] = len(cursor.fetchall())
            
            # 6. 删除孤立的日志记录
            cursor.execute("""
                DELETE FROM logs 
                WHERE user_id NOT IN (SELECT id FROM users)
                RETURNING id
            """)
            results['deleted_logs'] = len(cursor.fetchall())
            
            # 提交事务
            conn.commit()
            
            # 添加总计和时间戳
            results['total_deleted'] = sum(results.values())
            results['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results['backup_path'] = backup_path
            
            add_log("info", f"成功清理孤立数据: 共清理 {results['total_deleted']} 条记录")
            return results
            
        except Exception as e:
            # 发生错误时回滚事务
            conn.rollback()
            raise e
            
        finally:
            conn.close()
            
    except Exception as e:
        add_log("error", f"清理孤立数据失败: {str(e)}")
        st.error(f"清理孤立数据失败: {str(e)}")
        return None

def show_clear_interface():
    """显示数据清理界面"""
    st.header("🧹 数据清理")
    
    # 添加刷新按钮
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("孤立数据统计")
    with col2:
        if st.button("🔄 刷新"):
            st.rerun()
    
    # 获取孤立数据统计
    with st.spinner("正在统计孤立数据..."):
        stats = get_orphaned_data_stats()
        
    if stats:
        # 创建一个展开区域显示详细统计信息
        with st.expander("📊 详细统计信息", expanded=True):
            # 使用三列布局显示统计信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "孤立账单记录", 
                    stats['orphaned_bills'],
                    help="没有对应用户的账单记录"
                )
                st.metric(
                    "孤立日志记录", 
                    stats['orphaned_logs'],
                    help="没有对应用户的日志记录"
                )
            
            with col2:
                st.metric(
                    "孤立AWS客户", 
                    stats['orphaned_aws_customers'],
                    help="没有对应用户的AWS客户记录"
                )
                st.metric(
                    "孤立AWS通知", 
                    stats['orphaned_aws_notifications'],
                    help="与孤立AWS客户关联的通知记录"
                )
            
            with col3:
                st.metric(
                    "孤立AWS订阅", 
                    stats['orphaned_aws_subscriptions'],
                    help="与孤立AWS客户关联的订阅记录"
                )
                st.metric(
                    "孤立数据总数", 
                    stats['total_orphaned'],
                    help="所有类型的孤立数据总和"
                )
            
            st.caption(f"🕒 最后更新时间: {stats['timestamp']}")
        
        # 只有存在孤立数据时才显示清理选项
        if stats['total_orphaned'] > 0:
            st.divider()
            st.subheader("🗑️ 数据清理")
            
            # 添加确认复选框
            confirm = st.checkbox(
                "我已了解清理操作将永久删除这些数据，并且已确认这些数据确实无用",
                help="清理操作不可撤销，但会在清理前自动备份数据库"
            )
            
            # 清理按钮
            if confirm:
                if st.button("执行清���", type="primary", use_container_width=True):
                    # 显示进度提示
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                    
                    # 备份阶段
                    progress_text.text("正在备份数据库...")
                    progress_bar.progress(20)
                    
                    # 执行清理
                    progress_text.text("正在清理数据...")
                    progress_bar.progress(40)
                    results = clear_orphaned_data()
                    
                    if results:
                        # 更新进度
                        progress_bar.progress(100)
                        progress_text.empty()
                        
                        # 显示结果统计
                        st.success("✅ 清理完成！")
                        
                        # 使用表格显示详细结果
                        result_df = pd.DataFrame([
                            ["AWS订阅记录", results['deleted_subscriptions']],
                            ["AWS通知记录", results['deleted_notifications']],
                            ["AWS客户记录", results['deleted_customers']],
                            ["账单记录", results['deleted_bills']],
                            ["日志记录", results['deleted_logs']],
                            ["总计", results['total_deleted']]
                        ], columns=["数据类型", "清理数量"])
                        
                        st.table(result_df)
                        
                        # 显示备份信息
                        st.info(f"""
                        💾 数据库已备份至：
                        `{results['backup_path']}`
                        """)
                        
                        # 添加刷新按钮
                        if st.button("刷新统计信息"):
                            st.rerun()
                    else:
                        progress_bar.empty()
                        progress_text.empty()
                        st.error("❌ 清理操作失败，请查看错误信息")
            else:
                st.button(
                    "执行清理", 
                    type="primary", 
                    disabled=True,
                    help="请先确认清理操作",
                    use_container_width=True
                )
        else:
            st.success("✨ 当前没有检测到孤立数据，数据库状态良好。")
    else:
        st.error("❌ 无法获取孤立数据统计信息。")
        
    # 添加帮助信息
    with st.expander("ℹ️ 关于数据清理"):
        st.markdown("""
        **什么是孤立数据？**
        - 孤立数据是指那些失去了关联关系的数据记录
        - 例如：某个用户被删除后，与该用户关联的账单、日志等记录就成为了孤立数据
        
        **清理操作说明：**
        1. 系统会自动检测各类孤立数据
        2. 清理前会自动备份数据库
        3. 清理操作使用事务确保数据一致性
        4. 清理操作不可撤销，但可以通过备份恢复
        
        **注意事项：**
        - 执行清理前请确认数据确实无用
        - 如需恢复已清理的数据，可使用备份功能
        - 建议定期检查和清理孤立数据
        """)