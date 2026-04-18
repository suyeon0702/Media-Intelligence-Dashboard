from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from analyzer import generate_draft

router = APIRouter(prefix="/api/draft", tags=["draft"])


class DraftRequest(BaseModel):
    issue_id: int
    direction: str  # 취재 방향 입력


@router.post("")
async def create_draft(request: DraftRequest, db: Session = Depends(get_db)):
    """기사 초안 생성"""
    result = await generate_draft(request.issue_id, request.direction)
    return result