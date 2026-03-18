from flask import Blueprint, render_template_string, jsonify, request
from datetime import date
from app.extensions import db
from app.models import AllocationRun, Assignment, Agent, Warehouse, Order

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@dashboard_bp.route('/api/dashboard/stats')
def dashboard_stats():
    date_str = request.args.get('date', str(date.today()))
    try:
        target_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({'error': 'invalid date'}), 400

    run = AllocationRun.query.filter_by(run_date=target_date).order_by(
        AllocationRun.id.desc()
    ).first()

    total_orders = Order.query.filter(Order.scheduled_date == target_date).count()
    total_agents = Agent.query.filter_by(is_active=True).count()
    total_warehouses = Warehouse.query.count()

    # Order status distribution
    status_counts = (
        db.session.query(Order.status, db.func.count(Order.id))
        .filter(Order.scheduled_date <= target_date)
        .group_by(Order.status)
        .all()
    )
    status_dist = {s: c for s, c in status_counts}

    # Tier breakdown per agent
    tier_data = {'tier2': 0, 'tier1': 0, 'guarantee': 0, 'idle': 0}
    agent_counts = (
        db.session.query(
            Agent.id,
            db.func.count(Assignment.id).label('cnt')
        )
        .outerjoin(Assignment, (Assignment.agent_id == Agent.id) &
                   (Assignment.assignment_date == target_date))
        .group_by(Agent.id)
        .all()
    )
    for _, cnt in agent_counts:
        if cnt >= 50:
            tier_data['tier2'] += 1
        elif cnt >= 25:
            tier_data['tier1'] += 1
        elif cnt > 0:
            tier_data['guarantee'] += 1
        else:
            tier_data['idle'] += 1

    # Per-warehouse summary
    wh_summary = []
    warehouses = Warehouse.query.all()
    for wh in warehouses:
        assigned = (
            db.session.query(db.func.count(Assignment.id))
            .join(Order, Order.id == Assignment.order_id)
            .filter(
                Order.warehouse_id == wh.id,
                Assignment.assignment_date == target_date,
            )
            .scalar() or 0
        )
        pending = Order.query.filter_by(
            warehouse_id=wh.id, status='pending', scheduled_date=target_date
        ).count()
        deferred = Order.query.filter_by(
            warehouse_id=wh.id, status='deferred'
        ).count()

        wh_summary.append({
            'name': wh.name.replace('WH-', ''),
            'assigned': assigned,
            'pending': pending,
            'deferred': deferred,
            'lat': wh.latitude,
            'lon': wh.longitude,
        })

    return jsonify({
        'run': run.to_dict() if run else None,
        'totals': {
            'orders': total_orders,
            'agents': total_agents,
            'warehouses': total_warehouses,
        },
        'status_dist': status_dist,
        'tier_data': tier_data,
        'wh_summary': wh_summary,
    })


