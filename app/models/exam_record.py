from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ExamRecord(Base, TimestampMixin):
    __tablename__ = "exam_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id"), nullable=False)
    user_answer: Mapped[int | None] = mapped_column(default=None)
    is_correct: Mapped[bool | None] = mapped_column(default=None)
    exam_session_id: Mapped[str] = mapped_column(nullable=False, index=True)

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="exam_records")
