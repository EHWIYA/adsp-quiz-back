from typing import Iterable, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core_content_auto import (
    CoreContentAutoCandidate,
    CoreContentAutoOverride,
    CoreContentAutoRun,
    CoreContentAutoSetting,
    CoreContentCategoryRule,
)


DEFAULT_SETTINGS = {
    "min_confidence": 0.3,
    "strategy": "hybrid",
    "keyword_weight": 0.5,
    "similarity_weight": 0.5,
    "max_candidates": 3,
    "text_preview_length": 200,
}


async def get_auto_settings(session: AsyncSession) -> CoreContentAutoSetting | None:
    stmt = select(CoreContentAutoSetting).order_by(CoreContentAutoSetting.id.asc())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def ensure_auto_settings(session: AsyncSession) -> CoreContentAutoSetting:
    settings = await get_auto_settings(session)
    if settings:
        return settings
    
    settings = CoreContentAutoSetting(**DEFAULT_SETTINGS)
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings


async def update_auto_settings(
    session: AsyncSession,
    settings: CoreContentAutoSetting,
    update_fields: dict,
) -> CoreContentAutoSetting:
    for key, value in update_fields.items():
        setattr(settings, key, value)
    await session.commit()
    await session.refresh(settings)
    return settings


async def get_category_rules(session: AsyncSession) -> Sequence[CoreContentCategoryRule]:
    stmt = select(CoreContentCategoryRule).order_by(CoreContentCategoryRule.sub_topic_id.asc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def upsert_category_rules(
    session: AsyncSession,
    rules: Iterable[dict],
) -> Sequence[CoreContentCategoryRule]:
    sub_topic_ids = [rule["sub_topic_id"] for rule in rules]
    existing = {}
    if sub_topic_ids:
        stmt = select(CoreContentCategoryRule).where(CoreContentCategoryRule.sub_topic_id.in_(sub_topic_ids))
        result = await session.execute(stmt)
        existing = {rule.sub_topic_id: rule for rule in result.scalars().all()}
    
    updated_rules = []
    for rule_data in rules:
        sub_topic_id = rule_data["sub_topic_id"]
        rule = existing.get(sub_topic_id)
        if rule:
            for key, value in rule_data.items():
                setattr(rule, key, value)
        else:
            rule = CoreContentCategoryRule(**rule_data)
            session.add(rule)
        updated_rules.append(rule)
    
    await session.commit()
    for rule in updated_rules:
        await session.refresh(rule)
    return updated_rules


async def create_auto_run(session: AsyncSession, run: CoreContentAutoRun) -> CoreContentAutoRun:
    session.add(run)
    await session.flush()
    return run


async def create_auto_candidates(
    session: AsyncSession,
    candidates: Iterable[CoreContentAutoCandidate],
) -> None:
    session.add_all(list(candidates))
    await session.flush()


async def finalize_auto_run(
    session: AsyncSession,
    run: CoreContentAutoRun,
    final_sub_topic_id: int | None,
    status: str,
) -> CoreContentAutoRun:
    run.final_sub_topic_id = final_sub_topic_id
    run.status = status
    await session.commit()
    await session.refresh(run)
    return run


async def get_auto_run_by_id(session: AsyncSession, run_id: int) -> CoreContentAutoRun | None:
    stmt = select(CoreContentAutoRun).where(CoreContentAutoRun.id == run_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_candidates_by_run_ids(
    session: AsyncSession,
    run_ids: list[int],
) -> Sequence[CoreContentAutoCandidate]:
    if not run_ids:
        return []
    stmt = select(CoreContentAutoCandidate).where(CoreContentAutoCandidate.run_id.in_(run_ids))
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_pending_runs(
    session: AsyncSession,
    page: int,
    limit: int,
) -> tuple[Sequence[CoreContentAutoRun], int]:
    stmt = select(CoreContentAutoRun).where(CoreContentAutoRun.status == "pending")
    total_stmt = select(func.count()).select_from(CoreContentAutoRun).where(CoreContentAutoRun.status == "pending")
    total_result = await session.execute(total_stmt)
    total = total_result.scalar() or 0
    
    stmt = stmt.order_by(CoreContentAutoRun.created_at.desc())
    stmt = stmt.offset((page - 1) * limit).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all(), total


async def create_override(
    session: AsyncSession,
    run_id: int,
    auto_sub_topic_id: int | None,
    final_sub_topic_id: int,
    reason: str | None = None,
) -> CoreContentAutoOverride:
    override = CoreContentAutoOverride(
        run_id=run_id,
        auto_sub_topic_id=auto_sub_topic_id,
        final_sub_topic_id=final_sub_topic_id,
        reason=reason,
    )
    session.add(override)
    await session.commit()
    await session.refresh(override)
    return override
