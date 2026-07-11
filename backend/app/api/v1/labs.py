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
    
    # Batch query all progress records for user
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p for p in progress_records}
    
    response = []
    for academy in academies:
        academy_courses = []
        percentages = []
        
        for course in academy["courses"]:
            progress = progress_map.get(course["slug"])
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
        
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p for p in progress_records}
    
    academy_courses = []
    percentages = []
    
    for course in academy["courses"]:
        progress = progress_map.get(course["slug"])
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
        
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p for p in progress_records}
    
    percentages = []
    for course in academy["courses"]:
        progress = progress_map.get(course["slug"])
        percentages.append(progress.percentage if progress else 0)
        
    certificate_unlocked = all(p == 100 for p in percentages) if percentages else False
    if not certificate_unlocked:
        raise HTTPException(status_code=400, detail="Complete all courses in the academy to unlock certificate.")
        
    return {
        "success": True,
        "message": f"Successfully generated {academy['title']} certificate!",
        "certificate_id": str(uuid.uuid4())
    }

@router.get("/learning-paths/list")
def get_learning_paths_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve list of career-focused roadmaps.
    """
    paths = course_engine.get_learning_paths()
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p for p in progress_records}

    response = []
    for path in paths:
        course_percentages = []
        for slug in path["courses"]:
            p = progress_map.get(slug)
            course_percentages.append(p.percentage if p else 0)
        overall_progress = sum(course_percentages) // len(course_percentages) if course_percentages else 0

        response.append({
            **path,
            "progress": overall_progress
        })
    return response

@router.get("/learning-paths/detail/{path_id}")
def get_learning_path_detail(
    path_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve specific learning path with course statuses.
    """
    path = course_engine.get_learning_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="Learning Path not found.")

    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p for p in progress_records}

    courses_details = []
    course_percentages = []
    for slug in path["courses"]:
        p = progress_map.get(slug)
        percentage = p.percentage if p else 0
        course_percentages.append(percentage)
        
        # Look up course metadata inside academies courses list
        academies = course_engine.get_academies()
        found_course = None
        for a in academies:
            for c in a["courses"]:
                if c["slug"] == slug:
                    found_course = c
                    break
            if found_course:
                break
                
        title = found_course["title"] if found_course else slug.replace("-", " ").title()
        desc = found_course["description"] if found_course else "Learn modular skills and command operations."
        duration = found_course["duration"] if found_course else "30m"
        diff = found_course["difficulty"] if found_course else "beginner"

        courses_details.append({
            "slug": slug,
            "title": title,
            "description": desc,
            "duration": duration,
            "difficulty": diff,
            "percentage": percentage,
            "status": "completed" if percentage == 100 else "in-progress" if percentage > 0 else "not-started"
        })

    overall_progress = sum(course_percentages) // len(course_percentages) if course_percentages else 0

    return {
        **path,
        "progress": overall_progress,
        "courses_details": courses_details
    }
