AWS Marketplace 用户集成流程

1. Webhook 端点
开发环境：
- http://localhost:8000/register

生产环境：
- https://amazonsp.com/mp
- 由 Nginx 反向代理到内部 FastAPI 服务

2. 登录重定向流程
开发环境：
- Webhook 接收请求 -> 生成重定向 URL -> http://localhost:8501/?source=aws-mp&...

生产环境：
- Webhook 接收请求 -> 生成重定向 URL -> https://amazonsp.com/?source=aws-mp&...
- 参数包含：user、account、product 信息

3. 登录处理
- app.py 检测 URL 参数：source=aws-mp
- 与普通用户一样转入登录界面

4. 安全机制
- 操作日志记录
- 错误处理和告警

5. 环境变量配置
开发环境：
- WEBHOOK_URL=http://localhost:8000
- STREAMLIT_URL=http://localhost:8501

生产环境：
- WEBHOOK_URL=https://amazonsp.com/mp
- STREAMLIT_URL=https://amazonsp.com

6. Docker 配置步骤
Webhook 服务配置：
- 创建 Dockerfile.webhook
- 基于 python:3.12-slim
- 暴露端口 8000
- 运行 FastAPI 服务

Streamlit 应用配置：
- 创建 Dockerfile.app
- 基于 python:3.12-slim
- 暴露端口 8501
- 运行 Streamlit 应用

Docker Compose 配置：
- 创建 docker-compose.yml
- 定义两个服务：webhook 和 app
- 配置网络连接
- 设置环境变量
- 配置 Nginx 反向代理

部署命令：
- docker-compose build
- docker-compose up -d
- 查看日志：docker-compose logs -f 


开发环境启动docker-compose up -d

生产环境启动
WEBHOOK_URL=https://amazonsp.com/mp STREAMLIT_URL=https://amazonsp.com docker-compose up -d

创建 .env 文件（可选）
WEBHOOK_URL=https://amazonsp.com/mp
STREAMLIT_URL=https://amazonsp.com



需要单独添加 portalocker 包
# 进入容器
docker exec -it prfaq-main bash

# 安装包
pip install portalocker

# 退出容器
exit