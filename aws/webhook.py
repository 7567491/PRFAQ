from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
import json
import uuid
from datetime import datetime, timezone
import logging
from pathlib import Path
import portalocker
import os
from dotenv import load_dotenv
import traceback

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('webhook')

app = FastAPI()

class SessionManager:
    def __init__(self):
        self.session_file = Path("./config/mp_session.json")
        self.session_file.parent.mkdir(exist_ok=True)
        if not self.session_file.exists():
            self.session_file.write_text("{}")

    def create_session(self, user_info: dict) -> str:
        """创建新的会话"""
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_info": user_info,
            "status": "pending"
        }
        self.save_session(session_data)
        return session_id

    def save_session(self, session_data: dict) -> None:
        """保存会话信息"""
        try:
            with open(self.session_file, 'r+') as f:
                portalocker.lock(f, portalocker.LOCK_EX)
                try:
                    sessions = json.load(f)
                    sessions[session_data['session_id']] = session_data
                    f.seek(0)
                    json.dump(sessions, f, indent=2)
                    f.truncate()
                finally:
                    portalocker.unlock(f)
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save session")

session_manager = SessionManager()

@app.post("/register")
async def handle_registration(request: Request):
    """处理AWS Marketplace的注册请求"""
    try:
        # 记录收到的请求
        form_data = await request.form()
        logger.info(f"Received registration request with data: {form_data}")
        
        # 获取并解析token
        token_str = form_data.get("x-amzn-marketplace-token")
        if not token_str:
            logger.error("No token provided in request")
            raise HTTPException(status_code=400, detail="Token is required")
            
        logger.info(f"Received token string: {token_str}")
        
        try:
            token_data = json.loads(token_str)
            logger.info(f"Parsed token data: {token_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse token: {str(e)}")
            logger.error(f"Token string: {token_str}")
            raise HTTPException(status_code=400, detail="Invalid token format")

        # 验证token数据
        required_fields = ['customerIdentifier', 'customerAWSAccountId', 'productCode']
        missing_fields = [field for field in required_fields if field not in token_data]
        if missing_fields:
            logger.error(f"Missing required fields in token: {missing_fields}")
            logger.error(f"Token data: {token_data}")
            raise HTTPException(status_code=400, detail=f"Missing required fields: {missing_fields}")

        # 创建会话
        try:
            session_id = session_manager.create_session({
                "CustomerIdentifier": token_data['customerIdentifier'],
                "CustomerAWSAccountId": token_data['customerAWSAccountId'],
                "ProductCode": token_data['productCode'],
                "Entitlements": {"test": "test"}  # 模拟数据
            })
            logger.info(f"Created session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            logger.error(f"Error details: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail="Failed to create session")

        # 重定向到Streamlit应用
        redirect_url = f"http://localhost:8501/?session_id={session_id}"
        logger.info(f"Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url, status_code=303)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in registration: {str(e)}")
        logger.error(f"Error details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 