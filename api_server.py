"""
API Server module for AI Task Management Agent.
FastAPI backend managing endpoints, CORS, agent routing, file uploads, and latency monitoring.
"""

import os
import time
import shutil
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import (
    init_db,
    create_task,
    get_tasks,
    get_task_by_id,
    update_task,
    delete_task,
    add_subtasks,
    log_reinforcement_feedback,
    get_daily_status_summary,
    get_reinforcement_metrics,
    DEFAULT_DB_PATH
)
from tools import (
    auto_decompose_task,
    generate_morning_briefing,
    suggest_time_blocks,
    sync_calendar_event,
    parse_uploaded_file
)
from agent import TaskManagementAgent

# Initialize tables
init_db()

app = FastAPI(
    title="AI Task Management Agent API",
    description="Backend API powering natural language task management, auto-decomposition, and dynamic prioritization",
    version="2.0.0"
)

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000,*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in origins else origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = TaskManagementAgent()
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Latency tracking middleware to enforce < 1.5s target
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
    return response


# --- Pydantic Models ---
class ChatRequest(BaseModel):
    prompt: str = Field(..., example="Remind me to prep for the marketing review next Tuesday")


class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "P2 - Medium"
    due_date: Optional[str] = None
    estimated_duration_mins: Optional[int] = 30
    assignee: Optional[str] = "Unassigned"
    context: Optional[str] = ""
    parent_id: Optional[int] = None


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[str] = None
    estimated_duration_mins: Optional[int] = None
    assignee: Optional[str] = None
    context: Optional[str] = None


class DecomposeRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = ""


class FeedbackRequest(BaseModel):
    task_id: Optional[int] = None
    suggested_priority: str
    actual_priority: str
    was_accepted: bool
    user_override_reason: Optional[str] = ""


# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Task Management Agent API",
        "version": "2.0.0",
        "database": DEFAULT_DB_PATH
    }


@app.post("/api/agent/command")
def process_agent_command(req: ChatRequest):
    """Processes natural language user prompt through the Agent."""
    return agent.process_command(req.prompt)


@app.get("/api/tasks")
def list_tasks(status: Optional[str] = None, priority: Optional[str] = None):
    return get_tasks(status=status, priority=priority)


@app.post("/api/tasks")
def add_new_task(req: CreateTaskRequest):
    task = create_task(
        title=req.title,
        description=req.description or "",
        priority=req.priority or "P2 - Medium",
        due_date=req.due_date,
        estimated_duration_mins=req.estimated_duration_mins or 30,
        assignee=req.assignee or "Unassigned",
        context=req.context or "",
        parent_id=req.parent_id
    )
    return task


@app.get("/api/tasks/{task_id}")
def get_single_task(task_id: int):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/api/tasks/{task_id}")
def update_single_task(task_id: int, req: UpdateTaskRequest):
    updates = req.model_dump(exclude_unset=True)
    updated = update_task(task_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated


@app.delete("/api/tasks/{task_id}")
def delete_single_task(task_id: int):
    success = delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": f"Task {task_id} deleted."}


@app.post("/api/tasks/{task_id}/decompose")
def decompose_existing_task(task_id: int):
    task = get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    subtask_titles = auto_decompose_task(task["title"], task.get("description", ""))
    created_subtasks = add_subtasks(task_id, subtask_titles)
    task["subtasks"] = created_subtasks
    return {
        "task": task,
        "subtasks_generated": created_subtasks,
        "count": len(created_subtasks)
    }


@app.get("/api/briefing")
def get_morning_briefing():
    status_data = get_daily_status_summary()
    return generate_morning_briefing(status_data)


@app.post("/api/reinforcement/feedback")
def submit_reinforcement_feedback(req: FeedbackRequest):
    log_id = log_reinforcement_feedback(
        task_id=req.task_id,
        suggested_priority=req.suggested_priority,
        actual_priority=req.actual_priority,
        was_accepted=req.was_accepted,
        user_override_reason=req.user_override_reason or ""
    )
    return {"success": True, "log_id": log_id}


@app.get("/api/reinforcement/metrics")
def get_adaptive_metrics():
    return get_reinforcement_metrics()


@app.post("/api/upload")
async def upload_file_and_ingest(file: UploadFile = File(...)):
    """Accepts uploaded documents, saves them to uploads/, and extracts task definitions."""
    dest_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extracted = parse_uploaded_file(dest_path)
    created_tasks = []
    for item in extracted:
        t = create_task(
            title=item["title"],
            description=item.get("description", ""),
            priority=item.get("priority", "P2 - Medium")
        )
        created_tasks.append(t)

    return {
        "filename": file.filename,
        "file_path": dest_path,
        "tasks_extracted_count": len(created_tasks),
        "created_tasks": created_tasks
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=True)
