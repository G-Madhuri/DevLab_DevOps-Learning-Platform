import uuid
from sqlalchemy import String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Lab(Base):
    __tablename__ = "labs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # Beginner, Intermediate, Advanced
    duration: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "45 minutes"
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # Linux, Docker, etc.
    icon: Mapped[str] = mapped_column(String(50), nullable=False)  # Lucide icon slug
    estimated_time: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "45m"
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Active", "Beta"
    coming_soon: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
