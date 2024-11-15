FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖和中文字体
RUN apt-get update && apt-get install -y \
    fonts-dejavu \
    fonts-arphic-uming \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app

# 启动应用
CMD ["streamlit", "run", "app.py"] 