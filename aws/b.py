from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from urllib.parse import unquote
import logging
from datetime import datetime
import os
import sys

# 创建 logs 目录
os.makedirs('logs', exist_ok=True)

# 配置日志格式
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 创建 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 创建文件处理器
file_handler = logging.FileHandler(f'logs/b_{datetime.now().strftime("%Y%m%d")}.log')
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# 创建终端处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    print("\n收到GET请求，直接进入主页")
    return RedirectResponse(url="http://amazonsp.com:8501")

@app.post("/mp")
async def marketplace(request: Request):
    try:
        # 获取原始数据
        raw_data = await request.body()
        raw_str = raw_data.decode('utf-8')
        logger.info(f"收到原始数据: {raw_str}")

        try:
            # 尝试 URL 解码
            decoded_data = unquote(raw_str)
            logger.info(f"URL解码后: {decoded_data}")
            
            # 构造JSON格式
            data = {
                "x-amzn-marketplace-token": decoded_data
            }
            
            logger.info("\n处理后的数据如下：")
            logger.info("-" * 50)
            for key, value in data.items():
                logger.info(f"{key}: {value}")
            logger.info("-" * 50)
            
            redirect_url = "http://amazonsp.com:8501"
            logger.info(f"准备重定向到: {redirect_url}")
            return RedirectResponse(
                url=redirect_url,
                status_code=303  # 使用 303 See Other 来处理 POST 重定向
            )
            
        except Exception as e:
            logger.error(f"数据处理错误: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"error": "数据处理错误"}
            )
            
    except Exception as e:
        logger.error(f"发生错误: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误"}
        )

if __name__ == "__main__":
    print("服务器启动在 http://amazonsp.com:80")
    uvicorn.run(app, host="0.0.0.0", port=80) 