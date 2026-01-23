import logging
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.sub_topic import SubTopic
from app.models.main_topic import MainTopic

logger = logging.getLogger(__name__)

# 핵심 정보 구분자
CORE_CONTENT_SEPARATOR = "\n\n--- 추가 데이터 ---\n\n"


def parse_core_contents(core_content: str | None, source_type: str | None) -> list[dict]:
    """핵심 정보를 구분자로 분리하여 배열로 반환"""
    if not core_content or not core_content.strip():
        return []
    
    # 구분자로 분리
    parts = core_content.split(CORE_CONTENT_SEPARATOR)
    
    # 각 부분을 정리하여 반환 (앞뒤 공백 제거)
    result = []
    for index, part in enumerate(parts):
        cleaned = part.strip()
        if cleaned:
            result.append({
                "index": index,
                "core_content": cleaned,
                "source_type": source_type or "text"  # source_type이 없으면 기본값 "text"
            })
    
    return result


async def get_sub_topic_by_id(session: AsyncSession, sub_topic_id: int) -> SubTopic | None:
    """ID로 세부항목 조회"""
    result = await session.execute(select(SubTopic).where(SubTopic.id == sub_topic_id))
    return result.scalar_one_or_none()


async def get_sub_topics_by_main_topic_id(session: AsyncSession, main_topic_id: int) -> Sequence[SubTopic]:
    """주요항목 ID로 세부항목 목록 조회"""
    result = await session.execute(
        select(SubTopic)
        .where(SubTopic.main_topic_id == main_topic_id)
        .order_by(SubTopic.id)
    )
    return result.scalars().all()


async def get_sub_topic_with_core_content(session: AsyncSession, sub_topic_id: int) -> SubTopic | None:
    """세부항목 조회 (핵심 정보 및 관계 포함)"""
    logger.debug(f"세부항목 조회: sub_topic_id={sub_topic_id}")
    try:
        result = await session.execute(
            select(SubTopic)
            .where(SubTopic.id == sub_topic_id)
            .options(
                joinedload(SubTopic.main_topic).joinedload(MainTopic.subject)
            )
        )
        sub_topic = result.scalar_one_or_none()
        if sub_topic:
            logger.debug(f"세부항목 조회 성공: sub_topic_id={sub_topic_id}, name={sub_topic.name}")
        else:
            logger.debug(f"세부항목 조회 결과 없음: sub_topic_id={sub_topic_id}")
        return sub_topic
    except Exception as e:
        logger.error(
            f"세부항목 조회 중 예외: sub_topic_id={sub_topic_id}, "
            f"error={e.__class__.__name__}: {str(e)}",
            exc_info=True
        )
        raise


async def update_sub_topic_core_content(
    session: AsyncSession,
    sub_topic_id: int,
    core_content: str,
    source_type: str,
) -> SubTopic | None:
    """세부항목 핵심 정보 업데이트 (기존 방식, 호환성 유지)"""
    sub_topic = await get_sub_topic_by_id(session, sub_topic_id)
    if not sub_topic:
        return None
    
    sub_topic.core_content = core_content
    sub_topic.source_type = source_type
    await session.commit()
    await session.refresh(sub_topic)
    return sub_topic


async def append_sub_topic_core_content(
    session: AsyncSession,
    sub_topic_id: int,
    additional_content: str,
    source_type: str,
) -> SubTopic | None:
    """세부항목 핵심 정보 추가 (기존 데이터에 append, 수정/삭제 불가)"""
    sub_topic = await get_sub_topic_by_id(session, sub_topic_id)
    if not sub_topic:
        return None
    
    # 기존 데이터가 있으면 구분자와 함께 추가, 없으면 새로 생성
    if sub_topic.core_content and sub_topic.core_content.strip():
        # 구분자로 추가 데이터 구분 (역순으로 최신 데이터가 위에 오도록)
        sub_topic.core_content = f"{additional_content}{CORE_CONTENT_SEPARATOR}{sub_topic.core_content}"
    else:
        sub_topic.core_content = additional_content
    
    # source_type은 최신 것으로 업데이트 (여러 타입이 섞일 수 있으므로)
    sub_topic.source_type = source_type
    await session.commit()
    await session.refresh(sub_topic)
    return sub_topic
