"""
Database module for AI Task Management Agent.
Handles local storage and schema management for tasks, subtasks, and reinforcement logs.
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "tasks.db")


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates a database connection with dict-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority TEXT CHECK(priority IN ('P0 - Critical', 'P1 - High', 'P2 - Medium', 'P3 - Low')) DEFAULT 'P2 - Medium',
            status TEXT CHECK(status IN ('pending', 'in_progress', 'completed', 'blocked')) DEFAULT 'pending',
            due_date TEXT,
            estimated_duration_mins INTEGER DEFAULT 30,
            assignee TEXT DEFAULT 'Unassigned',
            context TEXT DEFAULT '',
            parent_id INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES tasks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            status TEXT CHECK(status IN ('pending', 'in_progress', 'completed')) DEFAULT 'pending',
            order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reinforcement_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            suggested_priority TEXT NOT NULL,
            actual_priority TEXT NOT NULL,
            was_accepted BOOLEAN NOT NULL DEFAULT 1,
            user_override_reason TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS agent_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT,
            latency_ms REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()


def create_task(
    title: str,
    description: str = "",
    priority: str = "P2 - Medium",
    due_date: Optional[str] = None,
    estimated_duration_mins: int = 30,
    assignee: str = "Unassigned",
    context: str = "",
    parent_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """Creates a new task and returns its dictionary representation."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tasks (title, description, priority, due_date, estimated_duration_mins, assignee, context, parent_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (title, description, priority, due_date, estimated_duration_mins, assignee, context, parent_id))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_task_by_id(task_id, db_path=db_path)


def get_task_by_id(task_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetches a task by its ID along with any associated subtasks."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    task = dict(row)
    cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index ASC", (task_id,))
    task["subtasks"] = [dict(sub) for sub in cursor.fetchall()]
    conn.close()
    return task


def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    parent_only: bool = True,
    db_path: str = DEFAULT_DB_PATH
) -> List[Dict[str, Any]]:
    """Retrieves tasks with optional filters."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if parent_only:
        query += " AND parent_id IS NULL"
    if status:
        query += " AND status = ?"
        params.append(status)
    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY CASE priority WHEN 'P0 - Critical' THEN 1 WHEN 'P1 - High' THEN 2 WHEN 'P2 - Medium' THEN 3 WHEN 'P3 - Low' THEN 4 END, created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    tasks = []
    for r in rows:
        t = dict(r)
        cursor.execute("SELECT * FROM subtasks WHERE task_id = ? ORDER BY order_index ASC", (t["id"],))
        t["subtasks"] = [dict(sub) for sub in cursor.fetchall()]
        tasks.append(t)

    conn.close()
    return tasks


def update_task(task_id: int, updates: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Updates fields on an existing task."""
    allowed_fields = {
        "title", "description", "priority", "status", "due_date",
        "estimated_duration_mins", "assignee", "context", "parent_id"
    }
    filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    if not filtered_updates:
        return get_task_by_id(task_id, db_path=db_path)

    set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
    set_clause += ", updated_at = CURRENT_TIMESTAMP"
    values = list(filtered_updates.values())
    values.append(task_id)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

    return get_task_by_id(task_id, db_path=db_path)


def delete_task(task_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Deletes a task and cascading subtasks."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def add_subtasks(task_id: int, subtasks: List[str], db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Adds multiple subtasks for a task."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    created_subtasks = []
    for idx, title in enumerate(subtasks):
        cursor.execute("""
            INSERT INTO subtasks (task_id, title, status, order_index)
            VALUES (?, ?, 'pending', ?)
        """, (task_id, title, idx))
        created_subtasks.append({
            "id": cursor.lastrowid,
            "task_id": task_id,
            "title": title,
            "status": "pending",
            "order_index": idx
        })

    conn.commit()
    conn.close()
    return created_subtasks


def log_reinforcement_feedback(
    task_id: Optional[int],
    suggested_priority: str,
    actual_priority: str,
    was_accepted: bool,
    user_override_reason: str = "",
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Logs reinforcement feedback to adaptively learn user priority preferences."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reinforcement_feedback (task_id, suggested_priority, actual_priority, was_accepted, user_override_reason)
        VALUES (?, ?, ?, ?, ?)
    """, (task_id, suggested_priority, actual_priority, 1 if was_accepted else 0, user_override_reason))
    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_reinforcement_metrics(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Calculates acceptance rate and priority override patterns."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total, SUM(was_accepted) as accepted FROM reinforcement_feedback")
    row = cursor.fetchone()
    total = row["total"] or 0
    accepted = row["accepted"] or 0
    acceptance_rate = (accepted / total * 100.0) if total > 0 else 100.0

    cursor.execute("""
        SELECT suggested_priority, actual_priority, COUNT(*) as count
        FROM reinforcement_feedback
        WHERE was_accepted = 0
        GROUP BY suggested_priority, actual_priority
    """)
    overrides = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "total_logged": total,
        "accepted_suggestions": accepted,
        "acceptance_rate_percent": round(acceptance_rate, 2),
        "frequent_overrides": overrides
    }


def get_daily_status_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Summarizes overdue tasks, high-priority items, and today's schedule limits."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    now_iso = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT * FROM tasks 
        WHERE status != 'completed' 
          AND due_date IS NOT NULL 
          AND due_date < ?
        ORDER BY due_date ASC
    """, (now_iso,))
    overdue = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT * FROM tasks 
        WHERE status != 'completed' 
          AND priority IN ('P0 - Critical', 'P1 - High')
        ORDER BY CASE priority WHEN 'P0 - Critical' THEN 1 ELSE 2 END
    """)
    high_priority = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'")
    pending_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'in_progress'")
    in_progress_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'completed'")
    completed_count = cursor.fetchone()["count"]

    conn.close()
    return {
        "overdue_tasks": overdue,
        "high_priority_tasks": high_priority,
        "pending_count": pending_count,
        "in_progress_count": in_progress_count,
        "completed_count": completed_count
    }
