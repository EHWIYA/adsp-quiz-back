import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import sub_topic as sub_topic_crud
from app.models.base import get_db
from app.schemas import sub_topic as sub_topic_schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/core-content", tags=["core-content"])


@router.get("/{sub_topic_id}", response_model=sub_topic_schema.SubTopicCoreContentResponse)
async def get_core_content(
    sub_topic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """세부항목 핵심 정보 조회 API (관리 페이지용, 목록 형식)
    
    관리 페이지에서 등록/수정을 위해 사용되므로, 세부항목이 없어도 빈 값으로 반환합니다.
    핵심 정보는 구분자로 분리되어 배열로 반환됩니다.
    """
    logger.info(f"세부항목 핵심 정보 조회 시작: sub_topic_id={sub_topic_id}")
    
    try:
        sub_topic = await sub_topic_crud.get_sub_topic_with_core_content(db, sub_topic_id)
    except Exception as e:
        logger.error(
            f"세부항목 조회 중 DB 에러: sub_topic_id={sub_topic_id}, "
            f"error={e.__class__.__name__}: {str(e)}",
            exc_info=True
        )
        raise
    
    if not sub_topic:
        logger.warning(f"세부항목을 찾을 수 없음: sub_topic_id={sub_topic_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "detail": f"세부항목을 찾을 수 없습니다: {sub_topic_id}",
            },
        )
    
    # 핵심 정보를 구분자로 분리하여 배열로 변환
    core_contents = sub_topic_crud.parse_core_contents(sub_topic.core_content, sub_topic.source_type)
    
    logger.info(f"세부항목 핵심 정보 조회 완료: sub_topic_id={sub_topic_id}, name={sub_topic.name}, core_contents_count={len(core_contents)}")
    
    # 목록 형식으로 응답 생성
    return sub_topic_schema.SubTopicCoreContentResponse(
        id=sub_topic.id,
        name=sub_topic.name,
        core_contents=[
            sub_topic_schema.CoreContentItem(**item) for item in core_contents
        ],
        updated_at=sub_topic.updated_at
    )
