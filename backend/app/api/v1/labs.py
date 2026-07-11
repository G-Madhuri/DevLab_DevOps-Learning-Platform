from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
import uuid
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


from app.dependencies.auth import get_current_user
from app.models.user import User
from app.courses.engine import course_engine
from app.models.progress import CourseProgress
from sqlalchemy.orm import Session

@router.get("/academies/list")
def get_academies_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the list of all learning academies along with user course progress.
    """
    academies = course_engine.get_academies()
    
    response = []
    for academy in academies:
        academy_courses = []
        percentages = []
        
        for course in academy["courses"]:
            # Query user progress for this course slug
            progress = db.query(CourseProgress).filter(
                CourseProgress.user_id == current_user.id,
                CourseProgress.course_slug == course["slug"]
            ).first()
            
            percentage = progress.percentage if progress else 0
            completed_lessons = progress.completed_lessons if progress else []
            
            percentages.append(percentage)
            academy_courses.append({
                **course,
                "percentage": percentage,
                "completed_lessons": completed_lessons
            })
            
        academy_percentage = sum(percentages) // len(percentages) if percentages else 0
        certificate_unlocked = all(p == 100 for p in percentages) if percentages else False
        
        response.append({
            "id": academy["id"],
            "title": academy["title"],
            "description": academy["description"],
            "icon": academy["icon"],
            "difficulty": academy["difficulty"],
            "coming_soon": academy["coming_soon"],
            "courses": academy_courses,
            "progress": academy_percentage,
            "certificate_unlocked": certificate_unlocked,
            "certificate_status": "unlocked" if certificate_unlocked else "locked"
        })
        
    return response

@router.get("/academies/detail/{academy_id}")
def get_academy_detail(
    academy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a single academy, including certificate status.
    """
    academies = course_engine.get_academies()
    academy = next((a for a in academies if a["id"] == academy_id), None)
    if not academy:
        raise HTTPException(status_code=404, detail="Academy not found.")
        
    academy_courses = []
    percentages = []
    
    for course in academy["courses"]:
        progress = db.query(CourseProgress).filter(
            CourseProgress.user_id == current_user.id,
            CourseProgress.course_slug == course["slug"]
        ).first()
        
        percentage = progress.percentage if progress else 0
        completed_lessons = progress.completed_lessons if progress else []
        
        percentages.append(percentage)
        academy_courses.append({
            **course,
            "percentage": percentage,
            "completed_lessons": completed_lessons
        })
        
    academy_percentage = sum(percentages) // len(percentages) if percentages else 0
    certificate_unlocked = all(p == 100 for p in percentages) if percentages else False
    
    return {
        "id": academy["id"],
        "title": academy["title"],
        "description": academy["description"],
        "icon": academy["icon"],
        "difficulty": academy["difficulty"],
        "coming_soon": academy["coming_soon"],
        "courses": academy_courses,
        "progress": academy_percentage,
        "certificate_unlocked": certificate_unlocked,
        "certificate_status": "unlocked" if certificate_unlocked else "locked"
    }

@router.post("/academies/detail/{academy_id}/certificate/generate")
def generate_academy_certificate(
    academy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate certificate for completing an academy.
    """
    academies = course_engine.get_academies()
    academy = next((a for a in academies if a["id"] == academy_id), None)
    if not academy:
        raise HTTPException(status_code=404, detail="Academy not found.")
        
    percentages = []
    for course in academy["courses"]:
        progress = db.query(CourseProgress).filter(
            CourseProgress.user_id == current_user.id,
            CourseProgress.course_slug == course["slug"]
        ).first()
        percentages.append(progress.percentage if progress else 0)
        
    certificate_unlocked = all(p == 100 for p in percentages) if percentages else False
    if not certificate_unlocked:
        raise HTTPException(status_code=400, detail="Complete all courses in the academy to unlock certificate.")
        
    return {
        "success": True,
        "message": f"Successfully generated {academy['title']} certificate!",
        "certificate_id": str(uuid.uuid4())
    }
