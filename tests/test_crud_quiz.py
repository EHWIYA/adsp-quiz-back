"""Quiz CRUD 테스트"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import quiz as quiz_crud
from app.models.quiz import Quiz
from app.models.subject import Subject
from app.schemas.ai import AIQuizGenerationResponse, AIQuizOption


@pytest.fixture
async def test_subject(test_db_session: AsyncSession):
    """테스트용 과목 생성"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    await test_db_session.refresh(subject)
    return subject


@pytest.mark.asyncio
async def test_get_quiz_by_id(test_db_session: AsyncSession, test_subject: Subject):
    """ID로 문제 조회"""
    quiz = Quiz(
        subject_id=test_subject.id,
        question="테스트 문제",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="test_hash",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
    result = await quiz_crud.get_quiz_by_id(test_db_session, quiz.id)
    assert result is not None
    assert result.id == quiz.id
    assert result.question == "테스트 문제"


@pytest.mark.asyncio
async def test_get_quiz_by_id_not_found(test_db_session: AsyncSession):
    """존재하지 않는 ID로 조회"""
    result = await quiz_crud.get_quiz_by_id(test_db_session, 999)
    assert result is None


@pytest.mark.asyncio
async def test_get_quiz_by_hash(test_db_session: AsyncSession, test_subject: Subject):
    """해시로 문제 조회"""
    source_hash = "test_hash_123"
    quiz = Quiz(
        subject_id=test_subject.id,
        question="테스트 문제",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash=source_hash,
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
    result = await quiz_crud.get_quiz_by_hash(test_db_session, source_hash)
    assert result is not None
    assert result.source_hash == source_hash


@pytest.mark.asyncio
async def test_create_quiz(test_db_session: AsyncSession, test_subject: Subject):
    """문제 생성"""
    ai_response = AIQuizGenerationResponse(
        question="새 문제",
        options=[
            AIQuizOption(index=0, text="선택지1"),
            AIQuizOption(index=1, text="선택지2"),
            AIQuizOption(index=2, text="선택지3"),
            AIQuizOption(index=3, text="선택지4"),
        ],
        correct_answer=1,
        explanation="설명",
    )
    
    quiz = await quiz_crud.create_quiz(
        test_db_session,
        subject_id=test_subject.id,
        ai_response=ai_response,
        source_hash="new_hash",
    )
    
    assert quiz.id is not None
    assert quiz.question == "새 문제"
    assert quiz.correct_answer == 1


@pytest.mark.asyncio
async def test_get_random_quizzes(test_db_session: AsyncSession, test_subject: Subject):
    """랜덤 문제 추출"""
    for i in range(5):
        quiz = Quiz(
            subject_id=test_subject.id,
            question=f"문제 {i}",
            options='[{"index": 0, "text": "선택지1"}]',
            correct_answer=0,
            source_hash=f"hash_{i}",
        )
        test_db_session.add(quiz)
    await test_db_session.commit()
    
    result = await quiz_crud.get_random_quizzes(test_db_session, test_subject.id, 3)
    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_random_quizzes_insufficient(test_db_session: AsyncSession, test_subject: Subject):
    """요청 개수보다 적은 경우"""
    quiz = Quiz(
        subject_id=test_subject.id,
        question="문제 1",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="hash_1",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
    result = await quiz_crud.get_random_quizzes(test_db_session, test_subject.id, 5)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_get_subject_by_id(test_db_session: AsyncSession, test_subject: Subject):
    """과목 조회"""
    result = await quiz_crud.get_subject_by_id(test_db_session, test_subject.id)
    assert result is not None
    assert result.id == test_subject.id
