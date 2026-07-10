from typing import Optional
from sqlalchemy.orm import Session
from app.models.token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def get_by_token(self, db: Session, token: str) -> Optional[RefreshToken]:
        """
        Fetch a refresh token database entry.
        """
        return db.query(self.model).filter(self.model.token == token).first()

    def revoke_token(self, db: Session, token: str) -> bool:
        """
        Mark a refresh token as revoked.
        """
        db_token = self.get_by_token(db, token)
        if db_token:
            db_token.is_revoked = True
            db.add(db_token)
            db.commit()
            db.refresh(db_token)
            return True
        return False


token_repository = RefreshTokenRepository(RefreshToken)
