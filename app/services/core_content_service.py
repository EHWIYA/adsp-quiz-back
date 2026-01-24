import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import core_content_auto as auto_crud
from app.crud import sub_topic as sub_topic_crud
from app.models.core_content_auto import CoreContentAutoCandidate, CoreContentAutoRun
from app.services import youtube_service
from app.utils.similarity import (
    calculate_question_similarity,
    extract_normalized_words,
    normalize_korean_text,
)

logger = logging.getLogger(__name__)

VALID_STRATEGIES = {"hybrid", "similarity_only", "keyword_only"}


class CoreContentAutoError(Exception):
    """핵심 정보 자동 분류 처리 오류"""

    def __init__(self, code: str, detail: str, status_code: int = 400):
        self.code = code
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _build_category_path(sub_topic) -> str:
    subject_name = (
        sub_topic.main_topic.subject.name
        if sub_topic.main_topic and sub_topic.main_topic.subject
        else "ADsP"
    )
    main_topic_name = sub_topic.main_topic.name if sub_topic.main_topic else "알 수 없음"
    return f"{subject_name} > {main_topic_name} > {sub_topic.name}"


def _build_category_text(sub_topic) -> str:
    subject_name = (
        sub_topic.main_topic.subject.name
        if sub_topic.main_topic and sub_topic.main_topic.subject
        else "ADsP"
    )
    main_topic_name = sub_topic.main_topic.name if sub_topic.main_topic else "알 수 없음"
    description = sub_topic.description or ""
    return f"{subject_name} {main_topic_name} {sub_topic.name} {description}".strip()


def _calculate_keyword_score(content: str, category_text: str) -> float:
    normalized_content = normalize_korean_text(content).lower()
    keywords = {kw.lower() for kw in extract_normalized_words(category_text) if kw}
    if not keywords:
        return 0.0
    keyword_hits = sum(1 for kw in keywords if kw in normalized_content)
    return keyword_hits / len(keywords)


def _calculate_base_score(
    content: str,
    category_text: str,
    strategy: str,
    keyword_weight: float,
    similarity_weight: float,
) -> float:
    similarity_score = calculate_question_similarity(content, category_text)
    keyword_score = _calculate_keyword_score(content, category_text)
    
    if strategy == "similarity_only":
        return similarity_score
    if strategy == "keyword_only":
        return keyword_score
    
    total_weight = (keyword_weight or 0.0) + (similarity_weight or 0.0)
    if total_weight <= 0:
        return similarity_score
    return (
        similarity_score * similarity_weight +
        keyword_score * keyword_weight
    ) / total_weight


def _clamp_score(score: float) -> float:
    return max(0.0, min(1.0, score))


