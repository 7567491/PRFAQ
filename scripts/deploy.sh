#!/bin/bash

# 确保脚本在错误时退出
set -e

echo "开始部署..."

# 1. 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 2. 设置字体
echo "设置字体..."
python scripts/setup_fonts.py

# 3. 创建必要的目录
echo "创建必要的目录..."
mkdir -p assets/fonts
mkdir -p output
mkdir -p db/backup

# 4. 设置权限
echo "设置权限..."
chmod -R 755 assets/fonts
chmod -R 755 output
chmod -R 755 db

echo "部署完成！" 