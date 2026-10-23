"""
Smoke Test for AI Task Management Agent.
Verifies:
1. Database Schema Initialization & CRUD
2. Intent Recognition Engine Accuracy
3. NLP Parsing Engine Accuracy (Date, Priority, Assignee extraction)
4. Auto-Decomposition Logic (Generates 3-5 subtasks)
5. Smart Scheduling & Morning Briefing Tools
6. Agent Execution Latency (< 1.5s metric)
"""

import time
import os
import sys
from datetime import datetime

# Temporary test database to avoid polluting main db
TEST_DB = "test_tasks.db"
os.environ["DATABASE_PATH"] = TEST_DB

from database import (
    init_db,
    create_task,
    get_task_by_id,
    get_tasks,
    update_task,
    delete_task,
    add_subtasks,
    log_reinforcement_feedback,
    get_daily_status_summary
)
from tools import (
    auto_decompose_task,
    suggest_time_blocks,
    generate_morning_briefing,
    sync_calendar_event
)
from agent import TaskManagementAgent, IntentType


def run_tests():
    print("=" * 65)
    print("  RUNNING SMOKE TESTS FOR AI TASK MANAGEMENT AGENT")
    print("=" * 65)
    passed = 0
    total = 0

    def assert_test(name: str, condition: bool, extra_info: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            print(f" [PASS] {name} {extra_info}")
            passed += 1
        else:
            print(f" [FAIL] {name} {extra_info}")

    # 1. Database tests
    print("\n[1/6] Testing Database & Persistence...")
    try:
        init_db(TEST_DB)
        task = create_task(
            title="Prepare Quarterly Roadmap",
            priority="P1 - High",
            due_date="2026-11-01",
            db_path=TEST_DB
        )
        assert_test("DB Task Creation", task is not None and task["id"] is not None, f"(ID: {task.get('id')})")

        subtasks = add_subtasks(task["id"], ["Draft OKRs", "Review with Leadership", "Publish Slides"], db_path=TEST_DB)
        assert_test("DB Subtask Insertion", len(subtasks) == 3)

        updated = update_task(task["id"], {"status": "in_progress"}, db_path=TEST_DB)
        assert_test("DB Task Update", updated["status"] == "in_progress")

        feedback_id = log_reinforcement_feedback(task["id"], "P2 - Medium", "P1 - High", False, "Time-critical delivery", db_path=TEST_DB)
        assert_test("Reinforcement Feedback Logging", feedback_id > 0)
    except Exception as e:
        assert_test("Database CRUD", False, str(e))

    # 2. Intent Classification Tests
    print("\n[2/6] Testing Intent Recognition Engine...")
    agent = TaskManagementAgent(db_path=TEST_DB)
    intent_cases = [
        ("Remind me to prep for the marketing review next Tuesday", IntentType.CREATE_TASK),
        ("Break down the mobile app onboarding redesign", IntentType.DECOMPOSE_TASK),
        ("What should I work on next?", IntentType.QUERY_TASKS),
        ("Give me my morning briefing", IntentType.MORNING_BRIEFING),
        ("When should I schedule the security audit?", IntentType.SCHEDULE_TASK),
        ("Sync my roadmap to calendar", IntentType.SYNC_CALENDAR),
    ]

    for prompt, expected_intent in intent_cases:
        res = agent.intent_engine.classify(prompt)
        assert_test(f"Intent for: '{prompt[:35]}...'", res["intent"] == expected_intent, f"(Detected: {res['intent']})")

    # 3. NLP Parsing Engine Tests
    print("\n[3/6] Testing NLP Parsing Engine (Dates, Priorities, Entities)...")
    nlp_prompt = "Remind me to prep urgent presentation for the marketing review next Tuesday @sarah 45 mins"
    parsed = agent.nlp_engine.parse(nlp_prompt)
    assert_test("NLP Priority Extraction (Urgent -> P0)", parsed["priority"] == "P0 - Critical")
    assert_test("NLP Assignee Extraction (@sarah)", parsed["assignee"] == "sarah")
    assert_test("NLP Duration Extraction (45 mins)", parsed["estimated_duration_mins"] == 45)
    assert_test("NLP Date Extraction (Tuesday)", parsed["due_date"] is not None, f"(Date: {parsed.get('due_date')})")
    assert_test("NLP Context Extraction", "marketing review" in parsed["context"].lower())

    # 4. Auto-Decomposition Tool
    print("\n[4/6] Testing Auto-Decomposition Tool...")
    sub_tasks = auto_decompose_task("Build payment gateway integration", "Stripe API setup")
    assert_test("Subtask count between 3 and 5", 3 <= len(sub_tasks) <= 5, f"(Generated {len(sub_tasks)} items)")

    # 5. Tools & Morning Briefing
    print("\n[5/6] Testing Status Aggregation & Scheduling...")
    status = get_daily_status_summary(TEST_DB)
    briefing = generate_morning_briefing(status)
    assert_test("Morning Briefing Generated", "headline" in briefing and "summary" in briefing)

    time_slot = suggest_time_blocks({"title": "Fix security vulnerability", "priority": "P0 - Critical", "estimated_duration_mins": 60})
    assert_test("Smart Scheduling Allocation", "suggested_slot" in time_slot)

    # 6. Latency Benchmark (< 1.5s / 1500ms metric)
    print("\n[6/6] Testing Agent Execution Latency (< 1.5s)...")
    start_t = time.time()
    agent_res = agent.process_command("Urgent: Deploy hotfix for checkout outage tomorrow")
    elapsed_ms = (time.time() - start_t) * 1000.0
    assert_test("Execution Time < 1500ms", elapsed_ms < 1500.0, f"({elapsed_ms:.2f} ms)")

    # Clean up test database
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except Exception:
            pass

    print("\n" + "=" * 65)
    print(f"  SMOKE TEST SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("=" * 65)

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
