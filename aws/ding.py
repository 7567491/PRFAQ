from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
import uvicorn
import uuid
import random
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging
import requests

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('marketplace_simulator')

app = FastAPI(title="AWS Marketplace Simulator")
templates = Jinja2Templates(directory="aws/templates")

class MarketplaceSimulator:
    def __init__(self):
        self.product_code = os.getenv('AWS_PRODUCT_CODE')
        self.webhook_url = "http://localhost:8000/mp"
    
    def generate_token(self):
        """生成模拟的注册数据"""
        return {
            "CustomerIdentifier": f"test-{uuid.uuid4().hex[:8]}",
            "CustomerAWSAccountId": ''.join([str(random.randint(0, 9)) for _ in range(12)]),
            "ProductCode": self.product_code,
            "Timestamp": datetime.now(timezone.utc).isoformat(),
            "Signature": f"sim-{uuid.uuid4().hex}"
        }

simulator = MarketplaceSimulator()

@app.post("/api/send-registration")
async def send_registration():
    """发送注册请求到webhook"""
    try:
        token = simulator.generate_token()
        response = requests.post(
            simulator.webhook_url,
            json=token,
            allow_redirects=False
        )
        
        if response.status_code == 302:
            return {
                "status": "success",
                "redirect_url": response.headers.get('Location')
            }
        return {
            "status": "error",
            "message": f"Unexpected response: {response.status_code}"
        }
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 