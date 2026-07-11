import asyncio
import json
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.repositories.session import session_repository
from app.schemas.session import (
    LabSessionListResponse,
    LabSessionResponse,
    TaskValidationRequest,
    TaskValidationResponse,
)
from app.services.runtime import runtime_service
from app.services.validation import validation_engine
from app.models.progress import CourseProgress
from app.courses.engine import course_engine

router = APIRouter()
logger = logging.getLogger("app.api.v1.labs_linux")


@router.post("/launch", response_model=LabSessionResponse)
def launch_lab(
    lab_name: str = Query("linux-basics"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Launch a new Linux basics sandbox container (or starts in Simulated Mode).
    Only allows one active session at a time per user.
    """
    # Check if there is an active session for this specific lab
    active = session_repository.get_active_session(db, user_id=current_user.id, lab_name=lab_name)
    if active:
        return active


    # Insert starting session into database
    session_data = {
        "user_id": current_user.id,
        "lab_name": lab_name,
        "status": "starting",
        "container_id": None,
        "started_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=60),
    }
    db_session = session_repository.create(db, obj_in_data=session_data)

    try:
        # Create container
        res = runtime_service.create_lab(str(db_session.id), db_session.lab_name)
        
        # Update session
        db_session.container_id = res["container_id"]
        db_session.status = "running"
        db_session.started_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db_session.status = "stopped"
        db.commit()
        logger.error(f"Failed to launch container: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to launch sandbox container: {e}",
        )


@router.post("/{session_id}/stop", response_model=LabSessionResponse)
def stop_lab(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stops and destroys the running lab container.
    """
    db_session = session_repository.get(db, id=session_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lab session not found.")

    # Cleanup runtime
    runtime_service.stop_lab(str(db_session.id), db_session.container_id, db_session.lab_name)

    # Update database
    db_session.status = "stopped"
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/active", response_model=Optional[LabSessionResponse])
def get_active_session(
    lab_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the user's currently active running lab.
    """
    if lab_name:
        return session_repository.get_active_session(db, user_id=current_user.id, lab_name=lab_name)
    return session_repository.get_running_session_for_user(db, user_id=current_user.id)


@router.get("/sessions", response_model=LabSessionListResponse)
def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user lab sessions log.
    """
    sessions = session_repository.get_user_sessions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    total = len(sessions)
    return {"sessions": sessions, "total": total}


@router.get("/{session_id}/status", response_model=LabSessionResponse)
def get_lab_status(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve status details of a specific lab.
    """
    db_session = session_repository.get(db, id=session_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lab session not found.")
    return db_session


@router.post("/{session_id}/validate", response_model=TaskValidationResponse)
def validate_lab_task(
    session_id: uuid.UUID,
    req: TaskValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validates whether the user completed a specific exercise step.
    """
    db_session = session_repository.get(db, id=session_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Lab session not found.")

    if db_session.status != "running":
        return {"success": False, "message": "Sandbox container is not active."}

    # Evaluate validation challenge
    mode = "simulated" if (db_session.container_id and db_session.container_id.startswith("simulated-")) else "docker"
    res = validation_engine.validate_task(
        session_id=str(db_session.id),
        container_id=db_session.container_id,
        task_id=req.task_id,
        mode=mode,
        lab_name=db_session.lab_name,
    )

    # Auto-update progress on successful check
    if res.get("success") is True:
        course_slug = db_session.lab_name
        progress = db.query(CourseProgress).filter(
            CourseProgress.user_id == current_user.id,
            CourseProgress.course_slug == course_slug
        ).first()

        if not progress:
            progress = CourseProgress(
                user_id=current_user.id,
                course_slug=course_slug,
                completed_lessons=[],
                current_lesson_id=1,
                percentage=0
            )
            db.add(progress)
            db.flush()

        completed = list(progress.completed_lessons)
        if req.task_id not in completed:
            completed.append(req.task_id)
            progress.completed_lessons = completed

        # Calculate progress percentage dynamically
        total_lessons = len(course_engine.get_lessons(course_slug))
        if total_lessons > 0:
            progress.percentage = int(len(completed) / total_lessons * 100)

        # Set next pointer
        if req.task_id + 1 <= total_lessons:
            progress.current_lesson_id = max(progress.current_lesson_id, req.task_id + 1)

        db.commit()

    return res


@router.get("/{course_slug}/lessons")
def get_course_lessons(
    course_slug: str,
    current_user: User = Depends(get_current_user),
):
    """
    Query lessons lists dynamically from config directories.
    """
    lessons = course_engine.get_lessons(course_slug)
    if not lessons:
        raise HTTPException(status_code=404, detail="Course lessons not found.")
    return lessons


@router.get("/{course_slug}/progress")
def get_course_progress(
    course_slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve progress tracker statistics details for a user course.
    """
    progress = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id,
        CourseProgress.course_slug == course_slug
    ).first()

    if not progress:
        return {
            "course_slug": course_slug,
            "completed_lessons": [],
            "current_lesson_id": 1,
            "percentage": 0
        }
    return progress



# ── WebSockets Terminal Streaming ───────────────────────

@router.websocket("/session/{session_id}/ws")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    """
    Main WebSocket router piping stdin keypresses and stdout streams.
    Saves and displays custom banners.
    """
    await websocket.accept()
    logger.info(f"WebSocket terminal connection accepted for session {session_id}")

    # Check session mode dynamically from db to handle server restarts
    from app.db.session import SessionLocal
    lab_name = None
    container_id = None
    try:
        with SessionLocal() as db:
            db_sess = session_repository.get(db, id=uuid.UUID(session_id))
            if db_sess:
                lab_name = db_sess.lab_name
                container_id = db_sess.container_id
    except Exception as e:
        logger.error(f"Failed to query session details: {e}")

    # Check simulated shell
    sim_shell = None
    if container_id and container_id.startswith("simulated-"):
        sim_shell = runtime_service.get_session_shell(session_id, lab_name)
    
    # Fallback: if Docker is unavailable, always provide a simulated shell
    if not sim_shell and (not runtime_service.is_docker_available or not runtime_service.docker_client):
        sim_shell = runtime_service.get_session_shell(session_id, lab_name or "docker-basics")
        logger.info(f"Docker unavailable — falling back to simulated shell for session {session_id}")

    # Welcome Banner
    banner = (
        "\r\n"
        "Welcome to Ubuntu 24.04 LTS (GNU/Linux 6.8.0-1002-aws x86_64)\r\n"
        " * Documentation:  https://help.ubuntu.com\r\n"
        " * Management:     https://landscape.canonical.com\r\n"
        " * Support:        https://ubuntu.com/pro\r\n"
        "\r\n"
        "student@devlab:~$ "
    )
    await websocket.send_text(banner)

    if sim_shell:
        # Simulated Shell Terminal Input/Output buffer loop
        cmd_buffer = []
        try:
            while True:
                data = await websocket.receive_text()
                
                # Handle inputs
                for char in data:
                    if char == "\r" or char == "\n":
                        # Hit Enter: Execute command
                        cmd = "".join(cmd_buffer)
                        cmd_buffer = []
                        await websocket.send_text("\r\n")
                        
                        # Exec command
                        response = sim_shell.execute_command(cmd)
                        await websocket.send_text(response)
                    elif char == "\x7f" or char == "\b":
                        # Backspace keypress
                        if cmd_buffer:
                            cmd_buffer.pop()
                            await websocket.send_text("\b \b") # Move back, write space to erase, move back
                    elif char == "\x03":
                        # Ctrl+C
                        cmd_buffer = []
                        await websocket.send_text("^C\r\nstudent@devlab:~" + sim_shell.cwd.replace('/home/student', '') + "$ ")
                    elif char.isprintable():
                        cmd_buffer.append(char)
                        await websocket.send_text(char)
        except WebSocketDisconnect:
            logger.info(f"WebSocket client disconnected from simulated session {session_id}")
    else:
        # Real Docker Socket attachments
        if not runtime_service.is_docker_available or not runtime_service.docker_client:
            await websocket.send_text("\r\n[Error] Docker Sandbox and simulated fallback not available.\r\n")
            await websocket.close()
            return

        try:
            client = runtime_service.docker_client
            container = client.containers.get(f"devlab-sandbox-{session_id}")
            
            # Start bash session inside container
            exec_inst = client.api.exec_create(
                container.id,
                cmd="/bin/bash",
                stdin=True,
                stdout=True,
                stderr=True,
                tty=True,
                user="student",
                environment={"HOME": "/home/student", "USER": "student"}
            )
            socket = client.api.exec_start(exec_inst["Id"], socket=True)
            socket._sock.setblocking(False)

            # Stream reader from docker container PTY to WebSocket client
            async def read_from_docker():
                try:
                    while True:
                        try:
                            # Read raw bytes from docker shell
                            r_data = socket.recv(4096)
                            if not r_data:
                                break
                            # Decode and forward to client
                            await websocket.send_text(r_data.decode("utf-8", errors="ignore"))
                        except (BlockingIOError, InterruptedError):
                            # Non blocking empty queue, yield to main loop
                            await asyncio.sleep(0.01)
                        except Exception:
                            break
                except Exception as e:
                    logger.error(f"Error in read_from_docker: {e}")

            read_task = asyncio.create_task(read_from_docker())

            # Read websocket keystrokes and pipe to Docker shell
            try:
                while True:
                    data = await websocket.receive_text()
                    # Write directly to container stdin socket
                    socket.send(data.encode("utf-8"))
            finally:
                read_task.cancel()

        except Exception as e:
            logger.error(f"WebSocket Docker bridging failed: {e}")
            await websocket.send_text(f"\r\n[System Error] Failed to attach socket: {e}\r\n")
            await websocket.close()
