from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import logging
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('webhook')

app = FastAPI(title="AWS Marketplace Webhook")

@app.post("/mp")
async def handle_marketplace_request(request: Request):
    """处理来自 AWS Marketplace 的注册请求"""
    try:
        # 获取请求数据
        token_data = await request.json()
        
        # 验证基本数据结构
        required_fields = ['CustomerIdentifier', 'CustomerAWSAccountId', 'ProductCode']
        if not all(field in token_data for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required fields")

        # 验证客户ID格式（测试环境要求以test-开头）
        if not token_data['CustomerIdentifier'].startswith('test-'):
            raise HTTPException(status_code=400, detail="Invalid customer identifier format")

        # 构建重定向URL，携带客户信息
        redirect_params = {
            'customer_id': token_data['CustomerIdentifier'],
            'aws_account_id': token_data['CustomerAWSAccountId'],
            'product_code': token_data['ProductCode']
        }
        
        # 重定向到用户注册页面
        registration_url = f"/user/register?{'&'.join(f'{k}={v}' for k, v in redirect_params.items())}"
        logger.info(f"Redirecting to registration: {registration_url}")
        
        return RedirectResponse(
            url=registration_url,
            status_code=302
        )

    except Exception as e:
        logger.error(f"Error processing marketplace request: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 