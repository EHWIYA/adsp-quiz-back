from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(default=None)

    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    main_topics: Mapped[list["MainTopic"]] = relationship(
        "MainTopic",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
