from __future__ import annotations

"""
polarity_diagram.py — Welder front-panel schematic with Dinse sockets, polarity labels,
                       mid-cable +/− badges, ventilation slots, and handle.
"""

import html as html_mod


def _polarity_sign(to_socket: str) -> str | None:
    s = to_socket.lower()
    if any(x in s for x in ["positive", "(+)", "dcep", "+ dinse"]):
        return "+"
    if any(x in s for x in ["negative", "(−)", "(-)", "dcen", "− dinse", "- dinse"]):
        return "−"
    return None


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().replace("(", " ").replace(")", " ").replace("/", " ").split())


def _matches_focus(connection: dict, focus_component: str | None, focus_socket: str | None) -> bool:
    if focus_component and _normalize(focus_component) in _normalize(connection.get("from_component", "")):
        return True
    if focus_socket and _normalize(focus_socket) in _normalize(connection.get("to_socket", "")):
        return True
    return False


def render_polarity_svg(spec: dict) -> str:
    process      = spec.get("process", "")
    polarity     = spec.get("polarity", "")
    connections  = spec.get("connections", [])
    gas_required = spec.get("gas_required", False)
    gas_type     = spec.get("gas_type", "")
    notes        = spec.get("notes", [])
    focus_component = spec.get("focus_component")
    focus_socket = spec.get("focus_socket")
    focus_note   = spec.get("focus_note")
    source_pages = spec.get("source_pages", [])

    n = len(connections)
    all_notes = []
    if gas_required and gas_type:
        all_notes.append(f"Gas: {gas_type} required")
    all_notes.extend(notes)
    focus_index = next(
        (i for i, connection in enumerate(connections) if _matches_focus(connection, focus_component, focus_socket)),
        None,
    )

    # ── Layout ──────────────────────────────────────────────────────────────
    W       = 720
    MACH_X  = 430
    MACH_W  = 250
    MACH_Y  = 75
    MACH_H  = max(190, 50 + n * 90)
    EQ_W    = 172
    EQ_H    = 50
    EQ_X    = 14
    FOCUS_H = 52 if focus_index is not None else 0
    NOTE_Y  = MACH_Y + MACH_H + 22 + FOCUS_H
    H       = NOTE_Y + len(all_notes) * 30 + 48
    FONT    = "system-ui, -apple-system, sans-serif"
    PORT_X  = MACH_X

    eq_spacing   = MACH_H // max(n, 1)
    eq_centers   = [MACH_Y + eq_spacing * i + eq_spacing // 2 for i in range(n)]
    port_spacing = MACH_H // max(n, 1)
    port_ys      = [MACH_Y + port_spacing * i + port_spacing // 2 for i in range(n)]

    mx, my, mw, mh = MACH_X, MACH_Y, MACH_W, MACH_H
    mcx = mx + mw // 2

    defs = """<defs>
    <filter id="sh" x="-15%" y="-15%" width="130%" height="130%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#00000020"/>
    </filter>
    <filter id="sh2" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-color="#00000015"/>
    </filter>
  </defs>"""

    els = []

    # ── Title ───────────────────────────────────────────────────────────────
    els.append(
        f'<text x="{W//2}" y="28" text-anchor="middle" font-family="{FONT}" '
        f'font-size="15" font-weight="700" fill="#111827">'
        f'{html_mod.escape(process)} — Connection Diagram</text>'
    )
    if polarity:
        els.append(
            f'<text x="{W//2}" y="48" text-anchor="middle" font-family="{FONT}" '
            f'font-size="12" fill="#6b7280">Polarity: {html_mod.escape(polarity)}</text>'
        )
    if focus_index is not None:
        highlighted = connections[focus_index]
        callout = html_mod.escape(
            focus_note
            or f"{highlighted.get('from_component', 'Highlighted lead')} -> {highlighted.get('to_socket', 'highlighted socket')}"
        )
        callout_y = MACH_Y + MACH_H + 30
        els.append(f'<rect x="14" y="{callout_y}" width="{W-28}" height="38" rx="10" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>')
        els.append(f'<text x="28" y="{callout_y+23}" font-family="{FONT}" font-size="12" font-weight="700" fill="#1d4ed8">Focus:</text>')
        els.append(f'<text x="90" y="{callout_y+23}" font-family="{FONT}" font-size="12" fill="#1e3a5f">{callout}</text>')

    # ── Machine body ────────────────────────────────────────────────────────
    # Handle at top
    hx = mcx - 44
    els.append(f'<rect x="{hx}" y="{my - 18}" width="88" height="20" rx="10" fill="#334155" stroke="#475569" stroke-width="1"/>')

    # Body
    els.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="10" fill="#1e293b" stroke="#475569" stroke-width="1.5" filter="url(#sh)"/>')
    # Inner bevel
    els.append(f'<rect x="{mx+5}" y="{my+5}" width="{mw-10}" height="{mh-10}" rx="7" fill="none" stroke="#334155" stroke-width="0.6"/>')

    # Ventilation slots — right side
    slot_x = mx + mw - 18
    for si in range(5):
        sy_slot = my + 20 + si * 14
        els.append(f'<rect x="{slot_x}" y="{sy_slot}" width="10" height="6" rx="3" fill="#0f172a" stroke="#334155" stroke-width="0.5"/>')

    # Display panel
    els.append(f'<rect x="{mx+12}" y="{my+12}" width="{mw-90}" height="30" rx="5" fill="#0f172a" stroke="#1e40af" stroke-width="1"/>')
    els.append(
        f'<text x="{mx+12+(mw-90)//2}" y="{my+31}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="8" fill="#7dd3fc" letter-spacing="0.8">VULCAN OMNIPRO 220</text>'
    )

    # Power LED (green = on)
    els.append(f'<circle cx="{mx+mw-38}" cy="{my+27}" r="5" fill="#22c55e"/>')
    els.append(f'<circle cx="{mx+mw-38}" cy="{my+27}" r="3" fill="#86efac" opacity="0.7"/>')

    # Control knobs (voltage + wire speed)
    for ki, kx in enumerate([mx + mw - 65, mx + mw - 38]):
        ky = my + mh - 40
        els.append(f'<circle cx="{kx}" cy="{ky}" r="12" fill="#334155" stroke="#475569" stroke-width="1.2" filter="url(#sh2)"/>')
        els.append(f'<circle cx="{kx}" cy="{ky}" r="5" fill="#1e293b"/>')
        # Indicator line rotated slightly for each knob
        angle_x = kx + (6 if ki == 0 else -4)
        angle_y = ky - (10 if ki == 0 else 9)
        els.append(f'<line x1="{kx}" y1="{ky}" x2="{angle_x}" y2="{angle_y}" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/>')

    knob_labels = ["VOLTAGE", "WIRE SPD"]
    for ki, kx in enumerate([mx + mw - 65, mx + mw - 38]):
        ky = my + mh - 40
        els.append(f'<text x="{kx}" y="{ky+22}" text-anchor="middle" font-family="{FONT}" font-size="6" fill="#475569">{knob_labels[ki]}</text>')

    # "WELDER" label at bottom of machine
    els.append(f'<text x="{mcx-20}" y="{my+mh-12}" text-anchor="middle" font-family="{FONT}" font-size="8" fill="#475569" letter-spacing="1">WELDER</text>')

    # ── Dinse-style sockets on machine left face ─────────────────────────────
    for i, (conn, py) in enumerate(zip(connections, port_ys)):
        to_sock  = conn.get("to_socket", "")
        sign     = _polarity_sign(to_sock)
        is_focus = focus_index == i
        socket_ring = "#2563eb" if is_focus else "#64748b"
        socket_fill = "#3b82f6" if is_focus else "#2d3748"
        label_fill = "#ffffff" if is_focus else "#cbd5e1"
        label_weight = "700" if is_focus else "500"

        # Dinse outer ring
        els.append(f'<circle cx="{PORT_X}" cy="{py}" r="15" fill="{socket_fill}" stroke="{socket_ring}" stroke-width="{3 if is_focus else 2}" filter="url(#sh2)"/>')
        # Dinse inner hole
        els.append(f'<circle cx="{PORT_X}" cy="{py}" r="8" fill="#0f172a" stroke="#94a3b8" stroke-width="1.5"/>')
        # Key notch at top (orientation slot)
        els.append(f'<rect x="{PORT_X - 3}" y="{py - 15}" width="6" height="6" rx="1" fill="#0f172a" stroke="#64748b" stroke-width="0.5"/>')
        # Polarity badge on socket
        if sign:
            badge_col = "#dc2626" if sign == "+" else "#374151"
            els.append(f'<circle cx="{PORT_X}" cy="{py}" r="4" fill="{badge_col}"/>')
            els.append(f'<text x="{PORT_X}" y="{py+3}" text-anchor="middle" font-family="{FONT}" font-size="6" font-weight="700" fill="#fff">{sign}</text>')

        # Socket label inside machine
        els.append(
            f'<text x="{PORT_X + 22}" y="{py + 4}" font-family="{FONT}" '
            f'font-size="11" font-weight="{label_weight}" fill="{label_fill}">{html_mod.escape(to_sock)}</text>'
        )
        if is_focus:
            els.append(f'<rect x="{PORT_X - 18}" y="{py - 22}" width="36" height="44" rx="18" fill="none" stroke="#93c5fd" stroke-width="2.5" opacity="0.95"/>')

    # ── Equipment + cables ───────────────────────────────────────────────────
    for i, (conn, cy_eq) in enumerate(zip(connections, eq_centers)):
        from_comp   = html_mod.escape(conn.get("from_component", ""))
        cable_color = conn.get("cable_color", "#3b82f6")
        to_sock     = conn.get("to_socket", "")
        sign        = _polarity_sign(to_sock)
        is_focus    = focus_index == i
        box_fill    = "#dbeafe" if is_focus else "#f0f9ff"
        text_fill   = "#0f172a" if is_focus else "#0c4a6e"
        cable_opacity = "0.18" if focus_index is None or is_focus else "0.08"
        cable_width = "5" if is_focus else "3.5"
        sheath_width = "9" if is_focus else "7"
        cable_stroke = "#2563eb" if is_focus else cable_color
        component_weight = "700" if is_focus else "600"

        eq_y  = cy_eq - EQ_H // 2
        eq_cx = EQ_X + EQ_W // 2

        # Equipment box
        els.append(f'<rect x="{EQ_X}" y="{eq_y}" width="{EQ_W}" height="{EQ_H}" rx="8" fill="{box_fill}" stroke="{cable_stroke}" stroke-width="{3 if is_focus else 2}" filter="url(#sh2)"/>')
        # Colored accent bar on left
        els.append(f'<rect x="{EQ_X}" y="{eq_y}" width="5" height="{EQ_H}" rx="4" fill="{cable_stroke}"/>')
        els.append(f'<text x="{eq_cx + 4}" y="{eq_y + EQ_H//2 + 5}" text-anchor="middle" font-family="{FONT}" font-size="13" font-weight="{component_weight}" fill="{text_fill}">{from_comp}</text>')

        # Connector nub on right edge
        nub_x = EQ_X + EQ_W
        els.append(f'<rect x="{nub_x}" y="{cy_eq - 9}" width="11" height="18" rx="3" fill="{cable_stroke}" filter="url(#sh2)"/>')

        # Cable path
        sx   = nub_x + 11
        sy   = cy_eq
        ex   = PORT_X - 15
        ey   = port_ys[i]
        cp1x = sx + (ex - sx) * 0.45
        cp2x = sx + (ex - sx) * 0.55
        mid_x = (sx + ex) // 2
        mid_y = (sy + ey) // 2

        # Outer sheath (width)
        els.append(
            f'<path d="M{sx},{sy} C{cp1x},{sy} {cp2x},{ey} {ex},{ey}" '
            f'fill="none" stroke="{cable_stroke}" stroke-width="{sheath_width}" stroke-linecap="round" opacity="{cable_opacity}"/>'
        )
        # Inner conductor
        els.append(
            f'<path d="M{sx},{sy} C{cp1x},{sy} {cp2x},{ey} {ex},{ey}" '
            f'fill="none" stroke="{cable_stroke}" stroke-width="{cable_width}" stroke-linecap="round" opacity="{1 if focus_index is None or is_focus else 0.32}"/>'
        )

        # Mid-cable polarity badge
        if sign:
            badge_bg = "#dc2626" if sign == "+" else "#1e293b"
            els.append(f'<circle cx="{mid_x}" cy="{mid_y}" r="9" fill="{badge_bg}" stroke="#fff" stroke-width="1.5"/>')
            els.append(f'<text x="{mid_x}" y="{mid_y + 4}" text-anchor="middle" font-family="{FONT}" font-size="11" font-weight="700" fill="#fff">{sign}</text>')
        if is_focus:
            els.append(f'<circle cx="{mid_x}" cy="{mid_y}" r="15" fill="none" stroke="#93c5fd" stroke-width="2.5" opacity="0.9"/>')

    # ── Notes / warnings ────────────────────────────────────────────────────
    for j, note in enumerate(all_notes):
        ny = NOTE_Y + j * 30
        els.append(f'<rect x="14" y="{ny-15}" width="{W-28}" height="24" rx="6" fill="#fffbeb" stroke="#fcd34d" stroke-width="1"/>')
        els.append(f'<text x="28" y="{ny+3}" font-family="{FONT}" font-size="12" fill="#92400e">⚠  {html_mod.escape(note)}</text>')

    # ── Source citation ──────────────────────────────────────────────────────
    if source_pages:
        pages_str = ", ".join(str(p) for p in source_pages)
        els.append(
            f'<text x="{W//2}" y="{H - 8}" text-anchor="middle" font-family="{FONT}" '
            f'font-size="10" fill="#9ca3af">Source: Manual pages {html_mod.escape(pages_str)}</text>'
        )

    inner = "\n  ".join(els)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    padding: 8px;
    background: #f8fafc;
  }}
  svg {{
    display: block;
    width: 100%;
    height: auto;
    max-width: 100%;
  }}
</style>
</head>
<body>
<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg">
  {defs}
  {inner}
</svg>
</body>
</html>"""
