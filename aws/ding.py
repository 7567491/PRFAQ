from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import json
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime
from pathlib import Path
import base64

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 设置应用和模板
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

class MarketplaceSimulator:
    def __init__(self):
        # 从环境变量获取配置
        self.webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:8000')
        self.product_code = os.getenv('AWS_PRODUCT_CODE', 'default_product_code')
    
    def generate_token(self):
        """生成一个随机的Base64编码令牌"""
        # 生成32字节的随机数据
        random_bytes = os.urandom(32)
        # 转换为Base64字符串
        token = base64.b64encode(random_bytes).decode('utf-8')
        # 添加test-前缀
        token = f"test-{token}"
        
        logger.info(f"生成新的测试Token: {token}")
        return token

# 创建模拟器实例
simulator = MarketplaceSimulator()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """渲染主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "product_code": simulator.product_code
    })

@app.post("/api/send-registration")
async def send_registration():
    """发送注册请求到webhook并记录详细过程"""
    process_log = []
    try:
        # 1. 生成随机token
        logger.info("开始模拟 AWS Marketplace 注册流程...")
        token = simulator.generate_token()
        process_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": "第一步：生成随机Token",
            "details": token
        })

        # 2. 准备HTTP请求
        request_data = {"x-amzn-marketplace-token": token}
        request_url = f"{simulator.webhook_url}/register"
        logger.info(f"准备发送注册请求到Webhook服务: {request_url}")
        process_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": "第二步：准备发送注册请求",
            "details": {
                "目标地址": request_url,
                "请求方式": "POST",
                "请求头": {"Content-Type": "application/x-www-form-urlencoded"},
                "请求数据": request_data
            }
        })

        # 3. 发送请求
        logger.info("正在发送注册请求到Webhook...")
        response = requests.post(
            request_url,
            data=request_data,
            allow_redirects=False
        )
        
        logger.info(f"收到Webhook响应: HTTP状态码 {response.status_code}")
        process_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": "第三步：收到Webhook响应",
            "details": {
                "状态码": response.status_code,
                "响应头": dict(response.headers)
            }
        })

        # 4. 处理响应
        result = {
            "status": "success",
            "process_log": process_log,
            "request": {
                "url": request_url,
                "method": "POST",
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
                "body": request_data
            },
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }
        }

        # 5. 获取webhook返回的登录地址
        try:
            response_data = response.json()
            if "login_url" in response_data:
                login_url = response_data["login_url"]
                logger.info(f"从Webhook获取到登录地址: {login_url}")
                process_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "step": "第四步：获取登录地址",
                    "details": {"登录地址": login_url}
                })
                result["redirect_url"] = login_url
            else:
                logger.warning("Webhook响应中未包含登录地址")
        except json.JSONDecodeError:
            logger.warning("Webhook响应格式不是有效的JSON")
        except KeyError:
            logger.warning("Webhook响应中缺少登录地址字段")

        logger.info("AWS Marketplace 注册流程模拟完成")
        return result
        
    except Exception as e:
        error_msg = f"注册过程发生错误: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=400, detail={
            "error": error_msg,
            "process_log": process_log
        })

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8002))
    uvicorn.run(app, host="0.0.0.0", port=port) 