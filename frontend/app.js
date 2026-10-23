/**
 * AI Task Management Agent - Frontend Client Controller
 * Manages conversational command submission, task board state,
 * auto-decomposition, morning briefings, and latency tracking.
 */

const API_BASE_URL = window.location.origin.includes(':5173') 
    ? 'http://localhost:8000/api'
    : 'http://localhost:8000/api';

// State store
const state = {
    tasks: [],
    loading: false,
    latency: null,
    briefing: null,
    apiOnline: false
};

// DOM Elements
const commandInput = document.getElementById('command-input');
const commandBtn = document.getElementById('command-btn');
const statusPendingEl = document.getElementById('tasks-pending');
const statusInProgressEl = document.getElementById('tasks-in-progress');
const statusCompletedEl = document.getElementById('tasks-completed');
const latencyBadgeEl = document.getElementById('latency-badge');
const apiStatusEl = document.getElementById('api-status');
const briefingBannerEl = document.getElementById('briefing-banner');
const briefingContentEl = document.getElementById('briefing-content');

// Helper to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}

// Check Backend API Health
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(2000) });
        if (response.ok) {
            state.apiOnline = true;
            if (apiStatusEl) {
                apiStatusEl.innerHTML = `<span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse mr-2"></span>Backend Online`;
                apiStatusEl.className = "flex items-center text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full";
            }
            loadTasks();
            loadBriefing();
        } else {
            throw new Error();
        }
    } catch {
        state.apiOnline = false;
        if (apiStatusEl) {
            apiStatusEl.innerHTML = `<span class="inline-block w-2.5 h-2.5 rounded-full bg-amber-500 mr-2"></span>Local Agent Standby`;
            apiStatusEl.className = "flex items-center text-xs font-semibold text-amber-400 bg-amber-950/60 border border-amber-800/80 px-3 py-1 rounded-full";
        }
        // Load initial offline placeholder tasks
        loadMockTasks();
    }
}

// Fetch all tasks from server
async function loadTasks() {
    try {
        const res = await fetch(`${API_BASE_URL}/tasks`);
        if (!res.ok) throw new Error();
        state.tasks = await res.json();
        renderTasks();
    } catch (err) {
        console.warn('Could not fetch tasks from server, keeping current view.');
    }
}

// Fetch Daily Morning Briefing
async function loadBriefing() {
    try {
        const res = await fetch(`${API_BASE_URL}/briefing`);
        if (res.ok) {
            state.briefing = await res.json();
            renderBriefing();
        }
    } catch (err) {
        console.warn('Briefing unavailable');
    }
}

function renderBriefing() {
    if (!briefingBannerEl || !state.briefing) return;
    briefingContentEl.innerHTML = `
        <div class="flex items-center justify-between">
            <div>
                <h4 class="font-bold text-amber-400 text-sm tracking-wide uppercase">${escapeHtml(state.briefing.headline)}</h4>
                <p class="text-slate-300 text-sm mt-0.5">${escapeHtml(state.briefing.summary)}</p>
            </div>
            <div class="flex gap-4 text-xs font-medium">
                <span class="bg-red-950/80 text-red-300 border border-red-800 px-3 py-1.5 rounded-lg font-mono">Overdue: <b>${state.briefing.overdue_count}</b></span>
                <span class="bg-amber-950/80 text-amber-300 border border-amber-800 px-3 py-1.5 rounded-lg font-mono">Critical/High: <b>${state.briefing.high_priority_count}</b></span>
            </div>
        </div>
    `;
    briefingBannerEl.classList.remove('hidden');
}

// Render Task Board Columns
function renderTasks() {
    if (!statusPendingEl || !statusInProgressEl || !statusCompletedEl) return;

    statusPendingEl.innerHTML = '';
    statusInProgressEl.innerHTML = '';
    statusCompletedEl.innerHTML = '';

    const pending = state.tasks.filter(t => t.status === 'pending');
    const inProgress = state.tasks.filter(t => t.status === 'in_progress');
    const completed = state.tasks.filter(t => t.status === 'completed');

    document.getElementById('count-pending').innerText = pending.length;
    document.getElementById('count-in-progress').innerText = inProgress.length;
    document.getElementById('count-completed').innerText = completed.length;

    pending.forEach(t => statusPendingEl.appendChild(createTaskCard(t)));
    inProgress.forEach(t => statusInProgressEl.appendChild(createTaskCard(t)));
    completed.forEach(t => statusCompletedEl.appendChild(createTaskCard(t)));
}

function getPriorityBadgeClass(priority) {
    if (!priority) return 'badge-p2';
    if (priority.includes('P0')) return 'badge-p0';
    if (priority.includes('P1')) return 'badge-p1';
    if (priority.includes('P2')) return 'badge-p2';
    return 'badge-p3';
}