# ── Embedded Dashboard HTML ───────────────────────────────────────────────────
DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DeliverIQ — Allocation Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0e1a;
    --surface: #111827;
    --border: #1e2a3a;
    --accent: #00e5ff;
    --accent2: #ff6b35;
    --green: #00c9a7;
    --yellow: #ffd166;
    --text: #e2e8f0;
    --muted: #64748b;
    --card: #151f2e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: 'DM Sans', sans-serif; min-height: 100vh; }

  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
  }
  .logo { font-family: 'Space Mono', monospace; font-size: 1.3rem; color: var(--accent); letter-spacing: -1px; }
  .logo span { color: var(--accent2); }
  .topbar-right { display: flex; gap: 12px; align-items: center; }
  .date-badge { background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 14px; font-size: .85rem; color: var(--muted); }
  .btn { background: var(--accent); color: #000; border: none; border-radius: 8px; padding: 8px 18px; font-family: 'Space Mono', monospace; font-size: .8rem; cursor: pointer; font-weight: 700; transition: opacity .2s; }
  .btn:hover { opacity: .8; }
  .btn.secondary { background: var(--surface); color: var(--accent); border: 1px solid var(--accent); }
  .btn.danger { background: var(--accent2); color: #fff; }

  main { padding: 28px 32px; max-width: 1400px; }

  .kpi-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 28px; }
  .kpi { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 20px; position: relative; overflow: hidden; }
  .kpi::before { content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%; background: var(--accent); }
  .kpi.green::before { background: var(--green); }
  .kpi.orange::before { background: var(--accent2); }
  .kpi.yellow::before { background: var(--yellow); }
  .kpi-label { font-size: .75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .kpi-value { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; color: var(--text); line-height: 1; }
  .kpi-sub { font-size: .75rem; color: var(--muted); margin-top: 6px; }

  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 24px; }

  .panel { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 22px; }
  .panel h3 { font-family: 'Space Mono', monospace; font-size: .85rem; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 18px; }

  .chart-wrap { position: relative; height: 220px; }

  table { width: 100%; border-collapse: collapse; font-size: .85rem; }
  th { text-align: left; color: var(--muted); font-size: .75rem; text-transform: uppercase; letter-spacing: .5px; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 10px; border-bottom: 1px solid rgba(30,42,58,.5); color: var(--text); }
  tr:last-child td { border-bottom: none; }
  .badge { display: inline-block; border-radius: 6px; padding: 2px 10px; font-size: .75rem; font-weight: 600; }
  .badge.tier2 { background: rgba(0,229,255,.15); color: var(--accent); }
  .badge.tier1 { background: rgba(0,201,167,.15); color: var(--green); }
  .badge.guarantee { background: rgba(255,209,102,.15); color: var(--yellow); }
  .badge.idle { background: rgba(100,116,139,.15); color: var(--muted); }
  .badge.assigned { background: rgba(0,201,167,.15); color: var(--green); }
  .badge.deferred { background: rgba(255,107,53,.15); color: var(--accent2); }
  .badge.pending { background: rgba(255,209,102,.15); color: var(--yellow); }

  .status-bar { display: flex; gap: 6px; margin-top: 10px; }
  .status-seg { height: 8px; border-radius: 4px; transition: width .5s ease; }

  .alert { background: rgba(0,229,255,.07); border: 1px solid rgba(0,229,255,.3); border-radius: 10px; padding: 14px 18px; margin-bottom: 24px; font-size: .9rem; color: var(--accent); display: none; }

  #loading { position: fixed; inset: 0; background: var(--bg); display: flex; align-items: center; justify-content: center; z-index: 100; flex-direction: column; gap: 16px; }
  .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }

  @media(max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } main { padding: 16px; } }
</style>
</head>
<body>

<div id="loading">
  <div class="spinner"></div>
  <div style="font-family:'Space Mono',monospace;color:var(--muted);font-size:.85rem">LOADING DELIVERIQ...</div>
</div>

<div class="topbar">
  <div class="logo">Deliver<span>IQ</span></div>
  <div class="topbar-right">
    <input type="date" id="dateInput" class="date-badge" style="background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 14px;font-size:.85rem;cursor:pointer">
    <button class="btn secondary" onclick="loadStats()">↻ Refresh</button>
    <button class="btn danger" onclick="triggerAllocation()">▶ Run Allocation</button>
    <button class="btn" onclick="seedData()">⚡ Seed Data</button>
  </div>
</div>

<main>
  <div class="alert" id="alertBox"></div>

  <!-- KPI Row -->
  <div class="kpi-row">
    <div class="kpi"><div class="kpi-label">Total Orders</div><div class="kpi-value" id="kpi-total">—</div><div class="kpi-sub">today's pool</div></div>
    <div class="kpi green"><div class="kpi-label">Assigned</div><div class="kpi-value" id="kpi-assigned">—</div><div class="kpi-sub" id="kpi-assigned-pct">—</div></div>
    <div class="kpi orange"><div class="kpi-label">Deferred</div><div class="kpi-value" id="kpi-deferred">—</div><div class="kpi-sub">to next day</div></div>
    <div class="kpi yellow"><div class="kpi-label">Active Agents</div><div class="kpi-value" id="kpi-agents">—</div><div class="kpi-sub" id="kpi-warehouses">— warehouses</div></div>
    <div class="kpi"><div class="kpi-label">Total Cost</div><div class="kpi-value" id="kpi-cost">—</div><div class="kpi-sub">agent payouts</div></div>
    <div class="kpi green"><div class="kpi-label">Avg Orders/Agent</div><div class="kpi-value" id="kpi-avg-orders">—</div><div class="kpi-sub" id="kpi-avg-km">— km avg</div></div>
  </div>

  <!-- Status bar -->
  <div class="panel" style="margin-bottom:24px;padding:18px 22px;">
    <h3>Order Status Distribution</h3>
    <div class="status-bar" id="statusBar"></div>
    <div style="display:flex;gap:20px;margin-top:12px;font-size:.8rem;color:var(--muted)" id="statusLegend"></div>
  </div>

  <!-- Charts row -->
  <div class="grid-2">
    <div class="panel">
      <h3>Agent Tier Distribution</h3>
      <div class="chart-wrap"><canvas id="tierChart"></canvas></div>
    </div>
    <div class="panel">
      <h3>Orders per Warehouse</h3>
      <div class="chart-wrap"><canvas id="whChart"></canvas></div>
    </div>
  </div>

  <!-- Warehouse table -->
  <div class="panel">
    <h3>Warehouse Summary</h3>
    <table>
      <thead><tr><th>Warehouse</th><th>Assigned</th><th>Pending</th><th>Deferred</th><th>Fill Rate</th></tr></thead>
      <tbody id="whTable"></tbody>
    </table>
  </div>
