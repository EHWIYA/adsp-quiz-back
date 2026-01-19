from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class MainTopic(Base, TimestampMixin):
    __tablename__ = "main_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(default=None)

    subject: Mapped["Subject"] = relationship("Subject", back_populates="main_topics")
    sub_topics: Mapped[list["SubTopic"]] = relationship(
        "SubTopic",
        back_populates="main_topic",
        cascade="all, delete-orphan",
    )
