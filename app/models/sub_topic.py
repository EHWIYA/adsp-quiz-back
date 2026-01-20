from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SubTopic(Base, TimestampMixin):
    __tablename__ = "sub_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    main_topic_id: Mapped[int] = mapped_column(ForeignKey("main_topics.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    core_content: Mapped[str | None] = mapped_column(Text, default=None, comment="핵심 정보 텍스트")
    source_type: Mapped[str | None] = mapped_column(default=None, comment="핵심 정보 소스 타입 (text | youtube_url)")

    main_topic: Mapped["MainTopic"] = relationship("MainTopic", back_populates="sub_topics")
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="sub_topic",
        cascade="all, delete-orphan",
    )
