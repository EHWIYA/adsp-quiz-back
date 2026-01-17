"""Exam API 통합 테스트"""
import pytest
from unittest.mock import patch

from app.models.quiz import Quiz
from app.models.subject import Subject
from app.models.exam_record import ExamRecord


@pytest.mark.asyncio
async def test_start_exam(client, test_db_session):
    """시험 시작"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    
    for i in range(5):
        quiz = Quiz(
            subject_id=1,
            question=f"문제 {i}",
            options='[{"index": 0, "text": "선택지1"}]',
            correct_answer=0,
            source_hash=f"hash_{i}",
        )
        test_db_session.add(quiz)
    await test_db_session.commit()
    
        response = client.post(
            "/api/v1/exam/start",
            json={"subject_id": 1, "quiz_count": 3},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["quizzes"]) == 3
        assert data["total"] == 3
        for quiz in data["quizzes"]:
            assert quiz["correct_answer"] is None


@pytest.mark.asyncio
async def test_start_exam_insufficient_quizzes(client, test_db_session):
    """문제 개수 부족"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    
    quiz = Quiz(
        subject_id=1,
        question="문제 1",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="hash_1",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
        response = client.post(
            "/api/v1/exam/start",
            json={"subject_id": 1, "quiz_count": 5},
        )
        
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_answer(client, test_db_session):
    """답안 제출"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    
    quiz = Quiz(
        subject_id=1,
        question="테스트 문제",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="test_hash",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
    from app.crud import exam as exam_crud
    record = await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=quiz.id,
        exam_session_id="session_123",
    )
    await test_db_session.commit()
    
        response = client.post(
            "/api/v1/exam/submit",
            json={
                "exam_session_id": "session_123",
                "quiz_id": quiz.id,
                "user_answer": 0,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_answer"] == 0
        assert data["is_correct"] is True


@pytest.mark.asyncio
async def test_get_exam_result(client, test_db_session):
    """시험 결과 조회"""
    subject = Subject(id=1, name="데이터 분석")
    test_db_session.add(subject)
    await test_db_session.commit()
    
    quiz = Quiz(
        subject_id=1,
        question="테스트 문제",
        options='[{"index": 0, "text": "선택지1"}]',
        correct_answer=0,
        source_hash="test_hash",
    )
    test_db_session.add(quiz)
    await test_db_session.commit()
    
    from app.crud import exam as exam_crud
    record = await exam_crud.create_exam_record(
        test_db_session,
        quiz_id=quiz.id,
        exam_session_id="session_123",
        user_answer=0,
    )
    await test_db_session.commit()
    
        response = client.get("/api/v1/exam/session_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["exam_session_id"] == "session_123"
        assert data["total_questions"] == 1
        assert data["correct_count"] == 1
