import json
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wrong_answer import WrongAnswer


async def get_wrong_answer_by_quiz_id(
    session: AsyncSession,
    quiz_id: int,
) -> WrongAnswer | None:
    """quiz_id로 오답노트 조회"""
    stmt = select(WrongAnswer).where(WrongAnswer.quiz_id == quiz_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_wrong_answer(
    session: AsyncSession,
    quiz_id: int,
    question: str,
    options: list[str],
    selected_answer: int,
    correct_answer: int,
    explanation: str | None = None,
    subject_id: int | None = None,
    sub_topic_id: int | None = None,
    created_at_original: datetime | None = None,
) -> WrongAnswer:
    """오답노트 생성"""
    options_json = json.dumps(
        [{"index": i, "text": opt} for i, opt in enumerate(options)],
        ensure_ascii=False
    )
    
    wrong_answer = WrongAnswer(
        quiz_id=quiz_id,
        question=question,
        options=options_json,
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        explanation=explanation,
        subject_id=subject_id,
        sub_topic_id=sub_topic_id,
        created_at_original=created_at_original,
    )
    session.add(wrong_answer)
    await session.commit()
    await session.refresh(wrong_answer)
    return wrong_answer


async def update_wrong_answer(
    session: AsyncSession,
    wrong_answer: WrongAnswer,
    selected_answer: int | None = None,
) -> WrongAnswer:
    """오답노트 업데이트 (선택 답안 갱신)"""
    if selected_answer is not None:
        wrong_answer.selected_answer = selected_answer
    await session.commit()
    await session.refresh(wrong_answer)
    return wrong_answer


async def get_wrong_answers(
    session: AsyncSession,
    subject_id: int | None = None,
    sub_topic_id: int | None = None,
    page: int = 1,
    limit: int = 20,
    sort: str = "saved_at",
    order: str = "desc",
) -> tuple[Sequence[WrongAnswer], int]:
    """오답노트 목록 조회 (필터링, 페이지네이션, 정렬)"""
    stmt = select(WrongAnswer)
    
    if subject_id is not None:
        stmt = stmt.where(WrongAnswer.subject_id == subject_id)
    if sub_topic_id is not None:
        stmt = stmt.where(WrongAnswer.sub_topic_id == sub_topic_id)
    
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0
    
    if sort == "created_at":
        sort_column = WrongAnswer.created_at_original
    else:
        sort_column = WrongAnswer.saved_at
    
    if order.lower() == "asc":
        stmt = stmt.order_by(sort_column.asc().nulls_last())
    else:
        stmt = stmt.order_by(sort_column.desc().nulls_last())
    
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all(), total


async def get_wrong_answer_by_id(
    session: AsyncSession,
    wrong_answer_id: int,
) -> WrongAnswer | None:
    """ID로 오답노트 조회"""
    stmt = select(WrongAnswer).where(WrongAnswer.id == wrong_answer_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def delete_wrong_answer(
    session: AsyncSession,
    wrong_answer_id: int,
) -> bool:
    """오답노트 삭제"""
    wrong_answer = await get_wrong_answer_by_id(session, wrong_answer_id)
    if not wrong_answer:
        return False
    await session.delete(wrong_answer)
    await session.commit()
    return True


async def delete_wrong_answers_batch(
    session: AsyncSession,
    ids: list[int],
) -> int:
    """오답노트 일괄 삭제"""
    stmt = select(WrongAnswer).where(WrongAnswer.id.in_(ids))
    result = await session.execute(stmt)
    wrong_answers = result.scalars().all()
    
    for wa in wrong_answers:
        await session.delete(wa)
    
    await session.commit()
    return len(wrong_answers)


async def get_wrong_answer_stats(
    session: AsyncSession,
) -> dict:
    """오답노트 통계 조회"""
    total_stmt = select(func.count()).select_from(WrongAnswer)
    total_result = await session.execute(total_stmt)
    total_count = total_result.scalar() or 0
    
    by_subject_stmt = select(
        WrongAnswer.subject_id,
        func.count().label("count")
    ).group_by(WrongAnswer.subject_id)
    by_subject_result = await session.execute(by_subject_stmt)
    by_subject = {str(row.subject_id): row.count for row in by_subject_result if row.subject_id}
    
    by_sub_topic_stmt = select(
        WrongAnswer.sub_topic_id,
        func.count().label("count")
    ).group_by(WrongAnswer.sub_topic_id)
    by_sub_topic_result = await session.execute(by_sub_topic_stmt)
    by_sub_topic = {str(row.sub_topic_id): row.count for row in by_sub_topic_result if row.sub_topic_id}
    
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_stmt = select(func.count()).select_from(WrongAnswer).where(
        WrongAnswer.saved_at >= seven_days_ago
    )
    recent_result = await session.execute(recent_stmt)
    recent_count = recent_result.scalar() or 0
    
    return {
        "total_count": total_count,
        "by_subject": by_subject,
        "by_sub_topic": by_sub_topic,
        "recent_count": recent_count,
    }
