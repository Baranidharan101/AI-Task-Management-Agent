import './style.css';

const API_BASE = '/api';

const state = {
  tasks: [],
  latency: 0,
  loading: false,
};

const appEl = document.getElementById('app');

function renderApp() {
  appEl.innerHTML = `
    <div class="min-h-screen flex flex-col">
      <!-- Navbar -->
      <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-30">
        <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-lg shadow-brand-500/30">
              <span class="text-white font-bold text-lg">⚡</span>
            </div>
            <div>
              <h1 class="text-base font-bold text-white tracking-tight">AI Task Management Agent</h1>
              <p class="text-xs text-slate-400">Vite + Tailwind CSS UI Scaffolding</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span id="latency-chip" class="text-xs font-mono font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-800 px-2.5 py-1 rounded-full">
              ${state.latency} ms
            </span>
            <span class="flex items-center text-xs font-semibold text-emerald-400 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full">
              <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse mr-2"></span>Vite UI Ready
            </span>
          </div>
        </div>
      </header>

      <!-- Main Body -->
      <main class="flex-1 max-w-7xl w-full mx-auto px-4 py-8 flex flex-col gap-6">
        <!-- Natural Language Prompt Input -->
        <div class="glass-card p-6">
          <h2 class="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-2">Natural Language Task Input</h2>
          <div class="flex gap-3">
            <input 
              id="prompt-input"
              type="text" 
              placeholder="e.g. Remind me to prep for the marketing review next Tuesday @sarah 45 mins" 
              class="flex-1 px-4 py-3 bg-slate-950/80 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-brand-500"
            />
            <button 
              id="send-prompt-btn"
              class="bg-brand-500 hover:bg-brand-600 active:scale-95 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg shadow-brand-500/20">
              Run Agent
            </button>
          </div>
        </div>

        <!-- Task Kanban -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="glass-card p-5">
            <h3 class="font-bold text-sm text-slate-300 mb-3 flex items-center justify-between">
              <span>Pending</span>
              <span id="badge-pending" class="text-xs bg-slate-800 px-2 py-0.5 rounded-full">0</span>
            </h3>
            <div id="col-pending" class="space-y-3 min-h-[140px]"></div>
          </div>

          <div class="glass-card p-5">
            <h3 class="font-bold text-sm text-sky-400 mb-3 flex items-center justify-between">
              <span>In Progress</span>
              <span id="badge-progress" class="text-xs bg-sky-950 border border-sky-800 px-2 py-0.5 rounded-full text-sky-400">0</span>
            </h3>
            <div id="col-progress" class="space-y-3 min-h-[140px]"></div>
          </div>

          <div class="glass-card p-5">
            <h3 class="font-bold text-sm text-emerald-400 mb-3 flex items-center justify-between">
              <span>Completed</span>
              <span id="badge-completed" class="text-xs bg-emerald-950 border border-emerald-800 px-2 py-0.5 rounded-full text-emerald-400">0</span>
            </h3>
            <div id="col-completed" class="space-y-3 min-h-[140px]"></div>
          </div>
        </div>
      </main>
    </div>
  `;

  attachEvents();
}

function attachEvents() {
  const btn = document.getElementById('send-prompt-btn');
  const input = document.getElementById('prompt-input');

  const execute = async () => {
    const val = input.value.trim();
    if (!val) return;
    btn.disabled = true;
    btn.innerText = 'Processing...';
    const start = performance.now();

    try {
      const res = await fetch(`${API_BASE}/agent/command`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: val }),
      });
      const data = await res.json();
      state.latency = Math.round(performance.now() - start);
      input.value = '';
      await fetchTasks();
    } catch {
      alert('Could not contact API server. Please make sure api_server.py is running.');
    } finally {
      btn.disabled = false;
      btn.innerText = 'Run Agent';
    }
  };

  btn?.addEventListener('click', execute);
  input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') execute();
  });
}

async function fetchTasks() {
  try {
    const res = await fetch(`${API_BASE}/tasks`);
    if (res.ok) {
      state.tasks = await res.json();
      renderTasksGrid();
    }
  } catch (e) {
    console.warn('API offline, running in offline preview mode', e);
  }
}

function renderTasksGrid() {
  const pCol = document.getElementById('col-pending');
  const progCol = document.getElementById('col-progress');
  const compCol = document.getElementById('col-completed');
  if (!pCol) return;

  pCol.innerHTML = '';
  progCol.innerHTML = '';
  compCol.innerHTML = '';

  const p = state.tasks.filter((t) => t.status === 'pending');
  const pr = state.tasks.filter((t) => t.status === 'in_progress');
  const c = state.tasks.filter((t) => t.status === 'completed');

  document.getElementById('badge-pending').innerText = p.length;
  document.getElementById('badge-progress').innerText = pr.length;
  document.getElementById('badge-completed').innerText = c.length;

  const makeCard = (t) => {
    const el = document.createElement('div');
    el.className = 'bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex flex-col gap-2';
    el.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-xs px-2 py-0.5 rounded-full font-semibold ${t.priority.includes('P0') ? 'bg-red-500/10 text-red-400 border border-red-500/30' : 'bg-brand-500/10 text-brand-400 border border-brand-500/30'}">${t.priority}</span>
        <span class="text-xs text-slate-500">#${t.id}</span>
      </div>
      <p class="text-sm font-semibold text-white">${t.title}</p>
      <div class="flex justify-between text-xs text-slate-400 border-t border-slate-800/60 pt-2">
        <span>📅 ${t.due_date || 'None'}</span>
        <span>👤 ${t.assignee || 'Unassigned'}</span>
      </div>
    `;
    return el;
  };

  p.forEach((t) => pCol.appendChild(makeCard(t)));
  pr.forEach((t) => progCol.appendChild(makeCard(t)));
  c.forEach((t) => compCol.appendChild(makeCard(t)));
}

// Initial render
renderApp();
fetchTasks();
