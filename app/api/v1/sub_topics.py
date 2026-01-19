from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import main_topic as main_topic_crud, sub_topic as sub_topic_crud
from app.models.base import get_db
from app.schemas import quiz as quiz_schema

router = APIRouter(prefix="/main-topics", tags=["main-topics"])


@router.get("/{main_topic_id}/sub-topics", response_model=quiz_schema.SubTopicListResponse)
async def get_sub_topics(
    main_topic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """세부항목 목록 조회 API"""
    # 주요항목 존재 확인
    main_topic = await main_topic_crud.get_main_topic_by_id(db, main_topic_id)
    if not main_topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"주요항목을 찾을 수 없습니다: {main_topic_id}",
        )
    
    sub_topics = await sub_topic_crud.get_sub_topics_by_main_topic_id(db, main_topic_id)
    sub_topic_responses = [
        quiz_schema.SubTopicResponse.model_validate(st) for st in sub_topics
    ]
    return quiz_schema.SubTopicListResponse(
        sub_topics=sub_topic_responses,
        total=len(sub_topic_responses)
    )
