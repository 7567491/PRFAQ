FROM python:3.12-slim

WORKDIR /app

# 复制项目文件
COPY . .

# 设置环境变量
ENV LANG=zh_CN.UTF-8
ENV LC_ALL=zh_CN.UTF-8
ENV PYTHONIOENCODING=utf8

# 安装系统依赖和字体
RUN apt-get update && apt-get install -y \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    xfonts-wqy \
    fontconfig \
    locales \
    locales-all \
    && locale-gen zh_CN.UTF-8 \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置权限
RUN chmod -R 755 assets/fonts output db

# 启动应用
CMD ["streamlit", "run", "app.py"] 