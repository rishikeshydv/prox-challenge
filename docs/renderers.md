# Artifact Renderers

## Design System

All renderers share a consistent visual language:

### Colors
- **Background:** `#0d1117`
- **Card/Panel:** `#1a1a2e`
- **Border:** `#333` or `#2d2d44`
- **Primary accent:** `#4a9eff` (blue — info, connections)
- **Secondary accent:** `#ff6b35` (orange — machine components, warnings)
- **Success:** `#4ade80` (green — fixes, good status)
- **Warning:** `#fbbf24` (yellow — caution)
- **Danger:** `#f87171` (red — errors, critical warnings)
- **Text primary:** `#ffffff`
- **Text secondary:** `#888888` or `#a0a0b0`
- **Text muted:** `#666666`

### Typography
- Font: `system-ui, -apple-system, sans-serif`
- Title: 18-20px bold
- Subtitle: 13-14px, secondary color
- Body: 14px
- Small/label: 11-12px, uppercase for category labels

### Layout
- Border radius: 8-12px
- Padding: 16-24px
- Card spacing: 8-12px gap
- Max width: container-responsive

### Rules
- Use inline styles or `<style>` blocks — no external CSS files
- Use vanilla JS — no React/framework dependencies inside artifacts
- All data baked into HTML at render time — no API calls from artifacts
- Self-contained: every artifact is a complete HTML document fragment
- Dark theme always — matches the app shell

## Renderer 1: Polarity Diagram

**File:** `backend/renderers/polarity_diagram.py`
**Tool:** `render_polarity_diagram`
**Output:** SVG

### What It Shows
- Machine front panel representation with labeled sockets
- Animated connection arrows from cables/leads to sockets
- Color-coded by cable type
- Polarity label (DCEP/DCEN)
- Gas connection note if applicable
- Warning notes panel

### Visual Layout
```
┌─────────────────────────────────────┐
│     {Process} Polarity Setup        │
│     Polarity: {DCEP/DCEN}           │
│                                     │
│  COMPONENT          MACHINE SOCKET  │
│  ┌──────────┐  →→→  ┌────────────┐ │
│  │ MIG Gun  │──────▶│ Positive   │ │
│  └──────────┘       └────────────┘ │
│  ┌──────────┐  →→→  ┌────────────┐ │
│  │ Ground   │──────▶│ Negative   │ │
│  └──────────┘       └────────────┘ │
│                                     │
│  ⚠ Gas: 75/25 Ar/CO2 required      │
│  ⚠ Verify connections before start  │
└─────────────────────────────────────┘
```

### Key Implementation Details
- Left column: components (blue cards, `#1e3a5f` fill, `#4a9eff` stroke)
- Right column: machine sockets (dark orange cards, `#2d1810` fill, `#ff6b35` stroke)
- Arrows: colored lines with arrowhead markers, matching cable_color
- Notes: warning icon + text, muted color
- SVG viewBox scales to connection count: `height = 120 + len(connections) * 80 + len(notes) * 24 + 80`

## Renderer 2: Duty Cycle Calculator

**File:** `backend/renderers/duty_cycle_calculator.py`
**Tool:** `render_duty_cycle_calculator`
**Output:** Interactive HTML

### What It Shows
- Dropdown selects for voltage input (120V/240V) and process
- Matching duty cycle entries as cards
- Circular progress gauge per entry
- Color-coded: green (≥60%), yellow (30-59%), red (<30%)
- Minutes interpretation: "X.X min welding per 10 min"

