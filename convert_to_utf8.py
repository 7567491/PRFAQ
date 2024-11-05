import json
from pathlib import Path

def convert_file_to_utf8(file_path):
    try:
        # 尝试以 UTF-8 读取
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # 如果失败，尝试以 GBK 读取
        with open(file_path, 'r', encoding='gbk') as f:
            data = json.load(f)
    
    # 以 UTF-8 写入
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 转换所有 JSON 文件
json_files = ['config.json', 'templates.json', 'prompts.json', 'metrics.json']
for file_name in json_files:
    file_path = Path(file_name)
    if file_path.exists():
        print(f"Converting {file_name} to UTF-8...")
        convert_file_to_utf8(file_path)
        print(f"Converted {file_name} successfully!") 