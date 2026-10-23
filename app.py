"""
Application entry point for AI Task Management Agent.
Provides an interactive command-line interface for direct agent interaction,
as well as a launcher for the API server.
"""

import sys
import argparse
from agent import TaskManagementAgent
from database import init_db, get_daily_status_summary, get_tasks
from tools import generate_morning_briefing


def interactive_cli():
    print("=" * 60)
    print("  AI Task Management Agent - Interactive CLI")
    print("=" * 60)
    print("Type your natural language command (or 'exit' / 'quit' to finish).")
    print("Examples:")
    print(" - 'Remind me to prep for the marketing review next Tuesday'")
    print(" - 'Break down building the new customer authentication flow'")
    print(" - 'Give me my morning briefing'")
    print(" - 'What should I work on next?'")
    print("-" * 60)

    init_db()
    agent = TaskManagementAgent()

    while True:
        try:
            prompt = input("\n[AI Agent] > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["exit", "quit", "q"]:
                print("Exiting AI Task Management Agent. Goodbye!")
                break

            result = agent.process_command(prompt)
            print(f"\n[Intent Detected]: {result['intent']} (Confidence: {result['confidence']:.2f})")
            print(f"[Latency]: {result['latency_ms']} ms")
            print(f"[Response]: {result['message']}")

            if result.get("data") and isinstance(result["data"], dict) and "subtasks" in result["data"]:
                subtasks = result["data"]["subtasks"]
                print("  Generated Subtasks:")
                for st in subtasks:
                    print(f"    - [{st.get('status', 'pending')}] {st.get('title')}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break


def main():
    parser = argparse.ArgumentParser(description="AI Task Management Agent Runner")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI API server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--briefing", action="store_true", help="Print daily morning briefing")
    parser.add_argument("--tasks", action="store_true", help="List all current tasks")

    args = parser.parse_args()

    init_db()

    if args.serve:
        import uvicorn
        from api_server import app
        print(f"Starting API Server on http://0.0.0.0:{args.port}...")
        uvicorn.run(app, host="0.0.0.0", port=args.port)
    elif args.briefing:
        status = get_daily_status_summary()
        briefing = generate_morning_briefing(status)
        print(f"\nHeadline: {briefing['headline']}")
        print(f"Summary: {briefing['summary']}")
        print(f"Overdue: {briefing['overdue_count']}, High Priority: {briefing['high_priority_count']}")
    elif args.tasks:
        tasks = get_tasks()
        print(f"\nTotal Tasks: {len(tasks)}")
        for t in tasks:
            print(f"[{t['priority']}] #{t['id']} {t['title']} (Status: {t['status']}, Due: {t['due_date']})")
    else:
        interactive_cli()


if __name__ == "__main__":
    main()
