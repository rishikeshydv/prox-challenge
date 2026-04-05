"""
duty_cycle_calculator.py — Arc gauge + tall time bar with inside labels + comparison bar chart.
"""

import json


def render_duty_cycle_widget(spec: dict) -> str:
    data         = spec.get("duty_cycle_data", [])
    source_pages = spec.get("source_pages", [])

    voltages   = sorted(set(d["voltage_input"] for d in data))
    processes  = sorted(set(d["process"] for d in data))

    data_json      = json.dumps(data)
    voltages_json  = json.dumps(voltages)
    processes_json = json.dumps(processes)
    pages_str      = ", ".join(str(p) for p in source_pages)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #f8fafc;
    color: #111827;
    padding: 16px;
  }}
  h2 {{ font-size: 17px; font-weight: 700; margin-bottom: 2px; }}
  .sub {{ font-size: 12px; color: #6b7280; margin-bottom: 14px; }}
  .controls {{ display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; }}
  select {{
    background: #fff;
    color: #111827;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
    cursor: pointer;
  }}
  select:focus {{ outline: 2px solid #2563eb; outline-offset: 1px; }}
  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(6px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}
  @keyframes barGrow {{
    from {{ width: 0 !important; }}
  }}

  /* ── Detail card ── */
  .card {{
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 18px 20px;
    display: flex;
    align-items: center;
    gap: 22px;
    margin-bottom: 16px;
  }}
  .gauge-wrap {{ flex-shrink: 0; }}
  .info {{ flex: 1; min-width: 0; }}
  .amperage {{ font-size: 26px; font-weight: 700; color: #111827; line-height: 1; }}
  .subtitle  {{ font-size: 12px; color: #6b7280; margin: 4px 0 14px; }}

  /* Tall time bar */
  .bar-wrap {{ position: relative; height: 28px; border-radius: 8px; overflow: hidden; display: flex; }}
  .bar-on  {{ background: #2563eb; display: flex; align-items: center; justify-content: flex-start; padding-left: 8px; transition: width 0.9s cubic-bezier(0.4,0,0.2,1); }}
  .bar-off {{ background: #e5e7eb; flex: 1; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; }}
  .bar-lbl {{ font-size: 11px; font-weight: 600; white-space: nowrap; }}
  .bar-lbl.on  {{ color: #fff; }}
  .bar-lbl.off {{ color: #9ca3af; }}
  .bar-title {{ font-size: 11px; color: #6b7280; margin-bottom: 5px; }}

  /* ── Comparison chart ── */
  .chart-section {{ margin-top: 4px; }}
  .chart-title {{ font-size: 12px; font-weight: 600; color: #374151; margin-bottom: 10px; }}
  .chart-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }}
  .chart-amp {{ font-size: 12px; color: #6b7280; width: 44px; text-align: right; flex-shrink: 0; }}
  .chart-bar-bg {{ flex: 1; background: #f3f4f6; border-radius: 5px; height: 18px; overflow: hidden; position: relative; cursor: pointer; }}
  .chart-bar-fill {{ height: 100%; border-radius: 5px; display: flex; align-items: center; padding-left: 8px; transition: width 0.7s cubic-bezier(0.4,0,0.2,1), opacity 0.15s; }}
  .chart-bar-fill:hover {{ opacity: 0.85; }}
  .chart-bar-pct {{ font-size: 11px; font-weight: 600; color: #fff; white-space: nowrap; }}
  .chart-row.active .chart-bar-bg {{ box-shadow: 0 0 0 2px #2563eb; }}

  .empty  {{ color: #9ca3af; font-size: 14px; padding: 24px 0; text-align: center; }}
  .source {{ font-size: 11px; color: #9ca3af; margin-top: 16px; text-align: center; }}
</style>
</head>
<body>

<h2>Duty Cycle</h2>
<div class="sub">Vulcan OmniPro 220 — select voltage and process</div>

<div class="controls">
  <select id="voltSel" onchange="update()"></select>
  <select id="procSel" onchange="update()"></select>
</div>

<div id="detail"></div>
<div id="chart" class="chart-section"></div>
<div class="source">Source: Manual pages {pages_str}</div>

<script>
const data      = {data_json};
const voltages  = {voltages_json};
const processes = {processes_json};

const voltSel = document.getElementById('voltSel');
const procSel = document.getElementById('procSel');
voltages.forEach(v  => {{ const o = document.createElement('option'); o.value = v; o.textContent = v; voltSel.appendChild(o); }});
processes.forEach(p => {{ const o = document.createElement('option'); o.value = p; o.textContent = p; procSel.appendChild(o); }});

let selectedAmp = null;

// ── SVG arc gauge ────────────────────────────────────────────────────────────
const R = 48, CX = 56, CY = 56;
const CIRC = 2 * Math.PI * R;
const GAP  = 22;
const ARC  = CIRC * (1 - GAP / 360);

function color(pct) {{
  return pct >= 60 ? '#2563eb' : pct >= 30 ? '#d97706' : '#dc2626';
}}

function arcGauge(pct) {{
  const c      = color(pct);
  const filled = ARC * (pct / 100);
  const rot    = 90 + GAP / 2;
  const arcId  = 'arc-' + Math.random().toString(36).slice(2);
  // Animate arc from 0 after first paint
  setTimeout(() => {{
    const el = document.getElementById(arcId);
    if (el) {{
      el.style.transition = 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)';
      el.setAttribute('stroke-dasharray', `${{filled}} ${{CIRC - filled}}`);
    }}
  }}, 60);
  return `<svg width="112" height="112" viewBox="0 0 112 112">
    <circle cx="${{CX}}" cy="${{CY}}" r="${{R}}" fill="none" stroke="#e5e7eb" stroke-width="11"
      stroke-dasharray="${{ARC}} ${{CIRC - ARC}}" stroke-linecap="round"
      transform="rotate(${{rot}} ${{CX}} ${{CY}})"/>
    <circle id="${{arcId}}" cx="${{CX}}" cy="${{CY}}" r="${{R}}" fill="none" stroke="${{c}}" stroke-width="11"
      stroke-dasharray="0 ${{CIRC}}" stroke-linecap="round"
      transform="rotate(${{rot}} ${{CX}} ${{CY}})"/>
    <text x="${{CX}}" y="${{CY - 5}}" text-anchor="middle"
      font-family="system-ui" font-size="20" font-weight="700" fill="${{c}}">${{pct}}%</text>
    <text x="${{CX}}" y="${{CY + 11}}" text-anchor="middle"
      font-family="system-ui" font-size="9" fill="#6b7280">duty cycle</text>
  </svg>`;
}}

function renderDetail(d) {{
  const pct    = d.duty_cycle_percent;
  const onMin  = (pct / 10).toFixed(1);
  const offMin = (10 - pct / 10).toFixed(1);
  const onPct  = Math.max(8, pct);
  const voltOut = d.voltage_output ? ` @ ${{d.voltage_output}}V` : '';
  const onLbl  = onMin + ' min welding';
  const offLbl = offMin + ' min cool';

  document.getElementById('detail').innerHTML = `
    <div class="card">
      <div class="gauge-wrap">${{arcGauge(pct)}}</div>
      <div class="info">
        <div class="amperage">${{d.amperage}}A${{voltOut}}</div>
        <div class="subtitle">${{procSel.value}} · ${{voltSel.value}}</div>
        <div class="bar-title">10-minute cycle</div>
        <div class="bar-wrap">
          <div class="bar-on"  style="width:${{onPct}}%">
            <span class="bar-lbl on">${{onLbl}}</span>
          </div>
          <div class="bar-off">
            <span class="bar-lbl off">${{offLbl}}</span>
          </div>
        </div>
      </div>
    </div>`;
}}

function renderChart(matches) {{
  if (matches.length < 2) {{
    document.getElementById('chart').innerHTML = '';
    return;
  }}
  const sorted = [...matches].sort((a, b) => b.amperage - a.amperage);
  const rows = sorted.map(d => {{
    const pct = d.duty_cycle_percent;
    const c   = color(pct);
    const isActive = selectedAmp === d.amperage;
    return `<div class="chart-row ${{isActive ? 'active' : ''}}" onclick="selectAmp(${{d.amperage}})">
      <div class="chart-amp">${{d.amperage}}A</div>
      <div class="chart-bar-bg">
        <div class="chart-bar-fill" style="width:${{pct}}%; background:${{c}}">
          <span class="chart-bar-pct">${{pct}}%</span>
        </div>
      </div>
    </div>`;
  }}).join('');

  const chartEl = document.getElementById('chart');
  chartEl.innerHTML = `
    <div class="chart-title">All amperage settings — click to select</div>
    ${{rows}}`;
  // Animate bars from 0 → target width
  chartEl.querySelectorAll('.chart-bar-fill').forEach((el, i) => {{
    const target = el.style.width;
    el.style.width = '0';
    el.style.transitionDelay = `${{i * 0.06}}s`;
    requestAnimationFrame(() => requestAnimationFrame(() => {{ el.style.width = target; }}));
  }});
}}

function selectAmp(amp) {{
  const volt    = voltSel.value;
  const proc    = procSel.value;
  const matches = data.filter(d => d.voltage_input === volt && d.process === proc);
  const d       = matches.find(d => d.amperage === amp);
  if (d) {{ selectedAmp = amp; renderDetail(d); renderChart(matches); }}
}}

function update() {{
  const volt    = voltSel.value;
  const proc    = procSel.value;
  const matches = data.filter(d => d.voltage_input === volt && d.process === proc);

  if (!matches.length) {{
    document.getElementById('detail').innerHTML = '<div class="empty">No data for this combination in the manual.</div>';
    document.getElementById('chart').innerHTML  = '';
    return;
  }}

  // Default: show highest amperage entry
  const sorted = [...matches].sort((a, b) => b.amperage - a.amperage);
  selectedAmp  = sorted[0].amperage;
  renderDetail(sorted[0]);
  renderChart(matches);
}}

update();
</script>
</body>
</html>"""
