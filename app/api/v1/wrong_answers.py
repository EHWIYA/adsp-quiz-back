from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import wrong_answer as wrong_answer_crud
from app.models.base import get_db
from app.schemas import wrong_answer as wrong_answer_schema

router = APIRouter(prefix="/wrong-answers", tags=["wrong-answers"])


@router.post("", response_model=wrong_answer_schema.WrongAnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_wrong_answer(
    request: wrong_answer_schema.WrongAnswerCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """오답 저장 API (동일 quiz_id가 있으면 기존 데이터 반환)"""
    existing = await wrong_answer_crud.get_wrong_answer_by_quiz_id(db, request.quiz_id)
    
    if existing:
        return wrong_answer_schema.WrongAnswerResponse.model_validate(existing)
    
    created_at_original = None
    if request.created_at:
        try:
            created_at_original = datetime.fromisoformat(request.created_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass
    
    wrong_answer = await wrong_answer_crud.create_wrong_answer(
        db,
        quiz_id=request.quiz_id,
        question=request.question,
        options=request.options,
        selected_answer=request.selected_answer,
        correct_answer=request.correct_answer,
        explanation=request.explanation,
        subject_id=request.subject_id,
        sub_topic_id=request.sub_topic_id,
        created_at_original=created_at_original,
    )
    
    return wrong_answer_schema.WrongAnswerResponse.model_validate(wrong_answer)


@router.get("", response_model=wrong_answer_schema.WrongAnswerListResponse)
async def get_wrong_answers(
    subject_id: int | None = Query(None, description="과목 ID로 필터링"),
    sub_topic_id: int | None = Query(None, description="세부항목 ID로 필터링"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    sort: str = Query("saved_at", description="정렬 기준 (created_at 또는 saved_at)"),
    order: str = Query("desc", description="정렬 순서 (asc 또는 desc)"),
    db: AsyncSession = Depends(get_db),
):
    """오답노트 조회 API (필터링, 페이지네이션, 정렬)"""
    if sort not in ("created_at", "saved_at"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort는 'created_at' 또는 'saved_at'이어야 합니다",
        )
    
    if order not in ("asc", "desc"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order는 'asc' 또는 'desc'이어야 합니다",
        )
    
    wrong_answers, total = await wrong_answer_crud.get_wrong_answers(
        db,
        subject_id=subject_id,
        sub_topic_id=sub_topic_id,
        page=page,
        limit=limit,
        sort=sort,
        order=order,
    )
    
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    return wrong_answer_schema.WrongAnswerListResponse(
        wrong_answers=[
            wrong_answer_schema.WrongAnswerResponse.model_validate(wa) for wa in wrong_answers
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.delete("/{wrong_answer_id}", response_model=wrong_answer_schema.WrongAnswerDeleteResponse)
async def delete_wrong_answer(
    wrong_answer_id: int,
    db: AsyncSession = Depends(get_db),
):
    """오답 삭제 API"""
    deleted = await wrong_answer_crud.delete_wrong_answer(db, wrong_answer_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 ID의 오답노트 항목이 존재하지 않습니다",
        )
    
    return wrong_answer_schema.WrongAnswerDeleteResponse(
        message="오답노트 항목이 삭제되었습니다.",
        id=wrong_answer_id,
    )


@router.delete("", response_model=wrong_answer_schema.WrongAnswerBatchDeleteResponse)
async def delete_wrong_answers_batch(
    request: wrong_answer_schema.WrongAnswerBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """오답 일괄 삭제 API"""
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ids 필드는 비어있을 수 없습니다",
        )
    
    deleted_count = await wrong_answer_crud.delete_wrong_answers_batch(db, request.ids)
    
    return wrong_answer_schema.WrongAnswerBatchDeleteResponse(
        message=f"{deleted_count}개의 오답노트 항목이 삭제되었습니다.",
        deleted_count=deleted_count,
    )


@router.get("/stats", response_model=wrong_answer_schema.WrongAnswerStatsResponse)
async def get_wrong_answer_stats(
    db: AsyncSession = Depends(get_db),
):
    """오답노트 통계 API"""
    stats = await wrong_answer_crud.get_wrong_answer_stats(db)
    return wrong_answer_schema.WrongAnswerStatsResponse.model_validate(stats)
