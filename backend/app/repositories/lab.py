from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.lab import Lab
from app.repositories.base import BaseRepository


class LabRepository(BaseRepository[Lab]):
    def get_by_slug(self, db: Session, slug: str) -> Optional[Lab]:
        """
        Retrieve a lab by its unique URL slug.
        """
        return db.query(self.model).filter(self.model.slug == slug).first()

    def get_categories(self, db: Session) -> List[str]:
        """
        Retrieve all distinct category strings.
        """
        results = db.query(self.model.category).distinct().all()
        return [r[0] for r in results]

    def get_labs_filtered(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Lab]:
        """
        Query labs with search, filters, sorting, and pagination.
        """
        query = db.query(self.model)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    self.model.title.ilike(search_pattern),
                    self.model.description.ilike(search_pattern),
                    self.model.category.ilike(search_pattern),
                )
            )

        # Apply difficulty filter
        if difficulty:
            query = query.filter(self.model.difficulty == difficulty)

        # Apply category filter
        if category:
            query = query.filter(self.model.category.ilike(category))

        # Apply sorting
        if sort_by == "alphabetical":
            query = query.order_by(self.model.title.asc())
        elif sort_by == "difficulty":
            # Simple sorting: Beginner -> Intermediate -> Advanced (A-Z strings won't do this, so we order by title as fallback or simple sort)
            query = query.order_by(self.model.difficulty.asc())
        elif sort_by == "duration":
            query = query.order_by(self.model.duration.asc())
        else:
            # Default sorting: alphabetical
            query = query.order_by(self.model.title.asc())

        return query.offset(skip).limit(limit).all()


lab_repository = LabRepository(Lab)
