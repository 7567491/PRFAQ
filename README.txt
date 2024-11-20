六页纸 AI 助手
====================
简介
----
这是一个基于 Streamlit 开发的 AI 辅助写作平台，集成了多种文档生成工具，包括逆向工作法、复盘六步法、FAQ生成等功能。
功能特性
--------
核心功能：
领导力测评 - 基于问卷的领导力能力评估
逆向工作法 - 通过未来新闻稿的形式规划项目
复盘六步法 - 系统化的项目复盘工具
辅助功能：
客户 FAQ 生成器
内部 FAQ 生成器
MLP（最小可行产品）开发规划
PRFAQ 一键生成
系统功能：
用户管理系统
积分管理系统
历史记录查看
数据库管理
AWS Marketplace 集成
文件结构
--------
project/
|-- admin/ # 管理员功能模块
|-- assets/ # 静态资源文件
|-- aws/ # AWS Marketplace 集成
|-- bill/ # 计费系统
|-- db/ # 数据库相关
| |-- users.db # SQLite数据库文件
|-- modules/ # 核心功能模块
|-- test/ # 测评相关
| |-- data/ # 测评数据
|-- user/ # 用户管理
|-- app.py # 主程序
|-- config.json # 配置文件
|-- requirements.txt # 依赖包列表
|-- templates.json # 模板配置


部署方法
--------
本地部署
1) 克隆代码库：
git clone [repository-url]
cd six-page-ai
2) 创建虚拟环境：
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
3) 安装依赖：
pip install -r requirements.txt
4) 配置环境：
复制 config.json.example 为 config.json
修改配置文件中的 API 密钥等信息
5) 运行应用：
streamlit run app.py
Docker 部署


1) 创建 Dockerfile：
FROM python:3.9-slim
WORKDIR /app
# 安装系统依赖
RUN apt-get update && apt-get install -y \
build-essential \
python3-dev \
&& rm -rf /var/lib/apt/lists/
# 复制项目文件
COPY . .
# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt
# 暴露端口
EXPOSE 8501
# 设置环境变量
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
# 启动命令
ENTRYPOINT ["streamlit", "run", "app.py"]


2) 构建镜像：
docker build -t six-page-ai .
3) 运行容器：
docker run -d \
-p 8501:8501 \
-v $(pwd)/db:/app/db \
-v $(pwd)/config.json:/app/config.json \
--name six-page-ai \
six-page-ai


Docker Compose 部署
1) 创建 docker-compose.yml：
version: '3'
services:
six-page-ai:
build: .
ports:
"8501:8501"
volumes:
./db:/app/db
./config.json:/app/config.json
restart: unless-stopped


2) 启动服务：
docker-compose up -d
环境要求
--------
Python 3.8+
SQLite3
python-docx (用于领导力测评报告生成)


其他依赖见 requirements.txt
配置说明
--------
config.json 示例：
{
"api": {
"endpoint": "YOUR_API_ENDPOINT",
"key": "YOUR_API_KEY"
},
"database": {
"path": "db/users.db"
}
}
数据库初始化：
首次运行时会自动创建数据库和必要的表
默认管理员账户：
用户名：admin
密码：admin123
注意事项
--------
请确保 db 目录具有写入权限
Docker 部署时建议挂载数据库文件到主机
定期备份数据库文件
生产环境部署时请修改默认管理员密码
建议使用 SSL 证书保护 Web 访问
定期检查日志文件大小
配置文件中的敏感信息请妥善保管
技术支持
--------
如有问题，请提交 Issue 或联系技术支持。
许可证