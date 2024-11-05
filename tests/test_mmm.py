import unittest
from pathlib import Path
import tempfile
import shutil
import os
from mmm import collect_python_files, read_file_content, write_to_prfaq

class TestMMM(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建测试文件
        self.test_files = {
            'test1.py': 'print("Hello")',
            'test2.py': 'def test(): pass',
            'mmm.py': 'should not collect this',
            'test3.txt': 'not a python file'
        }
        
        # 创建子目录和文件
        self.sub_dir = self.test_dir / 'subdir'
        self.sub_dir.mkdir()
        self.test_files['subdir/test4.py'] = 'class Test: pass'
        
        # 写入测试文件
        for file_path, content in self.test_files.items():
            full_path = self.test_dir / file_path
            full_path.parent.mkdir(exist_ok=True)
            full_path.write_text(content, encoding='utf-8')

    def tearDown(self):
        # 清理临时测试目录
        shutil.rmtree(self.test_dir)

    def test_collect_python_files(self):
        """测试Python文件收集功能"""
        python_files = collect_python_files(self.test_dir)
        
        # 验证收集到的文件数量（应该是3个，不包括mmm.py）
        self.assertEqual(len(python_files), 3)
        
        # 验证文件名
        file_names = [f.name for f in python_files]
        self.assertIn('test1.py', file_names)
        self.assertIn('test2.py', file_names)
        self.assertIn('test4.py', file_names)
        self.assertNotIn('mmm.py', file_names)
        self.assertNotIn('test3.txt', file_names)

    def test_read_file_content(self):
        """测试文件读取功能"""
        test_file = self.test_dir / 'test1.py'
        content = read_file_content(test_file)
        self.assertEqual(content, 'print("Hello")')

    def test_write_to_mmm(self):
        """测试文件合并写入功能"""
        output_file = self.test_dir / 'mmm.txt'
        python_files = collect_python_files(self.test_dir)
        write_to_prfaq(python_files, str(output_file))
        
        # 验证输出文件存在
        self.assertTrue(output_file.exists())
        
        # 验证输出文件内容
        content = output_file.read_text(encoding='utf-8')
        self.assertIn('Python代码收集结果', content)
        self.assertIn('test1.py', content)
        self.assertIn('test2.py', content)
        self.assertIn('test4.py', content)
        self.assertIn('print("Hello")', content) 