from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List
from ..models.database import SessionLocal, APIUsage, User
from ..dependencies import oauth2_scheme, get_current_user
from datetime import datetime, timedelta
from sqlalchemy import func

router = APIRouter()

@router.get("/usage")
async def get_usage_stats(
    days: int = 30,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """获取API使用统计"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查询使用记录
        usage_records = db.query(
            func.sum(APIUsage.input_chars).label("total_input"),
            func.sum(APIUsage.output_chars).label("total_output"),
            func.sum(APIUsage.cost).label("total_cost")
        ).filter(
            APIUsage.user_id == user.id,
            APIUsage.created_at.between(start_date, end_date)
        ).first()
        
        # 查询剩余配额
        remaining_quota = user.api_quota
        
        return {
            "period": f"Last {days} days",
            "total_input_chars": usage_records.total_input or 0,
            "total_output_chars": usage_records.total_output or 0,
            "total_cost_usd": float(usage_records.total_cost or 0),
            "remaining_quota": remaining_quota
        }
    finally:
        db.close()

@router.get("/history")
async def get_usage_history(
    days: int = 30,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """获取API使用历史"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        # 计算时间范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # 查询使用记录
        usage_records = db.query(APIUsage).filter(
            APIUsage.user_id == user.id,
            APIUsage.created_at.between(start_date, end_date)
        ).order_by(APIUsage.created_at.desc()).all()
        
        return [{
            "timestamp": record.created_at,
            "api_name": record.api_name,
            "input_chars": record.input_chars,
            "output_chars": record.output_chars,
            "cost_usd": float(record.cost)
        } for record in usage_records]
    finally:
        db.close()

@router.post("/add-quota")
async def add_quota(
    amount: int,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """增加API使用配额"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        user.api_quota += amount
        db.commit()
        return {
            "message": f"Successfully added {amount} quota",
            "current_quota": user.api_quota
        }
    finally:
        db.close()

@router.get("/check-quota")
async def check_quota(
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """检查当前配额"""
    user = await get_current_user(token)
    return {
        "current_quota": user.api_quota
    } 