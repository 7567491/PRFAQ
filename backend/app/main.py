from fastapi import FastAPI
from app.models.database import engine, Base
from app.models.migrations import run_migrations
from app.routes import auth, prfaq, billing
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化数据库
logger.info("正在初始化数据库...")
run_migrations()
logger.info("数据库初始化完成")

# 创建FastAPI应用
app = FastAPI(title="PRFAQ Pro API")

# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(prfaq.router, prefix="/prfaq", tags=["prfaq"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])

@app.get("/")
async def root():
    return {"message": "PRFAQ Pro API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 