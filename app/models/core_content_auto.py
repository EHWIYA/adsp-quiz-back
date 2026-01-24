from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CoreContentAutoSetting(Base, TimestampMixin):
    __tablename__ = "core_content_auto_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    min_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.3)
    strategy: Mapped[str] = mapped_column(String(30), nullable=False, default="hybrid")
    keyword_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    similarity_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    max_candidates: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    text_preview_length: Mapped[int] = mapped_column(Integer, nullable=False, default=200)


class CoreContentCategoryRule(Base, TimestampMixin):
    __tablename__ = "core_content_category_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    sub_topic_id: Mapped[int] = mapped_column(
        ForeignKey("sub_topics.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CoreContentAutoRun(Base, TimestampMixin):
    __tablename__ = "core_content_auto_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_core_content: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    classification_text_preview: Mapped[str] = mapped_column(Text, nullable=False)
    classification_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    auto_sub_topic_id: Mapped[int | None] = mapped_column(ForeignKey("sub_topics.id"), nullable=True, index=True)
    auto_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_sub_topic_id: Mapped[int | None] = mapped_column(ForeignKey("sub_topics.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    strategy: Mapped[str] = mapped_column(String(30), nullable=False)
    min_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    keyword_weight: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_candidates: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CoreContentAutoCandidate(Base, TimestampMixin):
    __tablename__ = "core_content_auto_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("core_content_auto_runs.id"),
        nullable=False,
        index=True,
    )
    sub_topic_id: Mapped[int] = mapped_column(ForeignKey("sub_topics.id"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    category_path: Mapped[str] = mapped_column(Text, nullable=False)


class CoreContentAutoOverride(Base, TimestampMixin):
    __tablename__ = "core_content_auto_overrides"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(
        ForeignKey("core_content_auto_runs.id"),
        nullable=False,
        index=True,
    )
    auto_sub_topic_id: Mapped[int | None] = mapped_column(ForeignKey("sub_topics.id"), nullable=True)
    final_sub_topic_id: Mapped[int] = mapped_column(ForeignKey("sub_topics.id"), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, default=None)
