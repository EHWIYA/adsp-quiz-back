import json
import random
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz
from app.models.subject import Subject
from app.schemas.ai import AIQuizGenerationResponse


async def get_quiz_by_id(session: AsyncSession, quiz_id: int) -> Quiz | None:
    """ID로 문제 조회"""
    result = await session.execute(select(Quiz).where(Quiz.id == quiz_id))
    return result.scalar_one_or_none()


async def get_quiz_by_hash(session: AsyncSession, source_hash: str) -> Quiz | None:
    """해시로 중복 문제 확인"""
    result = await session.execute(select(Quiz).where(Quiz.source_hash == source_hash))
    return result.scalar_one_or_none()


async def create_quiz(
    session: AsyncSession,
    subject_id: int,
    ai_response: AIQuizGenerationResponse,
    source_hash: str,
    source_url: str | None = None,
    source_text: str | None = None,
) -> Quiz:
    """문제 생성"""
    quiz = Quiz(
        subject_id=subject_id,
        question=ai_response.question,
        options=ai_response.options_json,
        correct_answer=ai_response.correct_answer,
        explanation=ai_response.explanation,
        source_hash=source_hash,
        source_url=source_url,
        source_text=source_text,
    )
    session.add(quiz)
    await session.commit()
    await session.refresh(quiz)
    return quiz


async def get_random_quizzes(
    session: AsyncSession,
    subject_id: int,
    count: int,
) -> Sequence[Quiz]:
    """과목별 랜덤 문제 추출"""
    stmt = select(Quiz).where(Quiz.subject_id == subject_id)
    result = await session.execute(stmt)
    all_quizzes = result.scalars().all()
    
    if len(all_quizzes) < count:
        return list(all_quizzes)
    
    return random.sample(list(all_quizzes), count)


async def get_subject_by_id(session: AsyncSession, subject_id: int) -> Subject | None:
    """ID로 과목 조회"""
    result = await session.execute(select(Subject).where(Subject.id == subject_id))
    return result.scalar_one_or_none()
