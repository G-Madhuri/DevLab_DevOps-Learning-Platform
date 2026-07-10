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

router = APIRouter()
logger = logging.getLogger("app.api.v1.labs_linux")


@router.post("/launch", response_model=LabSessionResponse)
def launch_lab(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Launch a new Linux basics sandbox container (or starts in Simulated Mode).
    Only allows one active session at a time per user.
    """
    # Check if there is an active session
    active = session_repository.get_running_session_for_user(db, user_id=current_user.id)
    if active:
        return active

    # Insert starting session into database
    session_data = {
        "user_id": current_user.id,
        "lab_name": "linux-basics",
        "status": "starting",
        "container_id": None,
        "started_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=60),
    }
    db_session = session_repository.create(db, obj_in_data=session_data)

    try:
        # Create container
        res = runtime_service.create_lab(str(db_session.id))
        
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
    runtime_service.stop_lab(str(db_session.id), db_session.container_id)

    # Update database
    db_session.status = "stopped"
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/active", response_model=Optional[LabSessionResponse])
def get_active_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the user's currently active running lab.
    """
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
    )
    return res


# ── WebSockets Terminal Streaming ───────────────────────

@router.websocket("/session/{session_id}/ws")
async def websocket_terminal(websocket: WebSocket, session_id: str):
    """
    Main WebSocket router piping stdin keypresses and stdout streams.
    Saves and displays custom banners.
    """
    await websocket.accept()
    logger.info(f"WebSocket terminal connection accepted for session {session_id}")

    # Check simulated shell
    sim_shell = runtime_service.get_session_shell(session_id)

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

            # Stream thread reader from docker container PTY to WebSocket client
            def read_from_docker():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    while True:
                        try:
                            # Read raw bytes from docker shell
                            r_data = socket.recv(4096)
                            if not r_data:
                                break
                            # Decode and forward to client
                            loop.run_until_complete(websocket.send_text(r_data.decode("utf-8", errors="ignore")))
                        except (BlockingIOError, InterruptedError):
                            # Non blocking empty queue
                            pass
                        except Exception:
                            break
                finally:
                    loop.close()

            thread = threading.Thread(target=read_from_docker, daemon=True)
            thread.start()

            # Read websocket keystrokes and pipe to Docker shell
            while True:
                data = await websocket.receive_text()
                # Write directly to container stdin socket
                socket.send(data.encode("utf-8"))

        except Exception as e:
            logger.error(f"WebSocket Docker bridging failed: {e}")
            await websocket.send_text(f"\r\n[System Error] Failed to attach socket: {e}\r\n")
            await websocket.close()
