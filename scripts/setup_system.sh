#!/bin/bash

# 确保脚本以root权限运行
if [ "$EUID" -ne 0 ]; then 
    echo "请使用sudo运行此脚本"
    exit 1
fi

echo "开始配置系统环境..."

# 更新系统包列表
echo "更新系统包列表..."
apt-get update

# 安装必要的字体包和字体工具
echo "安装字体包和工具..."
apt-get install -y \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    xfonts-wqy \
    fontconfig \
    locales \
    locales-all

# 配置中文支持
echo "配置中文支持..."
locale-gen zh_CN.UTF-8
update-locale LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8

# 刷新字体缓存
echo "刷新字体缓存..."
fc-cache -fv

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p /usr/share/fonts/chinese
mkdir -p assets/fonts
mkdir -p output
mkdir -p db/backup

# 设置目录权限
echo "设置目录权限..."
chmod -R 755 /usr/share/fonts/chinese
chmod -R 755 assets/fonts
chmod -R 755 output
chmod -R 755 db

# 复制字体文件到系统目录
echo "复制字体文件..."
if [ -f "assets/fonts/wqy-microhei.ttc" ]; then
    cp assets/fonts/wqy-microhei.ttc /usr/share/fonts/chinese/
fi
if [ -f "assets/fonts/wqy-zenhei.ttc" ]; then
    cp assets/fonts/wqy-zenhei.ttc /usr/share/fonts/chinese/
fi

# 再次刷新字体缓存
echo "最终刷新字体缓存..."
fc-cache -fv

# 验证字体安装
echo "验证字体安装..."
fc-list :lang=zh

# 验证中文支持
echo "验证中文支持..."
locale -a | grep zh
echo "当前语言环境: $LANG"

# 设置环境变量
echo "设置环境变量..."
cat >> /etc/environment << EOF
LANG=zh_CN.UTF-8
LC_ALL=zh_CN.UTF-8
PYTHONIOENCODING=utf8
EOF

echo "系统配置完成！"

# 显示系统信息
echo "系统信息："
echo "操作系统：$(uname -a)"
echo "Python版本：$(python3 --version)"
echo "字体列表："
fc-list | grep "wqy"

# 提示重启
echo "建议重启系统以使所有更改生效。"
echo "是否现在重启？(y/n)"
read -r answer
if [ "$answer" = "y" ]; then
    reboot
fi 