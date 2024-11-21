from fastapi import FastAPI, Request, HTTPException
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger('webhook')

app = FastAPI()

@app.post("/register")
async def handle_registration(request: Request):
    """
    处理注册请求：
    1. 接收任意token
    2. 生成新的用户信息
    3. 返回app.py可识别的登录URL
    """
    try:
        # 获取表单数据
        form_data = await request.form()
        token = form_data.get("x-amzn-marketplace-token")
        
        logger.info("【收到新的注册请求】")
        logger.info(f"收到的token: {token}")

        # 生成时间戳（用于用户ID和账号ID）
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 生成新用户信息
        mp_username = f"MP_User_{timestamp}"
        aws_account = timestamp
        product_code = os.getenv('AWS_PRODUCT_CODE', 'default_product_code')

        logger.info("【生成新用户信息】")
        logger.info(f"Marketplace用户名: {mp_username}")
        logger.info(f"AWS账号: {aws_account}")
        logger.info(f"产品代码: {product_code}")

        # 构建app.py的登录URL，添加source=aws-mp参数
        streamlit_port = os.getenv('STREAMLIT_PORT', '8501')
        login_url = (
            f"http://localhost:{streamlit_port}/"
            f"?source=aws-mp"
            f"&user={mp_username}"
            f"&account={aws_account}"
            f"&product={product_code}"
        )
        logger.info(f"【生成登录URL】: {login_url}")

        # 返回登录URL
        logger.info("✓ 注册流程完成")
        return {"login_url": login_url}

    except Exception as e:
        logger.error(f"❌ 处理注册请求时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 