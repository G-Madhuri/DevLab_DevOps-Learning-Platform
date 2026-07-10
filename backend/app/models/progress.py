import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, JSON, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CourseProgress(Base):
    __tablename__ = "course_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    completed_lessons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    current_lesson_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "course_slug", name="uq_user_course"),
    )
