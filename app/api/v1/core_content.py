import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import sub_topic as sub_topic_crud
from app.models.base import get_db
from app.schemas import core_content_auto as auto_schema
from app.schemas import sub_topic as sub_topic_schema
from app.services import core_content_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/core-content", tags=["core-content"])
admin_router = APIRouter(prefix="/admin/core-content", tags=["admin-core-content"])


@router.get("/{sub_topic_id}", response_model=sub_topic_schema.SubTopicCoreContentResponse)
async def get_core_content(
    sub_topic_id: int,
    db: AsyncSession = Depends(get_db),
):
    """세부항목 핵심 정보 조회 API (관리 페이지용, 목록 형식)
    
    관리 페이지에서 등록/수정을 위해 사용되므로, 세부항목이 없어도 빈 값으로 반환합니다.
    핵심 정보는 구분자로 분리되어 배열로 반환됩니다.
    """
    logger.info(f"세부항목 핵심 정보 조회 시작: sub_topic_id={sub_topic_id}")
    
    try:
        sub_topic = await sub_topic_crud.get_sub_topic_with_core_content(db, sub_topic_id)
    except Exception as e:
        logger.error(
            f"세부항목 조회 중 DB 에러: sub_topic_id={sub_topic_id}, "
            f"error={e.__class__.__name__}: {str(e)}",
            exc_info=True
        )
        raise
    
    if not sub_topic:
        logger.warning(f"세부항목을 찾을 수 없음: sub_topic_id={sub_topic_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "detail": f"세부항목을 찾을 수 없습니다: {sub_topic_id}",
            },
        )
    
    # 핵심 정보를 구분자로 분리하여 배열로 변환
    core_contents = sub_topic_crud.parse_core_contents(sub_topic.core_content, sub_topic.source_type)
    
    logger.info(f"세부항목 핵심 정보 조회 완료: sub_topic_id={sub_topic_id}, name={sub_topic.name}, core_contents_count={len(core_contents)}")
    
    # 목록 형식으로 응답 생성
    return sub_topic_schema.SubTopicCoreContentResponse(
        id=sub_topic.id,
        name=sub_topic.name,
        core_contents=[
            sub_topic_schema.CoreContentItem(**item) for item in core_contents
        ],
        updated_at=sub_topic.updated_at
    )


@admin_router.post("/auto", response_model=auto_schema.CoreContentAutoResponse)
async def auto_core_content(
    request: auto_schema.CoreContentAutoRequest,
    db: AsyncSession = Depends(get_db),
):
    """핵심 정보 자동 분류 및 등록 API (관리자용)"""
    logger.info(f"핵심 정보 자동 분류 요청: source_type={request.source_type}")
    
    try:
        updated_sub_topic, category_path, confidence, candidates, run = (
            await core_content_service.auto_assign_core_content(
                db,
                request.core_content,
                request.source_type,
            )
        )
    except core_content_service.CoreContentAutoError as e:
        log_level = logger.warning if e.status_code < 500 else logger.error
        log_level(
            f"핵심 정보 자동 분류 실패: code={e.code}, detail={e.detail}",
            exc_info=e.status_code >= 500,
        )
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "detail": e.detail,
            },
        )
    except Exception as e:
        logger.error(
            f"핵심 정보 자동 분류 중 예외 발생: error={e.__class__.__name__}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_SERVER_ERROR",
                "detail": "핵심 정보 자동 분류 중 오류가 발생했습니다",
            },
        )
    
    if updated_sub_topic:
        logger.info(
            f"핵심 정보 자동 분류 완료: sub_topic_id={updated_sub_topic.id}, score={confidence}"
        )
    
    return auto_schema.CoreContentAutoResponse(
        id=updated_sub_topic.id if updated_sub_topic else (run.auto_sub_topic_id or 0),
        category_path=category_path,
        confidence=confidence,
        candidates=[
            auto_schema.CoreContentAutoCandidateResponse(**candidate)
            for candidate in candidates
        ],
        updated_at=updated_sub_topic.updated_at if updated_sub_topic else None,
    )


