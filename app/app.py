from flask import Flask, jsonify, render_template_string
import redis, os, time, datetime

app = Flask(__name__)
r = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis-service'),
    port=6379, decode_responses=True
)

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Swapnil | DevOps Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Syne:wght@400;600;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #080c10;
    --panel: #0d1117;
    --border: #1c2a3a;
    --green: #00ff88;
    --green-dim: #00ff8822;
    --cyan: #00d4ff;
    --cyan-dim: #00d4ff18;
    --amber: #ffb800;
    --amber-dim: #ffb80018;
    --red: #ff4458;
    --text: #c9d1d9;
    --text-dim: #4a5568;
    --text-muted: #8892a4;
    --glow-g: 0 0 20px #00ff8840, 0 0 40px #00ff8820;
    --glow-c: 0 0 20px #00d4ff40, 0 0 40px #00d4ff20;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
    position: relative;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,255,136,0.012) 2px,
      rgba(0,255,136,0.012) 4px
    );
    pointer-events: none;
    z-index: 1000;
  }

  /* Grid background */
  body::after {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(0,212,255,0.04) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,212,255,0.04) 1px, transparent 1px);
    background-size: 48px 48px;
    pointer-events: none;
    z-index: 0;
  }

  .container {
    position: relative;
    z-index: 1;
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem 1.5rem 4rem;
  }

  /* ─── HEADER ─── */
  .header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header-left { flex: 1; }

  .prompt-line {
    font-size: 11px;
    color: var(--text-dim);
    letter-spacing: 0.08em;
    margin-bottom: 6px;
  }
  .prompt-line span { color: var(--green); }

  .name {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1;
    color: #fff;
    margin-bottom: 4px;
  }

  .title-tag {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--cyan);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 8px;
  }
  .title-tag::before {
    content: '';
    display: block;
    width: 6px; height: 6px;
    background: var(--cyan);
    border-radius: 50%;
    box-shadow: var(--glow-c);
    animation: blink 1.4s ease-in-out infinite;
  }

  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--green-dim);
    border: 1px solid #00ff8840;
    border-radius: 99px;
    padding: 6px 14px;
    font-size: 11px;
    color: var(--green);
    letter-spacing: 0.05em;
    white-space: nowrap;
    animation: pulse-border 2s ease-in-out infinite;
  }
  .status-dot {
    width: 7px; height: 7px;
    background: var(--green);
    border-radius: 50%;
    box-shadow: var(--glow-g);
    animation: blink 1s ease-in-out infinite;
  }

  /* ─── METRICS ROW ─── */
  .metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 1.5rem;
  }

  .metric {
    background: var(--panel);
    padding: 1.25rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: background 0.2s;
  }
  .metric:hover { background: #111820; }
  .metric::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }
  .metric.green::before { background: linear-gradient(90deg, transparent, var(--green), transparent); }
  .metric.cyan::before  { background: linear-gradient(90deg, transparent, var(--cyan), transparent); }
  .metric.amber::before { background: linear-gradient(90deg, transparent, var(--amber), transparent); }

  .metric-label {
    font-size: 10px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 10px;
  }
  .metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
  }
  .metric.green .metric-value { color: var(--green); text-shadow: var(--glow-g); }
  .metric.cyan  .metric-value { color: var(--cyan);  text-shadow: var(--glow-c); }
  .metric.amber .metric-value { color: var(--amber); }

  .metric-sub {
    font-size: 11px;
    color: var(--text-muted);
  }

  /* ─── MAIN GRID ─── */
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1rem;
  }
  @media (max-width: 680px) { .grid { grid-template-columns: 1fr; } }

  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }

  .panel-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    background: #0a1018;
  }
  .panel-dots { display: flex; gap: 5px; }
  .panel-dots span {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: block;
  }
  .panel-dots span:nth-child(1) { background: #ff5f57; }
  .panel-dots span:nth-child(2) { background: #ffbd2e; }
  .panel-dots span:nth-child(3) { background: #28c840; }

  .panel-title {
    font-size: 11px;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    flex: 1;
  }

  .panel-body { padding: 1rem 1.25rem; }

  /* ─── ENDPOINT LIST ─── */
  .endpoint-list { display: flex; flex-direction: column; gap: 8px; }

  .endpoint {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: #080c10;
    border: 1px solid var(--border);
    border-radius: 7px;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    position: relative;
    overflow: hidden;
  }
  .endpoint::after {
    content: '';
    position: absolute;
    inset: 0;
    background: var(--green-dim);
    opacity: 0;
    transition: opacity 0.2s;
  }
  .endpoint:hover { border-color: #00ff8840; }
  .endpoint:hover::after { opacity: 1; }

  .method-badge {
    font-size: 10px;
    font-weight: 700;
    padding: 3px 7px;
    border-radius: 4px;
    letter-spacing: 0.05em;
    background: var(--green-dim);
    color: var(--green);
    border: 1px solid #00ff8830;
    flex-shrink: 0;
  }

  .endpoint-path {
    font-size: 13px;
    color: var(--cyan);
    flex: 1;
  }

  .endpoint-desc {
    font-size: 10px;
    color: var(--text-dim);
  }

  /* ─── RESPONSE VIEWER ─── */
  .response-box {
    background: #060a0e;
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 12px;
    min-height: 160px;
    font-size: 12px;
    line-height: 1.7;
    position: relative;
  }
  .response-placeholder {
    color: var(--text-dim);
    font-style: italic;
  }
  .json-key   { color: var(--cyan); }
  .json-str   { color: var(--green); }
  .json-num   { color: var(--amber); }
  .json-bool  { color: #cba6f7; }
  .json-brace { color: var(--text-muted); }

  .response-status {
    position: absolute;
    top: 8px; right: 10px;
    font-size: 10px;
    color: var(--green);
    letter-spacing: 0.06em;
  }

  /* ─── PROBE INDICATORS ─── */
  .probe-grid { display: flex; flex-direction: column; gap: 10px; }

  .probe-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: #060a0e;
    border: 1px solid var(--border);
    border-radius: 7px;
  }

  .probe-icon {
    font-size: 16px;
    flex-shrink: 0;
  }

  .probe-info { flex: 1; }
  .probe-name { font-size: 12px; color: var(--text); font-weight: 500; }
  .probe-path { font-size: 10px; color: var(--text-dim); margin-top: 2px; }

  .probe-state {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 99px;
    letter-spacing: 0.04em;
  }
  .probe-state.ok {
    background: var(--green-dim);
    color: var(--green);
    border: 1px solid #00ff8830;
  }
  .probe-state.checking {
    background: var(--amber-dim);
    color: var(--amber);
    border: 1px solid #ffb80030;
    animation: blink 1s infinite;
  }
  .probe-state.fail {
    background: rgba(255,68,88,0.1);
    color: var(--red);
    border: 1px solid rgba(255,68,88,0.3);
  }

  /* ─── TERMINAL LOG ─── */
  .log-area {
    background: #060a0e;
    border: 1px solid var(--border);
    border-radius: 7px;
    padding: 12px;
    height: 160px;
    overflow-y: auto;
    font-size: 11px;
    line-height: 1.8;
  }
  .log-area::-webkit-scrollbar { width: 4px; }
  .log-area::-webkit-scrollbar-track { background: transparent; }
  .log-area::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .log-line { display: flex; gap: 8px; }
  .log-time { color: var(--text-dim); flex-shrink: 0; }
  .log-level-info { color: var(--cyan); }
  .log-level-ok   { color: var(--green); }
  .log-level-warn { color: var(--amber); }
  .log-msg        { color: var(--text-muted); }

  /* ─── FULL WIDTH PANEL ─── */
  .full-panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 1rem;
  }

  /* ─── ENV TABLE ─── */
  .env-table { width: 100%; border-collapse: collapse; }
  .env-table tr { border-bottom: 1px solid var(--border); }
  .env-table tr:last-child { border-bottom: none; }
  .env-table td { padding: 10px 14px; font-size: 12px; }
  .env-table td:first-child { color: var(--cyan); width: 40%; }
  .env-table td:last-child  { color: var(--green); }

  /* ─── ANIMATIONS ─── */
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
  }
  @keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 0 0 rgba(0,255,136,0.2); }
    50%       { box-shadow: 0 0 0 4px rgba(0,255,136,0); }
  }
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .fade-in { animation: fadeIn 0.4s ease forwards; }

  .spinner {
    display: inline-block;
    width: 10px; height: 10px;
    border: 1.5px solid var(--border);
    border-top-color: var(--cyan);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    vertical-align: middle;
    margin-right: 6px;
  }

  /* ─── FOOTER ─── */
  .footer {
    margin-top: 2rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .footer-left { font-size: 11px; color: var(--text-dim); }
  .footer-left span { color: var(--green); }
  .uptime-counter { font-size: 11px; color: var(--text-dim); font-family: 'JetBrains Mono', monospace; }
</style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <div class="prompt-line"><span>ubuntu@k3s-cluster</span>:~/devops-challenge$</div>
      <div class="name">Swapnil</div>
      <div class="title-tag">Aspiring DevOps Engineer</div>
    </div>
    <div class="status-pill">
      <span class="status-dot"></span>
      SYSTEM OPERATIONAL
    </div>
  </div>

  <!-- METRICS -->
  <div class="metrics" id="metrics">
    <div class="metric green">
      <div class="metric-label">// total requests</div>
      <div class="metric-value" id="hit-count">—</div>
      <div class="metric-sub">since pod start</div>
    </div>
    <div class="metric cyan">
      <div class="metric-label">// hostname</div>
      <div class="metric-value" style="font-size:1.1rem;padding-top:0.55rem" id="hostname-val">—</div>
      <div class="metric-sub">pod identity</div>
    </div>
    <div class="metric amber">
      <div class="metric-label">// uptime</div>
      <div class="metric-value" style="font-size:1.4rem;padding-top:0.3rem" id="uptime-val">00:00:00</div>
      <div class="metric-sub">hh:mm:ss</div>
    </div>
  </div>

  <!-- MAIN GRID -->
  <div class="grid">

    <!-- ENDPOINTS -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-dots"><span></span><span></span><span></span></div>
        <div class="panel-title">api_endpoints.py</div>
      </div>
      <div class="panel-body">
        <div class="endpoint-list">
          <a class="endpoint" onclick="callEndpoint('/', this)">
            <span class="method-badge">GET</span>
            <span class="endpoint-path">/</span>
            <span class="endpoint-desc">index · hit counter</span>
          </a>
          <a class="endpoint" onclick="callEndpoint('/health', this)">
            <span class="method-badge">GET</span>
            <span class="endpoint-path">/health</span>
            <span class="endpoint-desc">liveness probe</span>
          </a>
          <a class="endpoint" onclick="callEndpoint('/ready', this)">
            <span class="method-badge">GET</span>
            <span class="endpoint-path">/ready</span>
            <span class="endpoint-desc">readiness probe</span>
          </a>
        </div>
      </div>
    </div>

    <!-- RESPONSE VIEWER -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-dots"><span></span><span></span><span></span></div>
        <div class="panel-title">response_viewer.json</div>
      </div>
      <div class="panel-body">
        <div class="response-box" id="response-box">
          <span class="response-placeholder">// Click an endpoint to fire a request...</span>
          <span class="response-status" id="res-status" style="display:none"></span>
        </div>
      </div>
    </div>

    <!-- PROBES -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-dots"><span></span><span></span><span></span></div>
        <div class="panel-title">k8s_probes.yaml</div>
      </div>
      <div class="panel-body">
        <div class="probe-grid">
          <div class="probe-row">
            <span class="probe-icon">🫀</span>
            <div class="probe-info">
              <div class="probe-name">Liveness Probe</div>
              <div class="probe-path">httpGet /health — every 10s</div>
            </div>
            <span class="probe-state" id="liveness-state">CHECKING</span>
          </div>
          <div class="probe-row">
            <span class="probe-icon">✅</span>
            <div class="probe-info">
              <div class="probe-name">Readiness Probe</div>
              <div class="probe-path">httpGet /ready — every 5s</div>
            </div>
            <span class="probe-state" id="readiness-state">CHECKING</span>
          </div>
          <div class="probe-row">
            <span class="probe-icon">🗄️</span>
            <div class="probe-info">
              <div class="probe-name">Redis Connection</div>
              <div class="probe-path">host: redis-service:6379</div>
            </div>
            <span class="probe-state" id="redis-state">CHECKING</span>
          </div>
        </div>
      </div>
    </div>

    <!-- LIVE LOG -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-dots"><span></span><span></span><span></span></div>
        <div class="panel-title">stdout.log</div>
      </div>
      <div class="panel-body">
        <div class="log-area" id="log-area"></div>
      </div>
    </div>

  </div>

  <!-- ENV VARS -->
  <div class="full-panel">
    <div class="panel-header">
      <div class="panel-dots"><span></span><span></span><span></span></div>
      <div class="panel-title">environment_variables.env</div>
    </div>
    <div style="padding:0.5rem 0">
      <table class="env-table" id="env-table">
        <tr><td>REDIS_HOST</td><td id="env-redis">loading...</td></tr>
        <tr><td>HOSTNAME</td><td id="env-hostname">loading...</td></tr>
        <tr><td>FLASK_ENV</td><td>production</td></tr>
        <tr><td>PORT</td><td>5000</td></tr>
      </table>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <div class="footer-left">Built with <span>Flask + Redis + Kubernetes</span> · k3s on AWS EC2</div>
    <div class="uptime-counter" id="uptime-footer">uptime: 00:00:00</div>
  </div>

</div>

<script>
const startTime = Date.now();

// ─── UPTIME COUNTER ───
function formatUptime(ms) {
  const s = Math.floor(ms/1000);
  const h = String(Math.floor(s/3600)).padStart(2,'0');
  const m = String(Math.floor((s%3600)/60)).padStart(2,'0');
  const sec = String(s%60).padStart(2,'0');
  return `${h}:${m}:${sec}`;
}
setInterval(() => {
  const t = formatUptime(Date.now()-startTime);
  document.getElementById('uptime-val').textContent = t;
  document.getElementById('uptime-footer').textContent = 'uptime: '+t;
}, 1000);

// ─── LOGGER ───
function log(level, msg) {
  const area = document.getElementById('log-area');
  const now = new Date().toTimeString().split(' ')[0];
  const cls = { INFO:'log-level-info', OK:'log-level-ok', WARN:'log-level-warn' }[level] || 'log-level-info';
  const line = document.createElement('div');
  line.className = 'log-line fade-in';
  line.innerHTML = `<span class="log-time">${now}</span><span class="${cls}">[${level}]</span><span class="log-msg">${msg}</span>`;
  area.appendChild(line);
  area.scrollTop = area.scrollHeight;
}

// ─── JSON SYNTAX HIGHLIGHT ───
function highlight(obj) {
  const json = JSON.stringify(obj, null, 2);
  return json
    .replace(/("[\w]+")\s*:/g, '<span class="json-key">$1</span>:')
    .replace(/:\s*(".*?")/g, ': <span class="json-str">$1</span>')
    .replace(/:\s*(\d+)/g, ': <span class="json-num">$1</span>')
    .replace(/:\s*(true|false)/g, ': <span class="json-bool">$1</span>')
    .replace(/[{}]/g, m => `<span class="json-brace">${m}</span>`);
}

// ─── CALL ENDPOINT ───
async function callEndpoint(path, el) {
  const box = document.getElementById('response-box');
  const statusEl = document.getElementById('res-status');
  box.innerHTML = `<span class="spinner"></span><span style="color:var(--text-dim)">calling ${path}...</span>`;
  statusEl.style.display = 'none';
  log('INFO', `GET ${path} → request sent`);

  try {
    const res = await fetch(path);
    const data = await res.json();
    const statusColor = res.ok ? 'var(--green)' : 'var(--red)';
    box.innerHTML = `<pre style="white-space:pre-wrap">${highlight(data)}</pre>`;
    statusEl.style.display = 'block';
    statusEl.style.color = statusColor;
    statusEl.textContent = `${res.status} ${res.statusText}`;
    box.classList.add('fade-in');
    log('OK', `GET ${path} → ${res.status} ${res.statusText}`);

    // Update metrics if root endpoint
    if (path === '/' && data.hits !== undefined) {
      document.getElementById('hit-count').textContent = data.hits;
      document.getElementById('hostname-val').textContent = data.hostname.split('-').slice(-1)[0];
      document.getElementById('env-hostname').textContent = data.hostname;
    }
  } catch(e) {
    box.innerHTML = `<span style="color:var(--red)">// Connection error: ${e.message}</span>`;
    log('WARN', `GET ${path} → connection error`);
  }
}

// ─── PROBE POLLING ───
async function pollProbe(path, stateId, label) {
  const el = document.getElementById(stateId);
  try {
    const res = await fetch(path);
    const ok = res.ok;
    el.textContent = ok ? 'HEALTHY' : 'FAILING';
    el.className = `probe-state ${ok ? 'ok' : 'fail'}`;
    log(ok ? 'OK' : 'WARN', `${label} probe → ${ok ? 'healthy' : 'failing'}`);
  } catch(e) {
    el.textContent = 'OFFLINE';
    el.className = 'probe-state fail';
    log('WARN', `${label} probe → unreachable`);
  }
}

async function pollAll() {
  await pollProbe('/health', 'liveness-state', 'liveness');
  await pollProbe('/ready', 'readiness-state', 'readiness');
  // Redis status reflected through /ready
  const readinessEl = document.getElementById('readiness-state');
  const redisEl = document.getElementById('redis-state');
  redisEl.textContent = readinessEl.textContent === 'HEALTHY' ? 'CONNECTED' : 'DISCONNECTED';
  redisEl.className = `probe-state ${readinessEl.textContent === 'HEALTHY' ? 'ok' : 'fail'}`;
}

// ─── INITIAL LOAD ───
async function init() {
  log('INFO', 'dashboard initialized');
  log('INFO', 'REDIS_HOST=redis-service · PORT=5000');

  // Fetch root to populate metrics
  try {
    const res = await fetch('/');
    const data = await res.json();
    document.getElementById('hit-count').textContent = data.hits;
    document.getElementById('hostname-val').textContent = data.hostname.split('-').slice(-1)[0];
    document.getElementById('env-hostname').textContent = data.hostname;
    document.getElementById('env-redis').textContent = 'redis-service';
    log('OK', `service up · hostname=${data.hostname}`);
  } catch(e) {
    log('WARN', 'could not fetch root endpoint');
  }

  // Initial probe check
  await pollAll();

  // Poll probes every 10s
  setInterval(pollAll, 10000);
  log('INFO', 'probe polling active every 10s');
}

init();
</script>
</body>
</html>'''

@app.route('/')
def index():
    r.incr('hits')
    hits = r.get('hits')
    return jsonify({
        "message": "Hello I'm Swapnil, An aspiring DevOps Engineer!",
        "hits": hits,
        "hostname": os.getenv('HOSTNAME', 'unknown')
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ready')
def ready():
    try:
        r.ping()
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "not ready"}), 503

@app.route('/ui')
def ui():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
