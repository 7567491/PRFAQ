FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# 安装中文字体支持
RUN apt-get update && apt-get install -y \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 升级pip并安装依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 8501

# 启动命令（需要根据你的主程序文件名调整）
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"] 