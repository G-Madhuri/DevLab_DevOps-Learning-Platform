from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.schemas.lab import LabListResponse, LabResponse
from app.services.lab import lab_service

router = APIRouter()


@router.get("", response_model=LabListResponse)
def get_labs(
    search: Optional[str] = Query(None, description="Search by title, description, or category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Beginner, Intermediate, Advanced)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort_by: Optional[str] = Query(None, description="Sort by alphabetical, difficulty, duration"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all labs with optional search query, difficulty/category filters, sorting, and pagination.
    """
    return lab_service.list_labs(
        db,
        search=search,
        difficulty=difficulty,
        category=category,
        sort_by=sort_by,
        skip=skip,
        limit=limit,
    )


@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """
    Get a list of all distinct lab categories.
    """
    return lab_service.get_categories(db)


@router.get("/{slug}", response_model=LabResponse)
def get_lab_by_slug(slug: str, db: Session = Depends(get_db)):
    """
    Get a single lab detail by its unique slug.
    """
    return lab_service.get_lab_by_slug(db, slug=slug)
