from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from app.models.session import LabSession
from app.repositories.base import BaseRepository


class LabSessionRepository(BaseRepository[LabSession]):
    def get_active_session(
        self, db: Session, user_id: uuid.UUID, lab_name: str
    ) -> Optional[LabSession]:
        """
        Fetch any currently active/running session for a user and lab.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.lab_name == lab_name,
                self.model.status.in_(["starting", "running"]),
            )
            .first()
        )

    def get_running_session_for_user(self, db: Session, user_id: uuid.UUID) -> Optional[LabSession]:
        """
        Fetch the single running/starting lab session for the user (for dashboard display).
        """
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.status.in_(["starting", "running"]),
            )
            .first()
        )

    def get_user_sessions(
        self, db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[LabSession]:
        """
        List all lab sessions owned by the user.
        """
        return (
            db.query(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


session_repository = LabSessionRepository(LabSession)
