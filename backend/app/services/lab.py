from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.lab import Lab
from app.repositories.lab import lab_repository


class LabService:
    def list_labs(
        self,
        db: Session,
        *,
        search: Optional[str] = None,
        difficulty: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """
        List all labs with pagination, filtering, sorting, and search count.
        """
        labs = lab_repository.get_labs_filtered(
            db,
            search=search,
            difficulty=difficulty,
            category=category,
            sort_by=sort_by,
            skip=skip,
            limit=limit,
        )
        # Fetch total count for pagination
        total = len(
            lab_repository.get_labs_filtered(
                db,
                search=search,
                difficulty=difficulty,
                category=category,
                sort_by=sort_by,
                limit=1000,  # Max limit to get count
            )
        )
        return {"labs": labs, "total": total}

    def get_lab_by_slug(self, db: Session, slug: str) -> Lab:
        """
        Fetch a single lab by slug, raising 404 if not found.
        """
        lab = lab_repository.get_by_slug(db, slug=slug)
        if not lab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lab with slug '{slug}' not found.",
            )
        return lab

    def get_categories(self, db: Session) -> List[str]:
        """
        Fetch distinct categories.
        """
        return lab_repository.get_categories(db)


lab_service = LabService()