### Visual Layout
```
┌─────────────────────────────────────┐
│  Duty Cycle Calculator              │
│  Vulcan OmniPro 220                 │
│                                     │
│  [120V ▼]  [MIG ▼]                  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ At 200A          ◐ 25%     │    │
│  │ 25% duty cycle             │    │
│  │ 2.5 min per 10 min         │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ At 155A          ◐ 60%     │    │
│  │ 60% duty cycle             │    │
│  │ 6.0 min per 10 min         │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Key Implementation Details
- Data is baked into a JS variable: `const data = {json_data};`
- `update()` function filters data by selected voltage + process
- Circular gauge: CSS `conic-gradient` with color stop at percentage
- Card border-left colored by status (green/yellow/red)
- Shows "No data for this combination" if no matches
- Selects auto-populated from unique values in the data

## Renderer 3: Troubleshooting Flow

**File:** `backend/renderers/troubleshooting_flow.py`
**Tool:** `render_troubleshooting_flow`
**Output:** Interactive HTML

### What It Shows
- One diagnostic question at a time
- Yes/No buttons to navigate the decision tree
- Progress breadcrumb trail
- Fix cards (green highlight) when a resolution is reached
- "Start Over" button

### Visual Layout
```
┌─────────────────────────────────────┐
│  Troubleshooting: {Symptom}         │
│                                     │
│  Step 2 of ~5                       │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
│  │                              │   │
│  │  Is your gas flow rate       │   │
│  │  between 20-25 CFH?          │   │
│  │                              │   │
│  │  [ Yes ]    [ No ]           │   │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘   │
│                                     │
│  ── or when fix reached ──          │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ ✓ FIX FOUND                 │    │
│  │ Increase gas flow to 25 CFH │    │
│  │ and check for drafts near   │    │
│  │ the weld area.              │    │
│  └─────────────────────────────┘    │
│                                     │
│  [ Start Over ]                     │
└─────────────────────────────────────┘
```

### Key Implementation Details
- Steps array baked into JS: `const steps = {json_steps};`
- State tracked in JS: `currentStepId`, `history[]`
- Question nodes: centered text with two buttons
- Fix nodes: green-bordered card with checkmark icon
- Check nodes: instruction card with "Continue" button
- Breadcrumb: shows step IDs visited, clickable to go back
- Start Over: resets to first step, clears history
- Handles both `yes_next`/`no_next` (branching) and `fix_text` (terminal)

## Renderer 4: Settings Configurator

**File:** `backend/renderers/settings_configurator.py`
**Tool:** `render_settings_configurator`
**Output:** Interactive HTML

### What It Shows
- Process and material header
- Settings cards for each thickness option (tabs or cards)
- Each card shows: voltage, wire speed, amperage, gas type, gas flow, wire type/diameter
- Tips section with practical advice
- Source citation

### Visual Layout
```
┌─────────────────────────────────────┐
│  Recommended Settings               │
│  {Process} — {Material}             │
│                                     │
│  [Thin 20ga] [Medium 16ga] [Thick]  │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Voltage      │  18V         │    │
│  │ Wire Speed   │  280 IPM     │    │
│  │ Amperage     │  90A         │    │
│  │ Gas          │  75/25 Ar/CO2│    │
│  │ Gas Flow     │  20-25 CFH   │    │
│  │ Wire         │  .030" ER70S │    │
│  └─────────────────────────────┘    │
│                                     │
│  💡 Tips                            │
│  • Keep travel speed consistent     │
│  • Point the gun into the joint     │
└─────────────────────────────────────┘
```

### Key Implementation Details
- Tab buttons for thickness options, active tab highlighted with accent color
- Settings displayed as a two-column key-value list
- Empty/missing values hidden (not all settings apply to all processes)
- Tips section at bottom with subtle styling
- If only one settings option, skip tabs and show directly

## Renderer 5: Manual Page Viewer

**File:** `backend/renderers/manual_page.py`
**Tool:** `get_manual_page_image`
**Output:** HTML with base64 image

### What It Shows
- The actual manual page at readable size
- Page number label
- Optional highlight overlay (semi-transparent colored rectangle)

### Key Implementation Details
- Image displayed as `<img src="data:image/png;base64,{data}" />`
- Responsive: `max-width: 100%; height: auto`
- Highlight overlay: absolute-positioned div with `rgba(74, 158, 255, 0.15)` background
- Page number badge in top-right corner
- Zoom on click (optional enhancement)

## Adding New Renderers

To add a new artifact type:

1. Add tool definition in `tools.py` with structured input schema
2. Create renderer function in `renderers/` that takes tool input → HTML string
3. Register in `RENDERERS` dict in `tool_handlers.py`
4. Add the tool to the system prompt's response mode list

The renderer function signature is always:
```python
def render_my_artifact(spec: dict) -> str:
    """Takes structured tool input, returns self-contained HTML string."""
    ...
```
