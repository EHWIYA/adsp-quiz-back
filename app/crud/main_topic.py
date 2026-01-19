from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.main_topic import MainTopic


async def get_main_topic_by_id(session: AsyncSession, main_topic_id: int) -> MainTopic | None:
    """ID로 주요항목 조회"""
    result = await session.execute(select(MainTopic).where(MainTopic.id == main_topic_id))
    return result.scalar_one_or_none()


async def get_main_topics_by_subject_id(session: AsyncSession, subject_id: int) -> Sequence[MainTopic]:
    """과목 ID로 주요항목 목록 조회"""
    result = await session.execute(
        select(MainTopic)
        .where(MainTopic.subject_id == subject_id)
        .order_by(MainTopic.id)
    )
    return result.scalars().all()
