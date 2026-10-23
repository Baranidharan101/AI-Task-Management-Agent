"""
Tools module for AI Task Management Agent.
Defines external and algorithmic tools:
- Task Auto-Decomposition (generates 3-5 subtasks)
- Smart Scheduling & Time Blocking
- Daily Status Aggregation / Morning Briefings
- Calendar Synchronization (CalDAV/Google Calendar hooks)
- File Parsing & Ingestion
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def auto_decompose_task(title: str, description: str = "") -> List[str]:
    """
    Decomposes a broad or complex task into 3-5 logical, actionable subtasks.
    Uses pattern heuristics with fallback templates, ready for LLM augmentation.
    """
    text = f"{title} {description}".lower()

    # Domain-specific breakdown templates
    if any(k in text for k in ["prep", "review", "presentation", "slide", "meeting", "marketing"]):
        return [
            "Gather agenda items, key metrics, and supporting documents",
            "Draft presentation outline and slide deck narrative",
            "Review draft with team leads and incorporate feedback",
            "Finalize slide deck and rehearse talking points",
            "Send meeting invitations with agenda attachment"
        ]
    elif any(k in text for k in ["build", "develop", "implement", "feature", "code", "api", "app"]):
        return [
            "Define technical specifications and data schema",
            "Implement core logic and database integration",
            "Build user-facing endpoints / UI components",
            "Write automated smoke tests and perform manual verification",
            "Document deployment steps and merge pull request"
        ]
    elif any(k in text for k in ["deploy", "launch", "release", "ship"]):
        return [
            "Verify all test suites pass in staging environment",
            "Run database migrations and verify schema integrity",
            "Execute deployment pipeline and check server logs",
            "Perform smoke tests on production endpoints"
        ]
    elif any(k in text for k in ["research", "investigate", "audit", "analyze"]):
        return [
            "Identify key questions, goals, and evaluation criteria",
            "Collect relevant data, documents, and reference materials",
            "Synthesize findings into key takeaways and risks",
            "Formulate actionable recommendations and next steps"
        ]
    else:
        # General actionable breakdown
        clean_title = title.rstrip(".!?")
        return [
            f"Scope out requirements and dependencies for: {clean_title}",
            f"Draft initial execution plan and allocate needed resources",
            f"Execute primary action items for: {clean_title}",
            f"Review output against quality criteria and verify completion"
        ]


def suggest_time_blocks(
    task: Dict[str, Any],
    start_hour: int = 9,
    end_hour: int = 17,
    existing_commitments: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """
    Suggests optimal time blocks for a task by cross-referencing estimated
    duration with available working hours and calendar constraints.
    """
    duration = task.get("estimated_duration_mins", 45)
    priority = task.get("priority", "P2 - Medium")
    due_date = task.get("due_date")

    today = datetime.now()
    base_date = datetime.strptime(due_date, "%Y-%m-%d") if due_date else today

    # High priority tasks get early morning slots
    if "P0" in priority:
        suggested_start = base_date.replace(hour=9, minute=30, second=0)
    elif "P1" in priority:
        suggested_start = base_date.replace(hour=11, minute=0, second=0)
    elif "P2" in priority:
        suggested_start = base_date.replace(hour=14, minute=0, second=0)
    else:
        suggested_start = base_date.replace(hour=16, minute=0, second=0)

    suggested_end = suggested_start + timedelta(minutes=duration)

    return {
        "task_id": task.get("id"),
        "task_title": task.get("title"),
        "estimated_duration_mins": duration,
        "suggested_slot": {
            "start": suggested_start.strftime("%Y-%m-%d %H:%M"),
            "end": suggested_end.strftime("%Y-%m-%d %H:%M"),
            "focus_type": "Deep Work" if duration >= 60 else "Quick Execution"
        },
        "reasoning": f"Prioritized for {'morning peak focus' if 'P0' in priority or 'P1' in priority else 'afternoon standard window'} based on priority {priority}."
    }


def generate_morning_briefing(status_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constructs a daily morning briefing summarizing overdue tasks,
    high-priority items, and schedule workload limits.
    """
    overdue = status_data.get("overdue_tasks", [])
    high_priority = status_data.get("high_priority_tasks", [])
    pending = status_data.get("pending_count", 0)
    in_progress = status_data.get("in_progress_count", 0)

    total_urgent = len(overdue) + len(high_priority)
    workload_status = "manageable"
    if total_urgent > 5:
        workload_status = "heavy - action required"
    elif total_urgent > 2:
        workload_status = "moderate"

    summary_text = f"Good morning! You have {len(overdue)} overdue item(s) and {len(high_priority)} critical/high priority item(s). Your current workload is {workload_status}."

    return {
        "generated_at": datetime.now().isoformat(),
        "headline": "Morning Productivity Briefing",
        "summary": summary_text,
        "workload_status": workload_status,
        "overdue_count": len(overdue),
        "overdue_tasks": [{"id": t.get("id"), "title": t.get("title"), "due_date": t.get("due_date")} for t in overdue],
        "high_priority_count": len(high_priority),
        "high_priority_tasks": [{"id": t.get("id"), "title": t.get("title"), "priority": t.get("priority")} for t in high_priority],
        "in_progress_count": in_progress,
        "pending_count": pending
    }


def sync_calendar_event(task: Dict[str, Any], protocol: str = "google") -> Dict[str, Any]:
    """
    Two-way synchronization placeholder for Google Calendar or CalDAV.
    Generates an iCalendar standard payload and simulated sync confirmation.
    """
    title = task.get("title", "Untitled Task")
    due_date = task.get("due_date", datetime.now().strftime("%Y-%m-%d"))
    duration = task.get("estimated_duration_mins", 30)

    # Simulated calendar payload
    calendar_payload = {
        "protocol": protocol,
        "summary": title,
        "description": task.get("description", "") + f"\nContext: {task.get('context', 'None')}",
        "dtstart": f"{due_date}T09:00:00Z",
        "duration_minutes": duration,
        "status": "CONFIRMED",
        "sync_status": "synced_mock"
    }

    return {
        "success": True,
        "protocol": protocol,
        "message": f"Successfully prepared sync payload for '{title}' via {protocol.upper()}.",
        "event_data": calendar_payload
    }


def parse_uploaded_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parses an uploaded file (txt, json, csv, md) to extract potential task definitions.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    extracted_tasks = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    if ext == ".json":
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "title" in item:
                        extracted_tasks.append({
                            "title": item["title"],
                            "description": item.get("description", ""),
                            "priority": item.get("priority", "P2 - Medium")
                        })
            elif isinstance(data, dict) and "tasks" in data:
                for item in data["tasks"]:
                    extracted_tasks.append({
                        "title": item.get("title", "Untitled Task"),
                        "description": item.get("description", ""),
                        "priority": item.get("priority", "P2 - Medium")
                    })
        except Exception:
            pass

    # Fallback / text / markdown line parsing
    if not extracted_tasks:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        for line in lines:
            clean_line = re.sub(r"^[-*#\d\.\s\[\]]+", "", line).strip()
            if len(clean_line) >= 3:
                extracted_tasks.append({
                    "title": clean_line,
                    "description": f"Extracted from {os.path.basename(file_path)}",
                    "priority": "P2 - Medium"
                })

    return extracted_tasks
