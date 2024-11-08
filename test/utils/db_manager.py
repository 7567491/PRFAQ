import sqlite3
from datetime import datetime
import json
import os

class DatabaseManager:
    def __init__(self, db_path='database/test_results.db'):
        self.db_path = db_path
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """初始化数据库"""
        conn = self.get_connection()
        c = conn.cursor()
        
        try:
            # 检查表是否存在
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_results'")
            table_exists = c.fetchone() is not None
            
            if table_exists:
                # 检查是否需要添加 user_name 列
                c.execute('PRAGMA table_info(test_results)')
                columns = [info[1] for info in c.fetchall()]
                
                if 'user_name' not in columns:
                    # 创建临时表
                    c.execute('''
                        CREATE TABLE test_results_temp
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         timestamp TEXT,
                         user_name TEXT,
                         mbti_type TEXT,
                         mbti_scores TEXT,
                         big5_scores TEXT,
                         holland_scores TEXT,
                         leadership_scores TEXT,
                         recommended_position TEXT)
                    ''')
                    
                    # 复制数据
                    c.execute('''
                        INSERT INTO test_results_temp 
                        (timestamp, mbti_type, mbti_scores, big5_scores, 
                         holland_scores, leadership_scores, recommended_position)
                        SELECT timestamp, mbti_type, mbti_scores, big5_scores,
                               holland_scores, leadership_scores, recommended_position
                        FROM test_results
                    ''')
                    
                    # 删除旧表
                    c.execute('DROP TABLE test_results')
                    
                    # 重命名新表
                    c.execute('ALTER TABLE test_results_temp RENAME TO test_results')
            else:
                # 创建新表
                c.execute('''
                    CREATE TABLE test_results
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     user_name TEXT,
                     mbti_type TEXT,
                     mbti_scores TEXT,
                     big5_scores TEXT,
                     holland_scores TEXT,
                     leadership_scores TEXT,
                     recommended_position TEXT)
                ''')
            
            # 创建用户反馈表（如果不存在）
            c.execute('''
                CREATE TABLE IF NOT EXISTS user_feedback
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 result_id INTEGER,
                 feedback_type TEXT,
                 feedback_content TEXT,
                 timestamp TEXT,
                 FOREIGN KEY(result_id) REFERENCES test_results(id))
            ''')
            
            conn.commit()
        except Exception as e:
            print(f"初始化数据库时发生错误: {str(e)}")
            conn.rollback()
        finally:
            conn.close()
    
    def save_result(self, results, user_id=None):
        """保存测评结果"""
        conn = self.get_connection()
        c = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 生成完整的测评报告
        from utils.result_generator import generate_report
        report = generate_report(results)
        
        # 提取推荐职位
        recommended_positions = []
        for suggestion in report['career_suggestions'][:1]:  # 只取第一个推荐方向
            for pos in suggestion['positions'][:1]:  # 只取第一个推荐职位
                recommended_positions.append(pos['name'])
        
        c.execute('''
            INSERT INTO test_results 
            (timestamp, user_name, mbti_type, mbti_scores, big5_scores, 
             holland_scores, leadership_scores, recommended_position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_time,
            user_id,
            results.get('mbti_type', ''),
            json.dumps(results['scores']['mbti']),
            json.dumps(results['scores']['big5']),
            json.dumps(results['scores']['holland']),
            json.dumps(report.get('leadership_analysis', {})),
            ', '.join(recommended_positions)
        ))
        
        result_id = c.lastrowid
        conn.commit()
        conn.close()
        return result_id
    
    def get_result(self, result_id):
        """获取特定的测评结果"""
        conn = self.get_connection()
        c = conn.cursor()
        
        result = c.execute('''
            SELECT * FROM test_results WHERE id = ?
        ''', (result_id,)).fetchone()
        
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'timestamp': result[1],
                'user_name': result[2],
                'mbti_type': result[3],
                'mbti_scores': json.loads(result[4]),
                'big5_scores': json.loads(result[5]),
                'holland_scores': json.loads(result[6]),
                'leadership_scores': json.loads(result[7]),
                'recommended_position': result[8]
            }
        return None
    
    def get_history(self, user_id=None, limit=10):
        """获取历史测评记录"""
        conn = self.get_connection()
        c = conn.cursor()
        
        # 检查表结构
        cursor = c.execute('SELECT * FROM test_results LIMIT 0')
        columns = [description[0] for description in cursor.description]
        
        # 构建查询语句
        select_columns = ['id', 'timestamp', 'user_name', 'mbti_type']
        if 'recommended_position' in columns:
            select_columns.append('recommended_position')
        
        query = f'''
            SELECT {', '.join(select_columns)}
            FROM test_results 
            {'WHERE user_name = ?' if user_id else ''}
            ORDER BY timestamp DESC 
            LIMIT ?
        '''
        
        if user_id:
            results = c.execute(query, (user_id, limit)).fetchall()
        else:
            results = c.execute(query, (limit,)).fetchall()
        
        conn.close()
        
        # 构建返回数据
        history = []
        for r in results:
            record = {
                'id': r[0],
                'timestamp': r[1],
                'user_name': r[2],
                'mbti_type': r[3],
            }
            if 'recommended_position' in columns and len(r) > 4:
                record['recommended_position'] = r[4]
            else:
                record['recommended_position'] = '未记录'
            history.append(record)
        
        return history
    
    def save_feedback(self, result_id, feedback_type, feedback_content):
        """保存用户反馈"""
        conn = self.get_connection()
        c = conn.cursor()
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute('''
            INSERT INTO user_feedback 
            (result_id, feedback_type, feedback_content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (result_id, feedback_type, feedback_content, current_time))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """获取测评统计数据"""
        conn = self.get_connection()
        c = conn.cursor()
        
        stats = {
            'total_tests': c.execute('SELECT COUNT(*) FROM test_results').fetchone()[0],
            'mbti_distribution': {},
            'recent_positions': []
        }
        
        # 获取MBTI类型分布
        mbti_results = c.execute('''
            SELECT mbti_type, COUNT(*) as count 
            FROM test_results 
            GROUP BY mbti_type
        ''').fetchall()
        stats['mbti_distribution'] = dict(mbti_results)
        
        # 获取最近的推荐职位（如果列存在）
        try:
            recent_positions = c.execute('''
                SELECT recommended_position, COUNT(*) as count
                FROM test_results
                WHERE recommended_position IS NOT NULL
                GROUP BY recommended_position
                ORDER BY count DESC
                LIMIT 5
            ''').fetchall()
            stats['recent_positions'] = recent_positions
        except:
            stats['recent_positions'] = []
        
        conn.close()
        return stats