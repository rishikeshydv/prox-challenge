"""
settings_configurator.py — Settings widget with dynamic range bars computed from actual data.
"""

import html as html_mod
import json


def render_settings_widget(spec: dict) -> str:
    process         = spec.get("process", "")
    material        = spec.get("material", "")
    thickness_range = spec.get("thickness_range", "")
    options         = spec.get("settings_options", [])
    tips            = spec.get("tips", [])
    source_pages    = spec.get("source_pages", [])

    options_json    = json.dumps(options)
    pages_str       = ", ".join(str(p) for p in source_pages)
    header          = html_mod.escape(f"{process}" + (f" — {material}" if material else ""))
    subheader       = html_mod.escape(thickness_range) if thickness_range else ""
    tab_labels_json = json.dumps([o.get("label", f"Option {i+1}") for i, o in enumerate(options)])

    tips_html = ""
    if tips:
        items = "\n".join(f'<li>{html_mod.escape(t)}</li>' for t in tips)
        tips_html = f'<div class="tips"><div class="tips-hdr">Tips</div><ul>{items}</ul></div>'

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
  .header h2  {{ font-size: 17px; font-weight: 700; margin-bottom: 2px; }}
  .header .sub {{ font-size: 12px; color: #6b7280; margin-bottom: 14px; }}

  /* Tabs */
  .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }}
  .tab {{
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    cursor: pointer;
    color: #374151;
    transition: all 0.15s;
  }}
  .tab.active {{
    background: #eff6ff;
    border-color: #2563eb;
    color: #1d4ed8;
    font-weight: 600;
  }}

  /* Card */
  .card {{
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 14px;
  }}
  .row {{
    display: flex;
    align-items: stretch;
    border-bottom: 1px solid #f3f4f6;
    min-height: 58px;
  }}
  .row:last-child {{ border-bottom: none; }}
  .row-key {{
    width: 36%;
    padding: 12px 14px;
    font-size: 12px;
    color: #6b7280;
    background: #f9fafb;
    border-right: 1px solid #f3f4f6;
    display: flex;
    align-items: center;
  }}
  .row-val {{
    flex: 1;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 5px;
  }}
  /* Large bold value */
  .val-num {{
    font-size: 20px;
    font-weight: 700;
    color: #111827;
    line-height: 1;
  }}
  .val-text {{
    font-size: 14px;
    font-weight: 600;
    color: #111827;
  }}
  /* Range bar */
  .range-row {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}
  .range-min, .range-max {{
    font-size: 10px;
    color: #9ca3af;
    flex-shrink: 0;
  }}
  .range-track {{
    flex: 1;
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    position: relative;
  }}
  .range-fill {{
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    border-radius: 3px;
  }}
  .range-dot {{
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid #fff;
    box-shadow: 0 1px 3px #0002;
  }}

  /* Tips */
  .tips {{
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 14px;
  }}
  .tips-hdr {{
    font-size: 11px;
    font-weight: 700;
    color: #92400e;
    letter-spacing: 1px;
    margin-bottom: 8px;
  }}
  .tips ul {{ padding-left: 16px; }}
  .tips li  {{ font-size: 12px; color: #374151; margin-bottom: 5px; line-height: 1.5; }}
  .empty  {{ font-size: 13px; color: #9ca3af; padding: 14px; }}
  .source {{ font-size: 11px; color: #9ca3af; margin-top: 8px; text-align: center; }}
</style>
</head>
<body>

<div class="header">
  <h2>Recommended Settings</h2>
  <div class="sub">{header}{(" &mdash; " + subheader) if subheader else ""}</div>
</div>

<div class="tabs" id="tabs"></div>
<div class="card"  id="card"></div>

{tips_html}

<div class="source">Source: Manual pages {pages_str}</div>

<script>
const options   = {options_json};
const tabLabels = {tab_labels_json};
let activeIdx   = 0;

// Field definitions: [key, label, color]
// Ranges are computed dynamically from all options data
const FIELDS = [
  ['voltage',       'Voltage',       '#2563eb'],
  ['wire_speed',    'Wire Speed',    '#7c3aed'],
  ['amperage',      'Amperage',      '#0891b2'],
  ['gas_type',      'Shielding Gas', null],
  ['gas_flow_rate', 'Gas Flow',      null],
  ['wire_type',     'Wire Type',     null],
  ['wire_diameter', 'Wire Diameter', null],
];

// Extract first number from a string like "16-18V" → 17 (midpoint), or "250 IPM" → 250
function parseNum(val) {{
  if (!val) return null;
  const nums = String(val).match(/[\d.]+/g);
  if (!nums) return null;
  if (nums.length >= 2) return (parseFloat(nums[0]) + parseFloat(nums[1])) / 2;
  return parseFloat(nums[0]);
}}

// Compute min/max for a given key across ALL options
function getRange(key) {{
  const vals = options.map(o => parseNum(o[key])).filter(v => v !== null);
  if (vals.length < 2) return null;
  const mn = Math.min(...vals), mx = Math.max(...vals);
  if (mn === mx) return null;
  return {{ min: mn, max: mx }};
}}

// Pre-compute ranges once
const RANGES = {{}};
FIELDS.forEach(([key]) => {{ RANGES[key] = getRange(key); }});

function rangeHTML(raw, color, range) {{
  const n = parseNum(raw);
  if (n === null || !range || !color) return '';
  const pct = Math.max(4, Math.min(96, ((n - range.min) / (range.max - range.min)) * 100));
  return `
    <div class="range-row">
      <span class="range-min">${{range.min}}</span>
      <div class="range-track">
        <div class="range-fill" style="width:${{pct}}%;background:${{color}}20"></div>
        <div class="range-dot"  style="left:${{pct}}%;background:${{color}}"></div>
      </div>
      <span class="range-max">${{range.max}}</span>
    </div>`;
}}

function renderTabs() {{
  document.getElementById('tabs').innerHTML = tabLabels.map((lbl, i) =>
    `<div class="tab ${{i === activeIdx ? 'active' : ''}}" onclick="selectTab(${{i}})">${{lbl}}</div>`
  ).join('');
}}

function renderCard() {{
  const opt  = options[activeIdx];
  const rows = FIELDS
    .filter(([key]) => opt[key])
    .map(([key, label, color]) => {{
      const raw   = opt[key];
      const range = RANGES[key];
      const n     = parseNum(raw);
      // Show big number display if parseable, else text
      const isNum = n !== null && color !== null;
      const valEl = isNum
        ? `<div class="val-num">${{raw}}</div>`
        : `<div class="val-text">${{raw}}</div>`;
      const bar   = isNum ? rangeHTML(raw, color, range) : '';
      return `<div class="row">
        <div class="row-key">${{label}}</div>
        <div class="row-val">${{valEl}}${{bar}}</div>
      </div>`;
    }}).join('');

  document.getElementById('card').innerHTML =
    rows || '<div class="empty">No settings available.</div>';
}}

function selectTab(i) {{ activeIdx = i; renderTabs(); renderCard(); }}

renderTabs();
renderCard();
</script>
</body>
</html>"""
