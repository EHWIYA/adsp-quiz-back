import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import exam as exam_crud, quiz as quiz_crud
from app.models.base import get_db
from app.schemas import quiz as quiz_schema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exam", tags=["exam"])


@router.post("/start", response_model=quiz_schema.QuizListResponse)
async def start_exam(
    request: quiz_schema.ExamStartRequest,
    db: AsyncSession = Depends(get_db),
):
    """시험 시작 API"""
    try:
        subject = await quiz_crud.get_subject_by_id(db, request.subject_id)
        if not subject:
            logger.warning(f"과목을 찾을 수 없습니다: subject_id={request.subject_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"과목을 찾을 수 없습니다: {request.subject_id}",
            )

        quizzes = await quiz_crud.get_random_quizzes(db, request.subject_id, request.quiz_count)
        
        if len(quizzes) < request.quiz_count:
            logger.warning(
                f"문제 개수 부족: 요청={request.quiz_count}, 실제={len(quizzes)}, "
                f"subject_id={request.subject_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"요청한 문제 개수({request.quiz_count})보다 적은 문제가 있습니다. 현재: {len(quizzes)}개",
            )

        exam_session_id = str(uuid.uuid4())

        # 배치로 시험 기록 생성 (트랜잭션 일관성 보장)
        try:
            records = []
            for quiz in quizzes:
                record = await exam_crud.create_exam_record(
                    db,
                    quiz_id=quiz.id,
                    exam_session_id=exam_session_id,
                )
                records.append(record)
            # 모든 기록 생성 후 일괄 커밋
            await db.commit()
            # commit 후 각 record를 refresh하여 id 등 생성된 값 반영
            for record in records:
                await db.refresh(record)
        except ValueError as e:
            logger.error(f"시험 기록 생성 실패: {e}, exam_session_id={exam_session_id}")
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"시험 기록 생성 중 오류가 발생했습니다: {str(e)}",
            )
        except Exception as e:
            logger.error(f"시험 기록 생성 중 예상치 못한 오류: {e}, exam_session_id={exam_session_id}", exc_info=True)
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="시험 시작 중 오류가 발생했습니다",
            )

        quiz_responses = [quiz_schema.QuizResponse.model_validate(q) for q in quizzes]
        for qr in quiz_responses:
            qr.correct_answer = None

        logger.info(f"시험 시작 성공: exam_session_id={exam_session_id}, quiz_count={len(quizzes)}")
        return quiz_schema.QuizListResponse(quizzes=quiz_responses, total=len(quiz_responses))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시험 시작 API 오류: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="시험 시작 중 오류가 발생했습니다",
        )


@router.post("/submit", response_model=quiz_schema.ExamRecordResponse)
async def submit_answer(
    request: quiz_schema.ExamSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """답안 제출 API"""
    quiz = await quiz_crud.get_quiz_by_id(db, request.quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"문제를 찾을 수 없습니다: {request.quiz_id}",
        )

    record = await exam_crud.get_exam_record_by_session_and_quiz(
        db,
        request.exam_session_id,
        request.quiz_id,
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"시험 기록을 찾을 수 없습니다: exam_session_id={request.exam_session_id}, quiz_id={request.quiz_id}",
        )

    if record.user_answer is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 답안이 제출되었습니다",
        )

    record = await exam_crud.update_exam_record_answer(
        db,
        record,
        request.user_answer,
        request.user_answer == quiz.correct_answer,
    )

    return quiz_schema.ExamRecordResponse.model_validate(record)


@router.get("/{exam_session_id}", response_model=quiz_schema.ExamResponse)
async def get_exam_result(
    exam_session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """시험 결과 조회 API"""
    records = await exam_crud.get_exam_records_by_session(db, exam_session_id)
    
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"시험 기록을 찾을 수 없습니다: {exam_session_id}",
        )

    correct_count = sum(1 for r in records if r.is_correct is True)
    incorrect_count = sum(1 for r in records if r.is_correct is False)
    
    record_responses = [quiz_schema.ExamRecordResponse.model_validate(r) for r in records]
    
    first_record = records[0]
    quiz = await quiz_crud.get_quiz_by_id(db, first_record.quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="시험 기록에 연결된 문제를 찾을 수 없습니다",
        )

    return quiz_schema.ExamResponse(
        exam_session_id=exam_session_id,
        subject_id=quiz.subject_id,
        total_questions=len(records),
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        records=record_responses,
        created_at=first_record.created_at,
    )