async def auto_assign_core_content(
    session: AsyncSession,
    core_content: str,
    source_type: str,
):
    """핵심 정보 자동 분류 및 저장"""
    content = (core_content or "").strip()
    if not content:
        raise CoreContentAutoError(
            code="EMPTY_CORE_CONTENT",
            detail="core_content는 비어있을 수 없습니다.",
        )
    
    if source_type not in ("text", "youtube_url"):
        raise CoreContentAutoError(
            code="INVALID_SOURCE_TYPE",
            detail="source_type은 'text' 또는 'youtube_url'이어야 합니다.",
        )
    
    classification_text = content
    if source_type == "youtube_url":
        try:
            video_id = youtube_service.extract_video_id(content)
        except ValueError as e:
            raise CoreContentAutoError(
                code="INVALID_YOUTUBE_URL",
                detail=str(e),
            ) from e
        
        try:
            classification_text = await youtube_service.extract_transcript(video_id)
        except ValueError as e:
            raise CoreContentAutoError(
                code="TRANSCRIPT_NOT_FOUND",
                detail=str(e),
            ) from e
    
    if not classification_text or not classification_text.strip():
        raise CoreContentAutoError(
            code="EMPTY_CLASSIFICATION_TEXT",
            detail="분류를 위한 텍스트가 비어있습니다.",
        )
    
    settings = await auto_crud.ensure_auto_settings(session)
    strategy = settings.strategy if settings.strategy in VALID_STRATEGIES else "hybrid"
    if settings.strategy not in VALID_STRATEGIES:
        logger.warning(f"알 수 없는 전략 감지: strategy={settings.strategy} -> hybrid로 대체")
    
    sub_topics = await sub_topic_crud.get_sub_topics_with_relations(session)
    if not sub_topics:
        raise CoreContentAutoError(
            code="CATEGORY_DATA_NOT_FOUND",
            detail="분류 가능한 카테고리가 없습니다.",
            status_code=500,
        )
    
    rules = await auto_crud.get_category_rules(session)
    rule_map = {rule.sub_topic_id: rule for rule in rules if rule.is_active}
    
    candidates = []
    for sub_topic in sub_topics:
        category_text = _build_category_text(sub_topic)
        base_score = _calculate_base_score(
            classification_text,
            category_text,
            strategy,
            settings.keyword_weight,
            settings.similarity_weight,
        )
        rule = rule_map.get(sub_topic.id)
        weight = rule.weight if rule else 1.0
        priority = rule.priority if rule else 0
        score = base_score * weight
        candidates.append({
            "sub_topic": sub_topic,
            "score": score,
            "priority": priority,
        })
    
    if not candidates:
        raise CoreContentAutoError(
            code="CATEGORY_MATCH_FAILED",
            detail="카테고리 분류에 실패했습니다.",
            status_code=500,
        )
    
    candidates.sort(key=lambda item: (item["score"], item["priority"]), reverse=True)
    top_candidate = candidates[0]
    auto_sub_topic = top_candidate["sub_topic"]
    confidence = _clamp_score(top_candidate["score"])
    
    if confidence < 0.05:
        logger.warning(
            f"자동 분류 점수 낮음: sub_topic_id={auto_sub_topic.id}, score={confidence}"
        )
    
    preview_length = max(50, settings.text_preview_length)
    classification_preview = classification_text[:preview_length]
    classification_hash = youtube_service.generate_hash(classification_text)
    
    run = CoreContentAutoRun(
        request_core_content=content,
        source_type=source_type,
        classification_text_preview=classification_preview,
        classification_text_hash=classification_hash,
        auto_sub_topic_id=auto_sub_topic.id if auto_sub_topic else None,
        auto_confidence=confidence,
        status="pending" if confidence < settings.min_confidence else "applied",
        strategy=strategy,
        min_confidence=settings.min_confidence,
        keyword_weight=settings.keyword_weight,
        similarity_weight=settings.similarity_weight,
        max_candidates=settings.max_candidates,
        candidate_count=len(candidates),
    )
    await auto_crud.create_auto_run(session, run)
    
    max_candidates = max(1, settings.max_candidates)
    candidate_models = []
    for idx, candidate in enumerate(candidates[:max_candidates], start=1):
        sub_topic = candidate["sub_topic"]
        candidate_models.append(
            CoreContentAutoCandidate(
                run_id=run.id,
                sub_topic_id=sub_topic.id,
                score=_clamp_score(candidate["score"]),
                rank=idx,
                category_path=_build_category_path(sub_topic),
            )
        )
    await auto_crud.create_auto_candidates(session, candidate_models)
    await session.commit()
    
    updated_sub_topic = None
    category_path = None
    if confidence >= settings.min_confidence:
        try:
            updated_sub_topic = await sub_topic_crud.append_sub_topic_core_content(
                session,
                auto_sub_topic.id,
                content,
                source_type,
            )
            if updated_sub_topic:
                category_path = _build_category_path(auto_sub_topic)
                await auto_crud.finalize_auto_run(
                    session,
                    run,
                    final_sub_topic_id=updated_sub_topic.id,
                    status="applied",
                )
            else:
                raise CoreContentAutoError(
                    code="CORE_CONTENT_UPDATE_FAILED",
                    detail="핵심 정보 저장에 실패했습니다.",
                    status_code=500,
                )
        except Exception as e:
            logger.error(
                f"핵심 정보 저장 실패: run_id={run.id}, error={e.__class__.__name__}",
                exc_info=True,
            )
            await auto_crud.finalize_auto_run(
                session,
                run,
                final_sub_topic_id=None,
                status="failed",
            )
            raise
    
    response_candidates = [
        {
            "sub_topic_id": c.sub_topic_id,
            "category_path": c.category_path,
            "score": c.score,
            "rank": c.rank,
        }
        for c in candidate_models
    ]
    
    return updated_sub_topic, category_path, confidence, response_candidates, run


