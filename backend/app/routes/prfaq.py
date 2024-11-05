from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Dict
from ..models.database import SessionLocal
from ..dependencies import get_current_user, oauth2_scheme
from ..services.generator import PRFAQGenerator
from pydantic import BaseModel

router = APIRouter()

class GenerateRequest(BaseModel):
    type: str
    customer: str
    scenario: str
    demand: str
    pain: str
    company: str
    product: str
    feature: str
    benefit: str

@router.post("/generate")
async def generate_prfaq(
    request: GenerateRequest,
    token: str = Depends(oauth2_scheme)
) -> StreamingResponse:
    """生成PRFAQ内容"""
    user = await get_current_user(token)
    
    async def generate():
        try:
            generator = PRFAQGenerator()
            async for chunk in generator.generate_stream(
                type=request.type,
                customer=request.customer,
                scenario=request.scenario,
                demand=request.demand,
                pain=request.pain,
                company=request.company,
                product=request.product,
                feature=request.feature,
                benefit=request.benefit
            ):
                yield f"data: {chunk}\n\n"
            
            # 记录API使用情况
            total_chars = (
                len(request.customer) + len(request.scenario) + 
                len(request.demand) + len(request.pain) +
                len(request.company) + len(request.product) + 
                len(request.feature) + len(request.benefit)
            )
            await generator.record_usage(user.id, total_chars)
            
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    ) 