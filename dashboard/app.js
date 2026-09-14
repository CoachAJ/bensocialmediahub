// Pharmacist Ben Social Media Hub - Frontend Dashboard Controller

let isRunning = false;
let logPollInterval = null;

// DOM Elements
const refreshBtn = document.getElementById('refresh-btn');
const runBtn = document.getElementById('run-pipeline-btn');
const terminal = document.getElementById('terminal-stream');
const clearLogBtn = document.getElementById('clear-log-btn');
const copyLogBtn = document.getElementById('copy-log-btn');
const lastUpdatedText = document.getElementById('last-updated-text');
const runnerBadge = document.getElementById('runner-state-badge');

// Buffer Queue Elements
const ttPill = document.getElementById('tt-pill');
const ttBar = document.getElementById('tt-bar');
const ttSlots = document.getElementById('tt-slots-text');

const igPill = document.getElementById('ig-pill');
const igBar = document.getElementById('ig-bar');
const igSlots = document.getElementById('ig-slots-text');

const xPill = document.getElementById('x-pill');
const xBar = document.getElementById('x-bar');
const xSlots = document.getElementById('x-slots-text');

// Inventory Stats
const shortsCount = document.getElementById('shorts-count');
const podcastsCount = document.getElementById('podcasts-count');
const quizzesCount = document.getElementById('quizzes-count');

// Mode Selection Handler
const modeOptions = document.querySelectorAll('.mode-option');
let selectedMode = 'all';

modeOptions.forEach(opt => {
  opt.addEventListener('click', () => {
    modeOptions.forEach(o => o.classList.remove('active'));
    opt.classList.add('active');
    const radio = opt.querySelector('input');
    radio.checked = true;
    selectedMode = radio.value;
  });
});

// Append Line to Terminal
function appendTerminalLine(text, type = 'info') {
  const line = document.createElement('div');
  line.className = `terminal-line ${type}-msg`;
  line.textContent = text;
  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

// Fetch Live Stats from Backend
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const data = await res.json();

    // Update Queues (Capacity max 10)
    updateQueueUI('tt', data.queues?.tiktok || { count: 0, limit: 10 });
    updateQueueUI('ig', data.queues?.instagram || { count: 0, limit: 10 });
    updateQueueUI('x', data.queues?.x || { count: 0, limit: 10 });

    // Update Manifest Counts
    shortsCount.textContent = data.manifest?.existing_shorts || 0;
    podcastsCount.textContent = data.manifest?.podcast_episodes || 0;
    quizzesCount.textContent = data.manifest?.quizzes || 0;

    // Service Health
    updateHealthDot('health-gemini', data.health?.gemini);
    updateHealthDot('health-buffer', data.health?.buffer);
    updateHealthDot('health-drive', data.health?.drive);
    updateHealthDot('health-rss', data.health?.rss);

    const now = new Date();
    lastUpdatedText.textContent = `Updated ${now.toLocaleTimeString()}`;
  } catch (err) {
    console.warn('Could not fetch /api/stats (using local defaults):', err);
    lastUpdatedText.textContent = 'Offline / Standalone mode';
  }
}

function updateQueueUI(prefix, qData) {
  const count = qData.count || 0;
  const limit = qData.limit || 10;
  const pct = Math.min(100, Math.round((count / limit) * 100));
  const freeSlots = Math.max(0, limit - count);

  const pill = document.getElementById(`${prefix}-pill`);
  const bar = document.getElementById(`${prefix}-bar`);
  const slots = document.getElementById(`${prefix}-slots-text`);

  if (pill) pill.textContent = `${count} / ${limit}`;
  if (bar) {
    bar.style.width = `${pct}%`;
    if (pct >= 90) {
      bar.style.background = 'linear-gradient(90deg, #f59e0b, #ef4444)';
    } else {
      bar.style.background = 'linear-gradient(90deg, #38bdf8, #00f0ff)';
    }
  }
  if (slots) slots.textContent = `${freeSlots} slots available`;
}

