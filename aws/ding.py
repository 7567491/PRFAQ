from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import json
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path
import boto3
import os
from dotenv import load_dotenv
import logging
import requests
import traceback

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('marketplace_simulator')

app = FastAPI(title="AWS Marketplace Event Simulator")

# 设置模板目录
templates = Jinja2Templates(directory="aws/templates")

# 创建templates目录
Path("aws/templates").mkdir(parents=True, exist_ok=True)

class MarketplaceSimulator:
    def __init__(self):
        self.product_code = os.getenv('AWS_PRODUCT_CODE')
        self.webhook_url = "http://localhost:8000"
    
    def generate_customer_id(self):
        return f"cust-{uuid.uuid4().hex[:8]}"
    
    def generate_aws_account_id(self):
        return ''.join([str(random.randint(0, 9)) for _ in range(12)])
    
    def generate_token(self, customer_id=None, aws_account_id=None):
        """生成模拟的注册token"""
        if not customer_id:
            customer_id = self.generate_customer_id()
        if not aws_account_id:
            aws_account_id = self.generate_aws_account_id()
            
        token_data = {
            "customerIdentifier": customer_id,
            "customerAWSAccountId": aws_account_id,
            "productCode": self.product_code,
            "timestamp": datetime.utcnow().isoformat(),
            "signature": f"sim-{uuid.uuid4().hex}"
        }
        return token_data
    
    def generate_sns_message(self, event_type, details=None):
        """生成SNS消息"""
        if details is None:
            details = {}
            
        message = {
            "Type": event_type,
            "MessageId": str(uuid.uuid4()),
            "TopicArn": os.getenv('AWS_MP_SUBSCRIPTION_ARN'),
            "Message": json.dumps({
                "action": event_type,
                "customerIdentifier": self.generate_customer_id(),
                "productCode": self.product_code,
                "timestamp": datetime.utcnow().isoformat(),
                **details
            }),
            "Timestamp": datetime.utcnow().isoformat(),
            "SignatureVersion": "1",
            "Signature": f"sim-{uuid.uuid4().hex}",
            "SigningCertURL": "https://simulator.amazonses.com/cert.pem"
        }
        return message

simulator = MarketplaceSimulator()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """渲染主页"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "product_code": os.getenv('AWS_PRODUCT_CODE')
    })

@app.post("/api/generate-token")
async def generate_token(request: Request):
    """生成注册token"""
    try:
        data = await request.json()
        token = simulator.generate_token(
            customer_id=data.get('customerIdentifier'),
            aws_account_id=data.get('customerAWSAccountId')
        )
        return {"token": token}
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/send-registration")
async def send_registration(request: Request):
    """发送注册请求到webhook"""
    try:
        data = await request.json()
        token = data.get('token')
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        logger.info(f"Sending registration request with token: {token}")
        
        # 发送请求时不要自动跟随重定向
        response = requests.post(
            f"{simulator.webhook_url}/register",
            data={"x-amzn-marketplace-token": json.dumps({
                "customerIdentifier": token["customerIdentifier"],
                "customerAWSAccountId": token["customerAWSAccountId"],
                "productCode": token["productCode"]
            })},
            allow_redirects=False  # 不自动跟随重定向
        )
        
        logger.info(f"Webhook response: {response.status_code}")
        
        # 如果是重定向响应
        if response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = response.headers.get('Location')
            return {
                "status": "success",
                "webhook_response": {
                    "status_code": response.status_code,
                    "redirect_url": redirect_url,
                    "message": "Registration successful. Redirecting to application."
                }
            }
        
        return {
            "status": "success",
            "webhook_response": {
                "status_code": response.status_code,
                "body": response.text,
                "headers": dict(response.headers)
            }
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/send-sns")
async def send_sns(request: Request):
    """发送SNS消息到webhook"""
    try:
        data = await request.json()
        event_type = data.get('eventType')
        details = data.get('details', {})
        
        sns_message = simulator.generate_sns_message(event_type, details)
        
        response = requests.post(
            f"{simulator.webhook_url}/sns",
            json=sns_message
        )
        
        return {
            "status": "success",
            "webhook_response": {
                "status_code": response.status_code,
                "body": response.text
            }
        }
    except Exception as e:
        logger.error(f"SNS error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 