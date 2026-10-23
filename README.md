# AI Task Management Agent

An intelligent, autonomous productivity agent designed to automate, organize, and optimize user workflows natively within the Antigravity IDE. Unlike standard to-do applications, this agent uses natural language processing (NLP) to understand conversational intent, automatically breaks down high-level project goals into actionable subtasks, and dynamically prioritizes task queues with an adaptive feedback loop.

---

## Architecture Overview

The system adopts a decoupled full-stack architecture:

```
ai agent/
├── ai-task-management-ui/       # Modern Vite + Tailwind CSS frontend application
│   ├── public/                  # Static assets & icons
│   ├── src/                     # UI components, state management, and styles
│   ├── .gitignore               # Frontend ignore rules
│   ├── README.md                # UI specific documentation
│   ├── eslint.config.js         # ESLint configuration
│   ├── index.html               # Main web application entry point
│   ├── package-lock.json        # Dependency lockfile
│   ├── package.json             # NPM package manifest
│   └── vite.config.js           # Vite bundler & reverse proxy config
├── frontend/                    # Vanilla/Lightweight UI bundle
│   ├── app.js                   # Client-side agent communication & task board logic
│   ├── index.html               # Responsive web page
│   ├── postcss.config.js        # PostCSS configuration
│   ├── styles.css               # Tailwind CSS directives & custom styling
│   └── tailwind.config.js       # Design tokens & color palette
├── uploads/                     # Storage directory for uploaded user documents
│   └── .gitkeep
├── .env.example                 # Environment variables template
├── .gitignore                   # Repository git ignore rules
├── README.md                    # Project documentation
├── agent.py                     # Intent Recognition Engine & NLP Parsing loop
├── ai-task-management-prd.docx  # Product Requirements Document
├── api_server.py                # FastAPI REST API with CORS and latency tracking
├── app.py                       # Unified CLI and application runner
├── database.py                  # SQLite schema management & CRUD persistence
├── requirements.txt             # Python backend dependencies
├── smoke_test.py                # Automated agent verification & latency benchmarks
├── start.bat                    # One-click startup script (Full-stack)
├── start_api.bat                # One-click startup script (Backend API only)
└── tools.py                     # Auto-decomposition, scheduling & calendar tools
```

---

## Core Capabilities & PRD Specifications

1. **Frictionless NLP Parsing (P0 - Critical)**:
   Extracts task titles, assignees (`@sarah`), priorities (`urgent` -> `P0`, `important` -> `P1`), durations, and target dates (`next Tuesday`, `tomorrow`) from conversational prompts. Target accuracy: **95%**.
2. **Auto-Decomposition (P0 - Critical)**:
   Automatically generates 3-5 logical, domain-specific subtasks when a broad project command is received.
3. **Smart Scheduling & Time Blocking (P1 - High)**:
   Calculates optimal focus windows (Deep Work vs. Quick Execution) by cross-referencing task priority, duration, and availability.
4. **Daily Status Aggregation / Morning Briefing (P1 - High)**:
   Summarizes overdue tasks, critical blockers, and daily capacity limits.
5. **Adaptive Reinforcement Feedback**:
   Logs instances where users accept or override priority suggestions, dynamically adjusting weights for future schedules.
6. **Sub-1.5s API Latency**:
   Optimized lightweight architecture ensuring maximum round-trip time from user prompt to UI update is under **1.5 seconds**.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ (or `uv`)
- Node.js 18+ and `npm`

### 2. Backend Setup
Install Python dependencies:
```bash
pip install -r requirements.txt
```

Initialize environment variables:
```bash
cp .env.example .env
```

Run automated verification smoke tests:
```bash
python smoke_test.py
```

### 3. Running the Backend API
Start the FastAPI server on port 8000:
```bat
start_api.bat
```
Or directly via Python:
```bash
python api_server.py
```
Interactive CLI mode:
```bash
python app.py
```

### 4. Running the Frontend UI
Navigate to `ai-task-management-ui/`:
```bash
cd ai-task-management-ui
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

Or use the one-click startup batch script from the root directory:
```bat
start.bat
```

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and database verification |
| `POST` | `/api/agent/command` | Natural language conversational command processing |
| `GET` | `/api/tasks` | List all tasks (supports `status` and `priority` filters) |
| `POST` | `/api/tasks` | Create a new structured task |
| `GET` | `/api/tasks/{id}` | Retrieve task details with subtasks |
| `PUT` | `/api/tasks/{id}` | Update task status, priority, or metadata |
| `DELETE` | `/api/tasks/{id}` | Delete task and cascading subtasks |
| `POST` | `/api/tasks/{id}/decompose` | Trigger auto-decomposition into 3-5 subtasks |
| `GET` | `/api/briefing` | Fetch daily morning briefing & overdue warnings |
| `POST` | `/api/reinforcement/feedback` | Log user priority acceptance or override |
| `GET` | `/api/reinforcement/metrics` | Retrieve feedback learning metrics |
| `POST` | `/api/upload` | Upload document to `uploads/` and extract tasks |
