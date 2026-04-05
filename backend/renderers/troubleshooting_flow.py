"""
troubleshooting_flow.py — Clean interactive troubleshooting flow with compact
progress, decision chips, and minimal-copy step cards.
"""

import html as html_mod
import json


def render_troubleshooting_widget(spec: dict) -> str:
    symptom = spec.get("symptom", "Unknown issue")
    steps = spec.get("steps", [])
    source_pages = spec.get("source_pages", [])

    steps_json = json.dumps(steps)
    symptom_escaped = html_mod.escape(symptom)
    pages_str = ", ".join(str(p) for p in source_pages)
    first_id = steps[0]["id"] if steps else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{ height: 100%; }}
  body {{
    min-height: 100%;
    font-family: system-ui, -apple-system, sans-serif;
    background:
      radial-gradient(circle at top right, rgba(59, 130, 246, 0.10), transparent 26%),
      linear-gradient(180deg, #eef3f9, #e5ecf4);
    color: #0f172a;
    padding: 16px;
  }}

  .shell {{
    min-height: calc(100vh - 32px);
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}

  .panel {{
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 26px;
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(246,249,252,0.98));
    box-shadow: 0 18px 56px rgba(15, 23, 42, 0.08);
  }}

  .hero {{
    padding: 18px 20px;
  }}
  .hero-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .eyebrow {{
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    border: 1px solid rgba(245, 158, 11, 0.25);
    background: rgba(245, 158, 11, 0.10);
    color: #b45309;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }}
  .source-pill {{
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.06);
    color: #475569;
    padding: 7px 12px;
    font-size: 12px;
    font-weight: 600;
  }}
  .hero h2 {{
    margin-top: 12px;
    font-size: 24px;
    line-height: 1.1;
    letter-spacing: -0.03em;
  }}
  .progress-row {{
    margin-top: 16px;
    display: grid;
    gap: 8px;
  }}
  .progress-meta {{
    display: flex;
    justify-content: space-between;
    gap: 10px;
    font-size: 12px;
    color: #64748b;
  }}
  .progress-track {{
    height: 10px;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.18);
  }}
  .progress-fill {{
    width: 0%;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    transition: width 0.35s ease;
  }}

  .layout {{
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: 250px minmax(0, 1fr);
    gap: 14px;
  }}

  .sidebar {{
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}
  .mini-stats {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }}
  .stat {{
    border-radius: 18px;
    background: #f8fafc;
    border: 1px solid rgba(148, 163, 184, 0.16);
    padding: 12px;
  }}
  .stat-label {{
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  .stat-value {{
    margin-top: 6px;
    font-size: 20px;
    font-weight: 800;
  }}
  .sidebar-title {{
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #64748b;
  }}
  .path-rail {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .path-chip {{
    border: none;
    border-radius: 999px;
    background: #ffffff;
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #334155;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.12s ease, border-color 0.12s ease;
  }}
  .path-chip:hover {{
    transform: translateY(-1px);
    border-color: rgba(59, 130, 246, 0.30);
  }}
  .path-chip.yes {{ color: #1d4ed8; }}
  .path-chip.no {{ color: #b91c1c; }}
  .empty-state {{
    border-radius: 18px;
    background: rgba(241, 245, 249, 0.88);
    color: #64748b;
    padding: 14px;
    font-size: 13px;
    line-height: 1.5;
  }}
  .restart-btn {{
    margin-top: auto;
    border: none;
    border-radius: 18px;
    background: #0f172a;
    color: #fff;
    padding: 12px 14px;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: transform 0.12s ease, opacity 0.12s ease;
  }}
  .restart-btn:hover {{
    transform: translateY(-1px);
    opacity: 0.94;
  }}

  .workspace {{
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
    justify-content: center;
  }}
  .step-card {{
    border-radius: 28px;
    padding: 22px;
    background: linear-gradient(180deg, #ffffff, #f7fbff);
    border: 1px solid rgba(148, 163, 184, 0.18);
  }}
  .step-top {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
  }}
  .step-kind {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border-radius: 999px;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }}
  .step-kind.question {{ background: rgba(37, 99, 235, 0.10); color: #1d4ed8; }}
  .step-kind.check {{ background: rgba(245, 158, 11, 0.10); color: #b45309; }}
  .step-kind.fix {{ background: rgba(22, 163, 74, 0.10); color: #15803d; }}
  .step-id {{
    font-size: 12px;
    font-weight: 800;
    color: #94a3b8;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }}
  .step-title {{
    margin-top: 18px;
    font-size: 34px;
    line-height: 1.15;
    letter-spacing: -0.04em;
    max-width: 900px;
  }}
  .step-subtitle {{
    margin-top: 10px;
    font-size: 14px;
    line-height: 1.55;
    color: #64748b;
    max-width: 720px;
  }}

  .preview-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 18px;
  }}
  .preview-chip {{
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.06);
    color: #475569;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
  }}

  .actions {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
  }}
  .action-btn {{
    border: none;
    border-radius: 24px;
    padding: 18px;
    text-align: left;
    cursor: pointer;
    transition: transform 0.12s ease, opacity 0.12s ease, box-shadow 0.12s ease;
    box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
  }}
  .action-btn:hover {{
    transform: translateY(-1px);
    opacity: 0.97;
  }}
  .action-btn.yes {{
    background: linear-gradient(180deg, #2563eb, #1d4ed8);
    color: #fff;
  }}
  .action-btn.no {{
    background: linear-gradient(180deg, #ffffff, #f8fafc);
    color: #0f172a;
    border: 1px solid rgba(148, 163, 184, 0.20);
  }}
  .action-btn.continue {{
    grid-column: 1 / -1;
    background: linear-gradient(180deg, #0f172a, #1e293b);
    color: #fff;
  }}
  .action-label {{
    font-size: 18px;
    font-weight: 800;
  }}
  .action-next {{
    margin-top: 8px;
    font-size: 13px;
    line-height: 1.45;
    opacity: 0.88;
  }}

  .fix-card {{
    border-radius: 28px;
    padding: 24px;
    background: linear-gradient(180deg, #effdf5, #f8fff9);
    border: 1px solid rgba(22, 163, 74, 0.18);
  }}
  .fix-kicker {{
    display: inline-flex;
    align-items: center;
    border-radius: 999px;
    background: rgba(22, 163, 74, 0.12);
    color: #15803d;
    padding: 6px 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }}
  .fix-title {{
    margin-top: 16px;
    font-size: 34px;
    line-height: 1.15;
    letter-spacing: -0.04em;
    color: #14532d;
    max-width: 820px;
  }}
  .fix-copy {{
    margin-top: 10px;
    font-size: 15px;
    line-height: 1.65;
    color: #166534;
    max-width: 760px;
  }}
  .fix-path {{
    margin-top: 16px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }}
  .fix-path-chip {{
    border-radius: 999px;
    background: rgba(255,255,255,0.74);
    color: #166534;
    padding: 7px 10px;
    font-size: 12px;
    font-weight: 700;
  }}

  @media (max-width: 980px) {{
    .layout {{
      grid-template-columns: 1fr;
    }}
  }}

  @media (max-width: 720px) {{
    body {{ padding: 10px; }}
    .shell {{ min-height: calc(100vh - 20px); }}
    .hero, .sidebar, .workspace, .step-card, .fix-card {{ padding: 16px; }}
    .actions, .mini-stats {{
      grid-template-columns: 1fr;
    }}
    .step-title, .fix-title {{
      font-size: 26px;
    }}
  }}
</style>
</head>
<body>
<div class="shell">
  <section class="hero panel">
    <div class="hero-top">
      <div class="eyebrow">Troubleshooting</div>
      <div class="source-pill">Manual pages {pages_str}</div>
    </div>
    <h2>{symptom_escaped}</h2>
    <div class="progress-row">
      <div class="progress-meta">
        <span id="progressTitle">Starting path</span>
        <span id="progressStep">Step 1</span>
      </div>
      <div class="progress-track"><div class="progress-fill" id="progressFill"></div></div>
    </div>
  </section>

  <section class="layout">
    <aside class="panel sidebar">
      <div class="mini-stats">
        <div class="stat">
          <div class="stat-label">Current</div>
          <div class="stat-value" id="statCurrent">1</div>
        </div>
        <div class="stat">
          <div class="stat-label">Decisions</div>
          <div class="stat-value" id="statHistory">0</div>
        </div>
      </div>

      <div>
        <div class="sidebar-title">Path</div>
        <div class="path-rail" id="pathRail"></div>
      </div>

      <button class="restart-btn" onclick="restart()">Start Over</button>
    </aside>

    <main class="panel workspace">
      <div id="currentStep"></div>
    </main>
  </section>
</div>

<script>
const steps = {steps_json};
const stepMap = {{}};
steps.forEach((step) => stepMap[step.id] = step);

let currentId = {json.dumps(first_id)};
let history = [];

function escapeHtml(value) {{
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}}

function shortText(value, max = 72) {{
  const text = String(value ?? "").trim();
  if (text.length <= max) return text;
  return text.slice(0, max - 1).trimEnd() + "…";
}}

function kindLabel(type) {{
  if (type === "fix") return "Fix";
  if (type === "check") return "Check";
  return "Question";
}}

function kindSubtitle(type) {{
  if (type === "fix") return "Manual-backed resolution";
  if (type === "check") return "Inspect and choose the matching result";
  return "Answer the prompt to narrow down the cause";
}}

function previewLabel(nextId) {{
  const next = stepMap[nextId];
  if (!next) return "Next step";
  return `${{kindLabel(next.type)}}: ${{shortText(next.fix_text || next.text)}}`;
}}

function progressState(step) {{
  const visited = history.length + 1;
  const isFix = step && step.type === "fix";
  const estimated = Math.max(3, Math.ceil(steps.length * 0.55));
  return {{
    pct: isFix ? 100 : Math.min(92, Math.round((visited / estimated) * 100)),
    title: isFix ? "Resolution found" : kindLabel(step.type),
    stepLabel: isFix ? "Done" : `Step ${{visited}}`,
  }};
}}

function renderPath(step) {{
  document.getElementById("statCurrent").textContent = step ? step.id : "—";
  document.getElementById("statHistory").textContent = String(history.length);

  const rail = document.getElementById("pathRail");
  if (!history.length) {{
    rail.innerHTML = `<div class="empty-state">Your decisions will appear here so you can jump back quickly.</div>`;
    return;
  }}

  rail.innerHTML = history.map((entry, index) => `
    <button class="path-chip ${{escapeHtml(entry.choiceType)}}" onclick="goBack(${{index}})">
      ${{escapeHtml(entry.id)}} · ${{escapeHtml(entry.choiceLabel)}}
    </button>
  `).join("");
}}

function renderQuestionOrCheck(step) {{
  const actions = [];
  const previews = [];

  if (step.yes_next && step.no_next) {{
    previews.push(`<span class="preview-chip">Yes → ${{escapeHtml(previewLabel(step.yes_next))}}</span>`);
    previews.push(`<span class="preview-chip">No → ${{escapeHtml(previewLabel(step.no_next))}}</span>`);
    actions.push(`
      <button class="action-btn yes" onclick="advance('${{escapeHtml(step.yes_next)}}', 'Yes', 'yes')">
        <div class="action-label">Yes</div>
        <div class="action-next">${{escapeHtml(previewLabel(step.yes_next))}}</div>
      </button>
    `);
    actions.push(`
      <button class="action-btn no" onclick="advance('${{escapeHtml(step.no_next)}}', 'No', 'no')">
        <div class="action-label">No</div>
        <div class="action-next">${{escapeHtml(previewLabel(step.no_next))}}</div>
      </button>
    `);
  }} else if (step.yes_next) {{
    previews.push(`<span class="preview-chip">Next → ${{escapeHtml(previewLabel(step.yes_next))}}</span>`);
    actions.push(`
      <button class="action-btn continue" onclick="advance('${{escapeHtml(step.yes_next)}}', 'Continue', 'yes')">
        <div class="action-label">Continue</div>
        <div class="action-next">${{escapeHtml(previewLabel(step.yes_next))}}</div>
      </button>
    `);
  }}

  return `
    <section class="step-card">
      <div class="step-top">
        <span class="step-kind ${{escapeHtml(step.type)}}">${{escapeHtml(kindLabel(step.type))}}</span>
        <span class="step-id">${{escapeHtml(step.id)}}</span>
      </div>
      <h3 class="step-title">${{escapeHtml(step.text)}}</h3>
      <p class="step-subtitle">${{escapeHtml(kindSubtitle(step.type))}}</p>
      ${{previews.length ? `<div class="preview-row">${{previews.join("")}}</div>` : ""}}
      <div class="actions">${{actions.join("")}}</div>
    </section>
  `;
}}

function renderFix(step) {{
  const fixBody = step.fix_text ? step.fix_text : "Use this as your next correction before retesting.";
  const path = history.length
    ? history.map((entry) => `<span class="fix-path-chip">${{escapeHtml(entry.id)}} · ${{escapeHtml(entry.choiceLabel)}}</span>`).join("")
    : `<span class="fix-path-chip">Direct resolution</span>`;

  return `
    <section class="fix-card">
      <div class="fix-kicker">Fix found</div>
      <h3 class="fix-title">${{escapeHtml(step.text)}}</h3>
      <p class="fix-copy">${{escapeHtml(fixBody)}}</p>
      <div class="fix-path">${{path}}</div>
    </section>
  `;
}}

function render() {{
  const step = stepMap[currentId];
  const current = document.getElementById("currentStep");
  if (!step) {{
    current.innerHTML = `<section class="step-card"><h3 class="step-title">Step not found</h3><p class="step-subtitle">The troubleshooting path references a missing step.</p></section>`;
    return;
  }}

  const progress = progressState(step);
  document.getElementById("progressFill").style.width = progress.pct + "%";
  document.getElementById("progressTitle").textContent = progress.title;
  document.getElementById("progressStep").textContent = progress.stepLabel;

  renderPath(step);
  current.innerHTML = step.type === "fix" ? renderFix(step) : renderQuestionOrCheck(step);
}}

function advance(nextId, choiceLabel, choiceType) {{
  history.push({{
    id: currentId,
    choiceLabel,
    choiceType,
  }});
  currentId = nextId;
  render();
}}

function goBack(index) {{
  currentId = history[index].id;
  history = history.slice(0, index);
  render();
}}

function restart() {{
  currentId = {json.dumps(first_id)};
  history = [];
  render();
}}

render();
</script>
</body>
</html>"""
