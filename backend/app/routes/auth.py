from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..services.auth import authenticate_user, create_access_token, get_password_hash
from ..models.database import SessionLocal, User
from ..dependencies import get_current_user
from datetime import timedelta
from typing import Dict
from pydantic import BaseModel

router = APIRouter()

# 添加请求体模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register")
async def register(user: UserCreate):
    """用户注册"""
    # 输入验证
    if not user.username or not user.email or not user.password:
        raise HTTPException(
            status_code=400,
            detail="All fields are required"
        )
    
    # 验证邮箱格式
    if "@" not in user.email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email format"
        )
    
    # 验证密码长度
    if len(user.password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )
    
    db = SessionLocal()
    try:
        # 检查用户名是否已存在
        if db.query(User).filter(User.username == user.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
            
        # 检查邮箱是否已存在
        if db.query(User).filter(User.email == user.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
            
        # 创建新用户
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=get_password_hash(user.password)
        )
        db.add(db_user)
        db.commit()
        
        return {"message": "User registered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    finally:
        db.close()

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict:
    """用户登录"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/verify")
async def verify_token(user: User = Depends(get_current_user)):
    """验证token并返回用户信息"""
    return {
        "username": user.username,
        "email": user.email
    }