function updateHealthDot(elementId, isHealthy) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const dot = el.querySelector('.health-dot');
  if (dot) {
    if (isHealthy) {
      dot.style.background = '#10b981';
      dot.style.boxShadow = '0 0 6px #10b981';
    } else {
      dot.style.background = '#f59e0b';
      dot.style.boxShadow = '0 0 6px #f59e0b';
    }
  }
}

// Execute Pipeline Run
async function executeRun() {
  if (isRunning) return;

  isRunning = true;
  runBtn.disabled = true;
  runBtn.innerHTML = `
    <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 1s linear infinite;">
      <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
      <path d="M12 2a10 10 0 0 1 10 10" stroke-linecap="round"></path>
    </svg>
    <span>Executing Pipeline...</span>
  `;
  runnerBadge.textContent = 'Running';
  runnerBadge.style.color = '#38bdf8';
  runnerBadge.style.borderColor = '#38bdf8';

  appendTerminalLine(`[RUN TRIGGERED] Starting run with mode='${selectedMode}'...`, 'system');

  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: selectedMode })
    });

    if (!res.ok) throw new Error(`Execution failed with HTTP ${res.status}`);
    const data = await res.json();
    if (data.message) {
      appendTerminalLine(`[CLOUD] ${data.message}`, data.dispatched !== false ? 'success' : 'warn');
    }
    if (data.actions_url) {
      appendTerminalLine(`[GITHUB] View live workflow runs: ${data.actions_url}`, 'info');
    }
    
    // Start polling logs
    pollLogs();
  } catch (err) {
    appendTerminalLine(`[ERROR] Execution trigger failed: ${err.message}`, 'error');
    finishRun();
  }
}

function pollLogs() {
  if (logPollInterval) clearInterval(logPollInterval);
  
  let lastIndex = 0;
  logPollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/logs?since=${lastIndex}`);
      if (!res.ok) return;
      const data = await res.json();
      
      if (data.lines && data.lines.length > 0) {
        data.lines.forEach(line => {
          let type = 'info';
          if (line.includes('[ERROR]') || line.includes('failed')) type = 'error';
          else if (line.includes('[WARN]')) type = 'warn';
          else if (line.includes('finished') || line.includes('Successfully')) type = 'success';
          else if (line.includes('[SYSTEM]')) type = 'system';
          
          appendTerminalLine(line, type);
        });
        lastIndex = data.next_index;
      }

      if (data.status === 'completed' || data.status === 'idle') {
        clearInterval(logPollInterval);
        finishRun();
        fetchStats();
      }
    } catch (e) {
      console.warn('Log polling error:', e);
    }
  }, 1000);
}

function finishRun() {
  isRunning = false;
  runBtn.disabled = false;
  runBtn.innerHTML = `
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <polygon points="5 3 19 12 5 21 5 3"></polygon>
    </svg>
    <span>Run Pipeline Now</span>
  `;
  runnerBadge.textContent = 'Engine Ready';
  runnerBadge.style.color = '#00f0ff';
  runnerBadge.style.borderColor = 'rgba(0, 240, 255, 0.2)';
}

// Inline Quiz Preview interactive tester
function testQuizClick(btn, isCorrect) {
  const siblings = btn.parentElement.querySelectorAll('.inline-opt');
  siblings.forEach(s => s.disabled = true);
  if (isCorrect) {
    btn.classList.add('correct');
  } else {
    btn.classList.add('incorrect');
    siblings[1].classList.add('correct'); // B is correct in preview
  }
}

// Event Listeners
refreshBtn.addEventListener('click', fetchStats);
runBtn.addEventListener('click', executeRun);

clearLogBtn.addEventListener('click', () => {
  terminal.innerHTML = '<div class="terminal-line system-msg">[LOG CLEARED] Terminal reset.</div>';
});

copyLogBtn.addEventListener('click', () => {
  const text = terminal.innerText;
  navigator.clipboard.writeText(text).then(() => {
    appendTerminalLine('[SYSTEM] Terminal text copied to clipboard.', 'system');
  });
});

// Initial Setup & Polling
fetchStats();
setInterval(fetchStats, 15000); // Poll stats every 15s

// CSS Spinner keyframe helper
const style = document.createElement('style');
style.innerHTML = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;
document.head.appendChild(style);
