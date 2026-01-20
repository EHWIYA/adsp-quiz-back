from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sub_topic import SubTopic


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
    """세부항목 조회 (핵심 정보 포함)"""
    return await get_sub_topic_by_id(session, sub_topic_id)


async def update_sub_topic_core_content(
    session: AsyncSession,
    sub_topic_id: int,
    core_content: str,
) -> SubTopic | None:
    """세부항목 핵심 정보 업데이트"""
    sub_topic = await get_sub_topic_by_id(session, sub_topic_id)
    if not sub_topic:
        return None
    
    sub_topic.core_content = core_content
    await session.commit()
    await session.refresh(sub_topic)
    return sub_topic
