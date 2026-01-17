"""Exam CRUD 테스트"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import exam as exam_crud, quiz as quiz_crud
from app.models.quiz import Quiz
from app.models.exam_record import ExamRecord
from app.models.subject import Subject


@pytest.fixture
async def test_subject(test_db_session: AsyncSession):
    """테스트용 과목 생성"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    await test_db_session.refresh(subject)
    return subject


@pytest.fixture
async def test_quiz(test_db_session: AsyncSession, test_subject: Subject):
    """테스트용 문제 생성"""
    quiz = Quiz(
        subject_id=test_subject.id,
        question="테스트 문제",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="test_hash",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    await test_db_session.refresh(quiz)
    return quiz


@pytest.mark.asyncio
async def test_create_exam_record(test_db_session: AsyncSession, test_quiz: Quiz):
    """시험 기록 생성"""
    record = await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=test_quiz.id,
        exam_session_id="session_123",
    )
    
    assert record.id is not None
    assert record.quiz_id == test_quiz.id
    assert record.exam_session_id == "session_123"
    assert record.user_answer is None
    assert record.is_correct is None


@pytest.mark.asyncio
async def test_create_exam_record_with_answer(test_db_session: AsyncSession, test_quiz: Quiz):
    """답안과 함께 시험 기록 생성"""
    record = await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=test_quiz.id,
        exam_session_id="session_123",
        user_answer=0,
    )
    
    assert record.user_answer == 0
    assert record.is_correct is True


@pytest.mark.asyncio
async def test_create_exam_record_invalid_quiz(test_db_session: AsyncSession):
    """존재하지 않는 문제로 기록 생성"""
    with pytest.raises(ValueError, match="문제를 찾을 수 없습니다"):
        await exam_crud.create_exam_record(
            test_db_session,
            quiz_id=999,
            exam_session_id="session_123",
        )


@pytest.mark.asyncio
async def test_get_exam_records_by_session(test_db_session: AsyncSession, test_quiz: Quiz):
    """세션 ID로 기록 조회"""
    session_id = "session_123"
    
    for i in range(3):
        await exam_crud.create_exam_record(
            test_db_session,
            quiz_id=test_quiz.id,
            exam_session_id=session_id,
        )
    
    records = await exam_crud.get_exam_records_by_session(test_db_session, session_id)
    assert len(records) == 3


@pytest.mark.asyncio
async def test_get_exam_record_by_session_and_quiz(
    test_db_session: AsyncSession, test_quiz: Quiz
):
    """세션 ID와 문제 ID로 기록 조회"""
    session_id = "session_123"
    await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=test_quiz.id,
        exam_session_id=session_id,
    )
    
    record = await exam_crud.get_exam_record_by_session_and_quiz(
        test_db_session, session_id, test_quiz.id
    )
    
    assert record is not None
    assert record.quiz_id == test_quiz.id
    assert record.exam_session_id == session_id


@pytest.mark.asyncio
async def test_update_exam_record_answer(test_db_session: AsyncSession, test_quiz: Quiz):
    """시험 기록 답안 업데이트"""
    record = await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=test_quiz.id,
        exam_session_id="session_123",
    )
    
    updated = await exam_crud.update_exam_record_answer(
        test_db_session, record, user_answer=0, is_correct=True
    )
    
    assert updated.user_answer == 0
    assert updated.is_correct is True
