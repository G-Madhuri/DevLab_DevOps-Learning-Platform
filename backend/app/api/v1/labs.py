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
    academies_data = get_academies_list(db, current_user)
    academies_map = {a["id"]: a for a in academies_data}

    response = []
    for path in paths:
        course_percentages = []
        for slug in path["courses"]:
            academy = academies_map.get(slug)
            course_percentages.append(academy["progress"] if academy else 0)
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

    academies_data = get_academies_list(db, current_user)
    academies_map = {a["id"]: a for a in academies_data}

    courses_details = []
    course_percentages = []
    for slug in path["courses"]:
        academy = academies_map.get(slug)
        percentage = academy["progress"] if academy else 0
        course_percentages.append(percentage)
        
        if academy:
            title = academy["title"]
            desc = academy["description"]
            diff = academy["difficulty"]
            
            # Sum up durations of courses within this technology
            total_mins = 0
            for c in academy["courses"]:
                dur_str = c.get("duration", "30m")
                # Parse digits
                digits = "".join([char for char in dur_str if char.isdigit()])
                if digits:
                    total_mins += int(digits)
            if total_mins >= 60:
                hrs = total_mins // 60
                mins = total_mins % 60
                dur = f"{hrs} hrs {mins} mins" if mins > 0 else f"{hrs} hrs"
            else:
                dur = f"{total_mins} mins"
        else:
            title = slug.replace("-", " ").title()
            desc = "Learn modular skills and command operations."
            dur = "30 mins"
            diff = "beginner"

        courses_details.append({
            "slug": slug,
            "title": title,
            "description": desc,
            "duration": dur,
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


@router.get("/certificates/list")
def get_user_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all unlocked certificates for courses and academies completed by the user.
    """
    import hashlib
    # 1. Fetch all completed courses
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id,
        CourseProgress.percentage == 100
    ).all()
    completed_slugs = {p.course_slug: p.updated_at for p in progress_records}

    # 2. Get academies and courses mapping
    academies = course_engine.get_academies()
    
    certificates = []
    
    # Check individual course completions
    for academy in academies:
        academy_completed_count = 0
        total_academy_courses = len(academy["courses"])
        academy_completed_dates = []

        for course in academy["courses"]:
            if course["slug"] in completed_slugs:
                completed_at = completed_slugs[course["slug"]]
                academy_completed_count += 1
                academy_completed_dates.append(completed_at)
                
                # Dynamic deterministic certificate ID
                cert_id_seed = f"{current_user.id}:{course['slug']}"
                cert_uuid = str(uuid.UUID(hashlib.md5(cert_id_seed.encode()).hexdigest()))
                
                certificates.append({
                    "id": cert_uuid,
                    "type": "course",
                    "title": f"{course['title']} Certification",
                    "recipient_name": current_user.name,
                    "target_title": course["title"],
                    "target_id": course["slug"],
                    "category": academy["title"],
                    "issue_date": completed_at.isoformat() if completed_at else None,
                    "credential_id": cert_uuid[:8].upper()
                })

        # Check academy completion
        if total_academy_courses > 0 and academy_completed_count == total_academy_courses:
            # Academy certificate
            cert_id_seed = f"{current_user.id}:{academy['id']}"
            cert_uuid = str(uuid.UUID(hashlib.md5(cert_id_seed.encode()).hexdigest()))
            latest_date = max(academy_completed_dates) if academy_completed_dates else None
            
            certificates.append({
                "id": cert_uuid,
                "type": "academy",
                "title": f"{academy['title']} Academy Graduate",
                "recipient_name": current_user.name,
                "target_title": f"{academy['title']} Academy",
                "target_id": academy["id"],
                "category": academy["title"],
                "issue_date": latest_date.isoformat() if latest_date else None,
                "credential_id": cert_uuid[:8].upper()
            })
            
    return certificates


@router.post("/courses/{course_slug}/certificate/generate")
def generate_course_certificate(
    course_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate certificate for completing a single course.
    """
    import hashlib
    progress = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id,
        CourseProgress.course_slug == course_slug
    ).first()
    
    if not progress or progress.percentage < 100:
        raise HTTPException(status_code=400, detail="Complete this course to unlock its certificate.")
        
    cert_id_seed = f"{current_user.id}:{course_slug}"
    cert_uuid = str(uuid.UUID(hashlib.md5(cert_id_seed.encode()).hexdigest()))
    
    # Get course title
    academies = course_engine.get_academies()
    course_title = course_slug.replace("-", " ").title()
    category = "DevOps"
    for a in academies:
        for c in a["courses"]:
            if c["slug"] == course_slug:
                course_title = c["title"]
                category = a["title"]
                break
                
    return {
        "success": True,
        "message": f"Successfully generated {course_title} certificate!",
        "certificate": {
            "id": cert_uuid,
            "type": "course",
            "title": f"{course_title} Certification",
            "recipient_name": current_user.name,
            "target_title": course_title,
            "target_id": course_slug,
            "category": category,
            "issue_date": progress.updated_at.isoformat() if progress.updated_at else None,
            "credential_id": cert_uuid[:8].upper()
        }
    }


@router.get("/achievements/list")
def get_user_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all achievements, learning path badges, and daily learning streak milestones.
    """
    from app.services.user import user_service
    import hashlib

    # 1. Fetch user progress records
    progress_records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).all()
    progress_map = {p.course_slug: p.percentage for p in progress_records}

    # 2. Get all learning paths
    paths = course_engine.get_learning_paths()
    path_badges = []
    
    for path in paths:
        path_courses = path.get("courses", [])
        completed_count = 0
        total_count = len(path_courses)
        
        for slug in path_courses:
            if progress_map.get(slug, 0) == 100:
                completed_count += 1
            else:
                # Check if this slug represents an academy (like "monitoring" or "observability")
                academies = course_engine.get_academies()
                academy = next((a for a in academies if a["id"] == slug), None)
                if academy:
                    all_completed = True
                    for c in academy["courses"]:
                        if progress_map.get(c["slug"], 0) < 100:
                            all_completed = False
                            break
                    if all_completed and len(academy["courses"]) > 0:
                        completed_count += 1
                        
        unlocked = (completed_count == total_count) if total_count > 0 else False
        progress_pct = int((completed_count / total_count * 100)) if total_count > 0 else 0
        
        badge_id_seed = f"{current_user.id}:path:{path['id']}"
        badge_uuid = str(uuid.UUID(hashlib.md5(badge_id_seed.encode()).hexdigest()))
        
        path_badges.append({
            "id": badge_uuid,
            "type": "learning_path",
            "target_id": path["id"],
            "title": f"{path['title']} Badge",
            "description": f"Awarded for completing all courses in the {path['title']} learning path.",
            "unlocked": unlocked,
            "progress": progress_pct,
            "completed_count": completed_count,
            "total_count": total_count,
            "icon": "award" if unlocked else "lock",
            "rarity": "Legendary" if unlocked else "Epic" if progress_pct >= 50 else "Common"
        })

    # 3. Calculate streak and generate streak badges
    streak = user_service.calculate_streak(db, current_user.id)
    streak_milestones = [
        {"days": 3, "title": "3-Day Novice Spark", "desc": "Keep the spark alive! Complete labs on 3 consecutive days."},
        {"days": 7, "title": "7-Day Weekly Voyager", "desc": "Voyage on! Learn for 7 consecutive days."},
        {"days": 15, "title": "15-Day Tech Grind", "desc": "Unstoppable! Maintain a 15-day streak of daily learning."},
        {"days": 30, "title": "30-Day Streak Warrior", "desc": "Streak Warrior! Complete labs on 30 consecutive days."},
        {"days": 50, "title": "50-Day DevOps Guru", "desc": "DevOps Guru! Maintain a 50-day learning streak."},
        {"days": 100, "title": "100-Day Centurion Master", "desc": "Centurion Master! Complete labs on 100 consecutive days."},
        {"days": 365, "title": "365-Day Legendary Champion", "desc": "Legendary DevOps Champion! Maintain a full year of daily grinds."}
    ]
    
    streak_badges = []
    for milestone in streak_milestones:
        target = milestone["days"]
        unlocked = streak >= target
        progress_pct = min(100, int(streak / target * 100))
        
        badge_id_seed = f"{current_user.id}:streak:{target}"
        badge_uuid = str(uuid.UUID(hashlib.md5(badge_id_seed.encode()).hexdigest()))
        
        streak_badges.append({
            "id": badge_uuid,
            "type": "streak",
            "target_days": target,
            "title": milestone["title"],
            "description": milestone["desc"],
            "unlocked": unlocked,
            "progress": progress_pct,
            "completed_count": streak,
            "total_count": target,
            "icon": "flame" if unlocked else "lock",
            "rarity": "Legendary" if target >= 100 else "Rare" if target >= 30 else "Common"
        })

    return {
        "streak": streak,
        "badges": path_badges + streak_badges
    }
