import json
import logging
import re
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.sub_topic import SubTopic
from app.models.main_topic import MainTopic

logger = logging.getLogger(__name__)

# 핵심 정보 구분자
CORE_CONTENT_SEPARATOR = "\n\n--- 추가 데이터 ---\n\n"
# 메타데이터 패턴: [source_type:text] 형식
METADATA_PATTERN = re.compile(r'^\[source_type:([^\]]+)\]\s*(.*)$', re.DOTALL)


def parse_core_contents(core_content: str | None, source_type: str | None) -> list[dict]:
    """핵심 정보를 구분자로 분리하여 배열로 반환
    
    각 핵심 정보는 다음 형식 중 하나를 지원:
    1. 새 형식: [source_type:text]content (권장)
    2. 기존 형식: content (하위 호환성, 전체 source_type 사용)
    """
    if not core_content or not core_content.strip():
        return []
    
    # 구분자로 분리
    parts = core_content.split(CORE_CONTENT_SEPARATOR)
    
    result = []
    for index, part in enumerate(parts):
        cleaned = part.strip()
        if not cleaned:
            continue
        
        # 메타데이터 패턴 확인 (새 형식)
        match = METADATA_PATTERN.match(cleaned)
        if match:
            # 새 형식: [source_type:text]content
            item_source_type = match.group(1)
            item_content = match.group(2).strip()
            result.append({
                "index": index,
                "core_content": item_content,
                "source_type": item_source_type
            })
        else:
            # 기존 형식: content (하위 호환성)
            result.append({
                "index": index,
                "core_content": cleaned,
                "source_type": source_type or "text"
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


async def get_sub_topics_with_relations(session: AsyncSession) -> Sequence[SubTopic]:
    """모든 세부항목 조회 (관계 포함, ADsP 전용)"""
    result = await session.execute(
        select(SubTopic)
        .join(SubTopic.main_topic)
        .options(joinedload(SubTopic.main_topic).joinedload(MainTopic.subject))
        .where(MainTopic.subject_id == 1)
        .order_by(MainTopic.id, SubTopic.id)
    )
    return result.unique().scalars().all()


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
    """세부항목 핵심 정보 추가 (기존 데이터에 append, 수정/삭제 불가)
    
    각 핵심 정보의 source_type을 개별적으로 저장하기 위해 [source_type:xxx] 형식으로 저장합니다.
    기존 데이터와의 호환성을 위해 기존 형식도 지원합니다.
    """
    sub_topic = await get_sub_topic_by_id(session, sub_topic_id)
    if not sub_topic:
        return None
    
    # 새로운 핵심 정보를 메타데이터 포함 형식으로 구성
    new_item = f"[source_type:{source_type}]{additional_content}"
    
    # 기존 데이터가 있으면 구분자와 함께 추가, 없으면 새로 생성
    if sub_topic.core_content and sub_topic.core_content.strip():
        # 기존 데이터가 새 형식인지 확인
        existing_parts = sub_topic.core_content.split(CORE_CONTENT_SEPARATOR)
        if existing_parts and METADATA_PATTERN.match(existing_parts[0].strip()):
            # 새 형식: 그대로 추가
            sub_topic.core_content = f"{new_item}{CORE_CONTENT_SEPARATOR}{sub_topic.core_content}"
        else:
            # 기존 형식: 첫 번째 항목을 새 형식으로 변환
            converted_parts = []
            for part in existing_parts:
                cleaned = part.strip()
                if cleaned:
                    # 기존 형식이면 메타데이터 추가
                    if not METADATA_PATTERN.match(cleaned):
                        converted_parts.append(f"[source_type:{sub_topic.source_type or 'text'}]{cleaned}")
                    else:
                        converted_parts.append(cleaned)
            
            # 새로운 항목 추가
            sub_topic.core_content = f"{new_item}{CORE_CONTENT_SEPARATOR}{CORE_CONTENT_SEPARATOR.join(converted_parts)}"
    else:
        # 첫 번째 핵심 정보는 메타데이터 포함 형식으로 저장
        sub_topic.core_content = new_item
    
    # source_type은 최신 것으로 업데이트 (하위 호환성 유지)
    sub_topic.source_type = source_type
    await session.commit()
    await session.refresh(sub_topic)
    return sub_topic
