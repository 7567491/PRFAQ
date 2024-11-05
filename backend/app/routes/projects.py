from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
from ..models.database import SessionLocal, Project, User
from ..services.auth import oauth2_scheme, get_current_user
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# 添加请求体模型
class ProjectCreate(BaseModel):
    name: str
    description: str = None

@router.post("/create")
async def create_project(
    project: ProjectCreate,  # 修改这里，使用请求体
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """创建新项目"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        project_db = Project(
            user_id=user.id,
            name=project.name,
            description=project.description
        )
        db.add(project_db)
        db.commit()
        db.refresh(project_db)
        return {
            "id": project_db.id,
            "name": project_db.name,
            "description": project_db.description,
            "created_at": project_db.created_at
        }
    finally:
        db.close()

@router.get("/list")
async def list_projects(token: str = Depends(oauth2_scheme)) -> List[Dict]:
    """获取用户的所有项目"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        projects = db.query(Project).filter(Project.user_id == user.id).all()
        return [{
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at
        } for p in projects]
    finally:
        db.close()

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """获取项目详情"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id
        ).first()
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at
        }
    finally:
        db.close()

@router.put("/{project_id}")
async def update_project(
    project_id: int,
    name: str = None,
    description: str = None,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """更新项目信息"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id
        ).first()
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
        
        if name:
            project.name = name
        if description:
            project.description = description
            
        db.commit()
        db.refresh(project)
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at
        }
    finally:
        db.close()

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """删除项目"""
    user = await get_current_user(token)
    db = SessionLocal()
    try:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id
        ).first()
        if not project:
            raise HTTPException(
                status_code=404,
                detail="Project not found"
            )
            
        db.delete(project)
        db.commit()
        return {"message": "Project deleted successfully"}
    finally:
        db.close() 