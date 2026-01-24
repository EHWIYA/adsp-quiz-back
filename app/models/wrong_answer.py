from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class WrongAnswer(Base, TimestampMixin):
    __tablename__ = "wrong_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(nullable=False, unique=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[str] = mapped_column(Text, nullable=False)
    selected_answer: Mapped[int] = mapped_column(nullable=False)
    correct_answer: Mapped[int] = mapped_column(nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, default=None)
    subject_id: Mapped[int | None] = mapped_column(ForeignKey("subjects.id"), nullable=True, index=True)
    sub_topic_id: Mapped[int | None] = mapped_column(ForeignKey("sub_topics.id"), nullable=True, index=True)
    created_at_original: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment="원본 문제의 created_at")
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
