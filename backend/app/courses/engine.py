import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("app.courses.engine")


class CourseEngine:
    def __init__(self):
        # Base courses directory path
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def get_academies(self) -> List[Dict[str, Any]]:
        """
        Loads and returns the list of all academies and their course structures.
        """
        academies_path = os.path.join(self.base_dir, "academies.json")
        if not os.path.exists(academies_path):
            logger.warning(f"Academies file not found at {academies_path}")
            return []
        try:
            with open(academies_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load academies: {e}")
            return []

    def get_lessons(self, course_slug: str) -> List[Dict[str, Any]]:
        """
        Loads and returns the list of lessons for a specific course slug dynamically.
        """
        # Try new modular path: app/courses/lessons/{course_slug}.json
        json_path = os.path.join(self.base_dir, "lessons", f"{course_slug}.json")
        
        if not os.path.exists(json_path):
            # Fallback to old layout: app/courses/{slug_key}/lessons.json
            slug_key = course_slug.replace("-basics", "")
            json_path = os.path.join(self.base_dir, slug_key, "lessons.json")
        
        if not os.path.exists(json_path):
            logger.warning(f"Lessons configuration for course {course_slug} not found at {json_path}")
            return []
            
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load course lessons JSON: {e}")
            return []

    def get_lesson(self, course_slug: str, lesson_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single lesson details from the course slug.
        """
        lessons = self.get_lessons(course_slug)
        for lesson in lessons:
            if lesson.get("id") == lesson_id:
                return lesson
        return None

    def get_course_metadata(self, course_slug: str) -> Dict[str, Any]:
        """
        Generates course catalog metrics details on the fly.
        """
        lessons = self.get_lessons(course_slug)
        difficulty = "Beginner"
        if "docker" in course_slug:
            difficulty = "Intermediate"
        elif "networking" in course_slug or "capstone" in course_slug:
            difficulty = "Advanced"

        return {
            "slug": course_slug,
            "total_lessons": len(lessons),
            "estimated_time": f"{len(lessons) * 5}m",
            "difficulty": difficulty,
        }


# Global singleton instance
course_engine = CourseEngine()