</main>

<script>
let tierChart = null;
let whChart = null;

function today() {
  return new Date().toISOString().slice(0,10);
}

document.getElementById('dateInput').value = today();

function showAlert(msg, isError=false) {
  const box = document.getElementById('alertBox');
  box.style.display = 'block';
  box.style.color = isError ? 'var(--accent2)' : 'var(--accent)';
  box.style.borderColor = isError ? 'rgba(255,107,53,.4)' : 'rgba(0,229,255,.3)';
  box.style.background = isError ? 'rgba(255,107,53,.07)' : 'rgba(0,229,255,.07)';
  box.textContent = msg;
  setTimeout(() => box.style.display = 'none', 4000);
}

async function loadStats() {
  const d = document.getElementById('dateInput').value || today();
  try {
    const res = await fetch(`/api/dashboard/stats?date=${d}`);
    const data = await res.json();
    renderDashboard(data);
    document.getElementById('loading').style.display = 'none';
  } catch(e) {
    showAlert('Failed to load stats: ' + e.message, true);
    document.getElementById('loading').style.display = 'none';
  }
}

function fmt(n) { return (n||0).toLocaleString('en-IN'); }
function pct(a,b) { return b ? Math.round(a/b*100) + '%' : '0%'; }

function renderDashboard(data) {
  const run = data.run || {};
  const totals = data.totals || {};
  const tier = data.tier_data || {};
  const whs = data.wh_summary || [];
  const sd = data.status_dist || {};

  // KPIs
  const assigned = run.assigned_orders || 0;
  const total = run.total_orders || totals.orders || 0;
  const deferred = run.deferred_orders || 0;

  document.getElementById('kpi-total').textContent = fmt(total);
  document.getElementById('kpi-assigned').textContent = fmt(assigned);
  document.getElementById('kpi-assigned-pct').textContent = pct(assigned, total) + ' fill rate';
  document.getElementById('kpi-deferred').textContent = fmt(deferred);
  document.getElementById('kpi-agents').textContent = fmt(run.total_agents || totals.agents);
  document.getElementById('kpi-warehouses').textContent = (totals.warehouses||0) + ' warehouses';
  document.getElementById('kpi-cost').textContent = '₹' + fmt(Math.round(run.total_cost||0));
  document.getElementById('kpi-avg-orders').textContent = run.avg_orders_per_agent ? run.avg_orders_per_agent.toFixed(1) : '—';
  document.getElementById('kpi-avg-km').textContent = run.avg_km_per_agent ? run.avg_km_per_agent.toFixed(1) : '—';

  // Status bar
  const statuses = [
    { key: 'assigned', label: 'Assigned', color: 'var(--green)' },
    { key: 'pending',  label: 'Pending',  color: 'var(--yellow)' },
    { key: 'deferred', label: 'Deferred', color: 'var(--accent2)' },
    { key: 'delivered',label: 'Delivered',color: 'var(--accent)' },
  ];
  const totalStatus = Object.values(sd).reduce((a,b)=>a+b,0)||1;
  document.getElementById('statusBar').innerHTML = statuses.map(s => {
    const val = sd[s.key]||0;
    return `<div class="status-seg" style="background:${s.color};width:${pct(val,totalStatus)};min-width:${val?'4px':'0'}" title="${s.label}: ${val}"></div>`;
  }).join('');
  document.getElementById('statusLegend').innerHTML = statuses.map(s => {
    const val = sd[s.key]||0;
    return `<span style="color:${s.color}">● ${s.label}: <b>${fmt(val)}</b></span>`;
  }).join('');

  // Tier doughnut
  const tierLabels = ['₹42/order (50+)', '₹35/order (25-49)', 'Guarantee (<25)', 'Idle'];
  const tierValues = [tier.tier2||0, tier.tier1||0, tier.guarantee||0, tier.idle||0];
  const tierColors = ['#00e5ff','#00c9a7','#ffd166','#1e2a3a'];
  if(tierChart) tierChart.destroy();
  tierChart = new Chart(document.getElementById('tierChart'), {
    type: 'doughnut',
    data: { labels: tierLabels, datasets: [{ data: tierValues, backgroundColor: tierColors, borderWidth: 0, hoverOffset: 4 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#64748b', font: { family: 'DM Sans', size: 11 } } } }
    }
  });

  // Warehouse bar chart
  if(whChart) whChart.destroy();
  whChart = new Chart(document.getElementById('whChart'), {
    type: 'bar',
    data: {
      labels: whs.map(w=>w.name),
      datasets: [
        { label: 'Assigned', data: whs.map(w=>w.assigned), backgroundColor: 'rgba(0,201,167,.7)', borderRadius: 4 },
        { label: 'Deferred', data: whs.map(w=>w.deferred), backgroundColor: 'rgba(255,107,53,.6)', borderRadius: 4 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#64748b', font: { size: 11 } } } },
      scales: {
        x: { stacked: true, ticks: { color: '#64748b', font: { size: 10 } }, grid: { color: 'rgba(30,42,58,.5)' } },
        y: { stacked: true, ticks: { color: '#64748b' }, grid: { color: 'rgba(30,42,58,.5)' } },
      }
    }
  });

  // Warehouse table
  document.getElementById('whTable').innerHTML = whs.map(w => {
    const total = w.assigned + w.pending + w.deferred;
    const fillPct = total ? Math.round(w.assigned/total*100) : 0;
    return `<tr>
      <td><b>${w.name}</b></td>
      <td><span class="badge assigned">${fmt(w.assigned)}</span></td>
      <td><span class="badge pending">${fmt(w.pending)}</span></td>
      <td><span class="badge deferred">${fmt(w.deferred)}</span></td>
      <td>
        <div style="display:flex;align-items:center;gap:10px">
          <div style="flex:1;background:var(--border);border-radius:4px;height:6px">
            <div style="background:var(--green);width:${fillPct}%;height:6px;border-radius:4px"></div>
          </div>
          <span style="font-size:.8rem;color:var(--muted);width:36px">${fillPct}%</span>
        </div>
      </td>
    </tr>`;
  }).join('');
}

async function triggerAllocation() {
  const d = document.getElementById('dateInput').value || today();
  showAlert('⏳ Running allocation job...');
  try {
    const res = await fetch('/api/allocation/run', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({date: d})
    });
    const data = await res.json();
    const m = data.metrics || {};
    showAlert(`✅ Done! Assigned: ${fmt(m.assigned_orders)} | Deferred: ${fmt(m.deferred_orders)} | Cost: ₹${fmt(Math.round(m.total_cost||0))}`);
    loadStats();
  } catch(e) {
    showAlert('Allocation failed: ' + e.message, true);
  }
}

async function seedData() {
  const d = document.getElementById('dateInput').value || today();
  showAlert('⚡ Seeding test data (10 warehouses, 200 agents, ~12,000 orders)...');
  try {
    const res = await fetch('/api/allocation/seed', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({date: d})
    });
    const data = await res.json();
    showAlert(`✅ Seeded! ${data.warehouses} warehouses, ${data.agents} agents, ${data.orders_created} orders`);
    loadStats();
  } catch(e) {
    showAlert('Seed failed: ' + e.message, true);
  }
}

document.getElementById('dateInput').addEventListener('change', loadStats);
loadStats();
</script>
</body>
</html>
"""