async def get_auto_settings(session: AsyncSession):
    return await auto_crud.ensure_auto_settings(session)


async def update_auto_settings(
    session: AsyncSession,
    update_fields: dict,
    category_rules: list[dict] | None,
):
    settings = await auto_crud.ensure_auto_settings(session)
    if "strategy" in update_fields and update_fields["strategy"] not in VALID_STRATEGIES:
        raise CoreContentAutoError(
            code="INVALID_STRATEGY",
            detail="strategy는 hybrid, similarity_only, keyword_only 중 하나여야 합니다.",
        )
    if update_fields:
        settings = await auto_crud.update_auto_settings(session, settings, update_fields)
    if category_rules:
        for rule in category_rules:
            sub_topic = await sub_topic_crud.get_sub_topic_by_id(session, rule["sub_topic_id"])
            if not sub_topic:
                raise CoreContentAutoError(
                    code="SUB_TOPIC_NOT_FOUND",
                    detail="세부항목을 찾을 수 없습니다.",
                )
        await auto_crud.upsert_category_rules(session, category_rules)
    return settings


async def get_pending_runs(session: AsyncSession, page: int, limit: int):
    runs, total = await auto_crud.get_pending_runs(session, page, limit)
    run_ids = [run.id for run in runs]
    candidates = await auto_crud.get_candidates_by_run_ids(session, run_ids)
    candidate_map: dict[int, list] = {}
    for candidate in candidates:
        candidate_map.setdefault(candidate.run_id, []).append(candidate)
    return runs, total, candidate_map


async def approve_auto_run(
    session: AsyncSession,
    run_id: int,
    sub_topic_id: int,
    reason: str | None = None,
):
    run = await auto_crud.get_auto_run_by_id(session, run_id)
    if not run:
        raise CoreContentAutoError(
            code="RUN_NOT_FOUND",
            detail="자동 분류 이력이 존재하지 않습니다.",
            status_code=404,
        )
    
    if run.status not in ("pending", "applied", "overridden"):
        raise CoreContentAutoError(
            code="RUN_STATUS_INVALID",
            detail="승인할 수 없는 상태입니다.",
        )
    
    sub_topic = await sub_topic_crud.get_sub_topic_by_id(session, sub_topic_id)
    if not sub_topic:
        raise CoreContentAutoError(
            code="SUB_TOPIC_NOT_FOUND",
            detail="세부항목을 찾을 수 없습니다.",
        )
    
    if run.final_sub_topic_id == sub_topic_id and run.status in ("applied", "overridden"):
        return run
    
    updated_sub_topic = await sub_topic_crud.append_sub_topic_core_content(
        session,
        sub_topic_id,
        run.request_core_content,
        run.source_type,
    )
    if not updated_sub_topic:
        raise CoreContentAutoError(
            code="CORE_CONTENT_UPDATE_FAILED",
            detail="핵심 정보 저장에 실패했습니다.",
            status_code=500,
        )
    
    status = "applied"
    if run.final_sub_topic_id and run.final_sub_topic_id != sub_topic_id:
        status = "overridden"
    
    if run.auto_sub_topic_id != sub_topic_id:
        await auto_crud.create_override(
            session,
            run_id=run.id,
            auto_sub_topic_id=run.auto_sub_topic_id,
            final_sub_topic_id=sub_topic_id,
            reason=reason,
        )
        status = "overridden"
    
    run = await auto_crud.finalize_auto_run(
        session,
        run,
        final_sub_topic_id=sub_topic_id,
        status=status,
    )
    return run


async def reject_auto_run(
    session: AsyncSession,
    run_id: int,
    reason: str | None = None,
):
    run = await auto_crud.get_auto_run_by_id(session, run_id)
    if not run:
        raise CoreContentAutoError(
            code="RUN_NOT_FOUND",
            detail="자동 분류 이력이 존재하지 않습니다.",
            status_code=404,
        )
    
    if run.status != "pending":
        raise CoreContentAutoError(
            code="RUN_STATUS_INVALID",
            detail="거절할 수 없는 상태입니다.",
        )
    
    if reason:
        logger.info(f"자동 분류 거절 사유: run_id={run.id}, reason={reason}")
    
    run = await auto_crud.finalize_auto_run(
        session,
        run,
        final_sub_topic_id=None,
        status="rejected",
    )
    return run