function createTaskCard(task) {
    const card = document.createElement('div');
    card.className = "bg-slate-900/90 border border-slate-800/90 hover:border-slate-700 p-4 rounded-xl shadow-lg transition duration-200 flex flex-col gap-3 group relative";

    const subtasks = task.subtasks || [];
    const subtaskHtml = subtasks.length > 0 ? `
        <div class="mt-2 pt-2 border-t border-slate-800/80">
            <p class="text-xs font-semibold text-slate-400 mb-1 flex items-center justify-between">
                <span>Subtasks (${subtasks.filter(s => s.status === 'completed').length}/${subtasks.length})</span>
            </p>
            <div class="space-y-1">
                ${subtasks.map(s => `
                    <div class="text-xs flex items-center gap-2 text-slate-300">
                        <span class="w-1.5 h-1.5 rounded-full ${s.status === 'completed' ? 'bg-emerald-400' : 'bg-slate-600'}"></span>
                        <span class="${s.status === 'completed' ? 'line-through text-slate-500' : ''}">${escapeHtml(s.title)}</span>
                    </div>
                `).join('')}
            </div>
        </div>
    ` : '';

    card.innerHTML = `
        <div class="flex items-start justify-between gap-2">
            <span class="${getPriorityBadgeClass(task.priority)}">${escapeHtml(task.priority)}</span>
            <div class="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition">
                <button onclick="handleStatusChange(${task.id}, '${task.status === 'pending' ? 'in_progress' : task.status === 'in_progress' ? 'completed' : 'pending'}')" 
                        class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded transition" title="Move status">
                    ${task.status === 'pending' ? 'Start →' : task.status === 'in_progress' ? 'Done ✓' : '↺ Reset'}
                </button>
            </div>
        </div>

        <div>
            <h3 class="text-sm font-semibold text-white tracking-tight leading-snug">${escapeHtml(task.title)}</h3>
            ${task.context ? `<p class="text-xs text-brand-400 mt-1">Context: ${escapeHtml(task.context)}</p>` : ''}
        </div>

        <div class="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/60">
            <span>📅 ${task.due_date || 'No due date'}</span>
            <span>👤 ${escapeHtml(task.assignee || 'Unassigned')}</span>
        </div>

        ${subtaskHtml}

        <div class="flex items-center gap-2 mt-1">
            ${subtasks.length === 0 ? `
                <button onclick="handleDecompose(${task.id})" class="text-xs text-brand-400 hover:text-brand-300 bg-brand-950/40 border border-brand-800/50 hover:bg-brand-900/50 px-2.5 py-1 rounded-md transition duration-150 flex items-center gap-1">
                    ✨ Auto-Decompose
                </button>
            ` : ''}
            <button onclick="handleOverridePriority(${task.id}, '${task.priority}')" class="text-xs text-slate-400 hover:text-slate-200 bg-slate-800/50 hover:bg-slate-700/60 px-2 py-1 rounded-md transition">
                ⚡ Adjust Priority
            </button>
        </div>
    `;

    return card;
}

// Handle Natural Language Command Submission
async function submitCommand() {
    const prompt = commandInput.value.trim();
    if (!prompt) return;

    commandBtn.disabled = true;
    commandBtn.innerText = "Processing...";
    const startTime = performance.now();

    try {
        const res = await fetch(`${API_BASE_URL}/agent/command`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        const duration = Math.round(performance.now() - startTime);

        updateLatency(duration);
        commandInput.value = '';
        await loadTasks();
        await loadBriefing();
    } catch (err) {
        console.error(err);
        alert('Could not connect to API server. Ensure python api_server.py is running.');
    } finally {
        commandBtn.disabled = false;
        commandBtn.innerText = "Send Command";
    }
}

// Update latency indicator
function updateLatency(ms) {
    if (!latencyBadgeEl) return;
    latencyBadgeEl.innerText = `${ms} ms`;
    if (ms < 1500) {
        latencyBadgeEl.className = "text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2.5 py-1 rounded-full";
    } else {
        latencyBadgeEl.className = "text-xs font-mono font-bold text-red-400 bg-red-950/80 border border-red-800 px-2.5 py-1 rounded-full";
    }
}

// Auto-Decompose Task
window.handleDecompose = async function(taskId) {
    try {
        const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/decompose`, { method: 'POST' });
        if (res.ok) {
            await loadTasks();
        }
    } catch (e) {
        console.error(e);
    }
};

// Update Task Status
window.handleStatusChange = async function(taskId, newStatus) {
    try {
        const res = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (res.ok) {
            await loadTasks();
            await loadBriefing();
        }
    } catch (e) {
        console.error(e);
    }
};

// Adaptive Reinforcement Priority Override
window.handleOverridePriority = async function(taskId, currentPriority) {
    const priorities = ["P0 - Critical", "P1 - High", "P2 - Medium", "P3 - Low"];
    const nextPriority = priorities[(priorities.indexOf(currentPriority) + 1) % priorities.length];
    
    // Log feedback
    try {
        await fetch(`${API_BASE_URL}/reinforcement/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                task_id: taskId,
                suggested_priority: currentPriority,
                actual_priority: nextPriority,
                was_accepted: false,
                user_override_reason: "Manual user reprioritization via UI"
            })
        });

        // Update task
        await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ priority: nextPriority })
        });

        await loadTasks();
    } catch (e) {
        console.error(e);
    }
};

// Fallback Mock Data for standalone UI preview
function loadMockTasks() {
    state.tasks = [
        {
            id: 1,
            title: "Prep for marketing review next Tuesday",
            priority: "P1 - High",
            status: "pending",
            due_date: "2026-10-27",
            assignee: "sarah",
            context: "marketing review",
            subtasks: [
                { id: 101, title: "Gather conversion analytics and ROI charts", status: "completed" },
                { id: 102, title: "Draft slide deck and executive takeaways", status: "pending" },
                { id: 103, title: "Review with VP of Growth", status: "pending" }
            ]
        },
        {
            id: 2,
            title: "Urgent: Resolve database connection pooling blocker",
            priority: "P0 - Critical",
            status: "in_progress",
            due_date: "2026-10-23",
            assignee: "dev-team",
            context: "infrastructure",
            subtasks: []
        },
        {
            id: 3,
            title: "Configure CalDAV and Google Calendar synchronization",
            priority: "P2 - Medium",
            status: "completed",
            due_date: "2026-10-22",
            assignee: "alex",
            context: "third-party sync",
            subtasks: []
        }
    ];
    renderTasks();
}

// Event Listeners
if (commandBtn && commandInput) {
    commandBtn.addEventListener('click', submitCommand);
    commandInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') submitCommand();
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkApiHealth();
});