@admin_router.get("/auto/settings", response_model=auto_schema.CoreContentAutoSettingsResponse)
async def get_auto_settings(db: AsyncSession = Depends(get_db)):
    """자동 분류 설정 조회"""
    settings = await core_content_service.get_auto_settings(db)
    return auto_schema.CoreContentAutoSettingsResponse.model_validate(settings)


@admin_router.put("/auto/settings", response_model=auto_schema.CoreContentAutoSettingsResponse)
async def update_auto_settings(
    request: auto_schema.CoreContentAutoSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """자동 분류 설정 업데이트"""
    update_fields = {
        key: value
        for key, value in request.model_dump(exclude={"category_rules"}).items()
        if value is not None
    }
    category_rules = None
    if request.category_rules:
        category_rules = [rule.model_dump() for rule in request.category_rules]
    
    try:
        settings = await core_content_service.update_auto_settings(
            db,
            update_fields,
            category_rules,
        )
    except core_content_service.CoreContentAutoError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "detail": e.detail,
            },
        )
    return auto_schema.CoreContentAutoSettingsResponse.model_validate(settings)


@admin_router.get("/auto/pending", response_model=auto_schema.CoreContentAutoPendingResponse)
async def get_pending_auto_runs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """자동 분류 보류 목록 조회"""
    runs, total, candidate_map = await core_content_service.get_pending_runs(db, page, limit)
    
    items = []
    for run in runs:
        candidates = candidate_map.get(run.id, [])
        items.append(
            auto_schema.CoreContentAutoPendingItem(
                run_id=run.id,
                request_core_content=run.request_core_content,
                source_type=run.source_type,
                classification_text_preview=run.classification_text_preview,
                auto_sub_topic_id=run.auto_sub_topic_id,
                auto_confidence=run.auto_confidence,
                status=run.status,
                created_at=run.created_at,
                candidates=[
                    auto_schema.CoreContentAutoCandidateResponse(
                        sub_topic_id=c.sub_topic_id,
                        category_path=c.category_path,
                        score=c.score,
                        rank=c.rank,
                    )
                    for c in sorted(candidates, key=lambda item: item.rank)
                ],
            )
        )
    
    return auto_schema.CoreContentAutoPendingResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )


@admin_router.post(
    "/auto/{run_id}/approve",
    response_model=auto_schema.CoreContentAutoReviewResponse,
)
async def approve_auto_run(
    run_id: int,
    request: auto_schema.CoreContentAutoReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """자동 분류 승인 및 오버라이드"""
    try:
        run = await core_content_service.approve_auto_run(
            db,
            run_id=run_id,
            sub_topic_id=request.sub_topic_id,
            reason=request.reason,
        )
    except core_content_service.CoreContentAutoError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "detail": e.detail,
            },
        )
    return auto_schema.CoreContentAutoReviewResponse(
        run_id=run.id,
        status=run.status,
        final_sub_topic_id=run.final_sub_topic_id,
        updated_at=run.updated_at,
    )


@admin_router.post(
    "/auto/{run_id}/reject",
    response_model=auto_schema.CoreContentAutoReviewResponse,
)
async def reject_auto_run(
    run_id: int,
    request: auto_schema.CoreContentAutoRejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """자동 분류 거절"""
    try:
        run = await core_content_service.reject_auto_run(
            db,
            run_id=run_id,
            reason=request.reason,
        )
    except core_content_service.CoreContentAutoError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "code": e.code,
                "detail": e.detail,
            },
        )
    return auto_schema.CoreContentAutoReviewResponse(
        run_id=run.id,
        status=run.status,
        final_sub_topic_id=run.final_sub_topic_id,
        updated_at=run.updated_at,
    )
