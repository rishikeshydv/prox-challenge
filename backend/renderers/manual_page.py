"""
manual_page.py — Manual page image viewer renderer.
"""

import html as html_mod


def render_manual_page(spec: dict) -> str:
    """
    spec keys:
      page: int
      image_base64: str
      highlight: str | None
    """
    page = spec.get("page", "?")
    image_b64 = spec.get("image_base64", "")
    highlight = spec.get("highlight")

    highlight_overlay = ""
    if highlight:
        h_text = html_mod.escape(highlight)
        highlight_overlay = f"""
    <div style="
      position: absolute;
      top: 5%; left: 5%;
      width: 90%; height: 30%;
      background: rgba(74, 158, 255, 0.15);
      border: 1.5px solid rgba(74, 158, 255, 0.4);
      border-radius: 4px;
      pointer-events: none;
    " title="{h_text}"></div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: system-ui, -apple-system, sans-serif;
    background: #0d1117;
    color: #fff;
    padding: 16px;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }}
  .page-wrapper {{
    position: relative;
    width: 100%;
    max-width: 800px;
  }}
  img {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 8px;
    border: 1px solid #333;
    cursor: zoom-in;
  }}
  img.zoomed {{
    cursor: zoom-out;
    position: fixed;
    top: 0; left: 0;
    width: 100vw;
    height: 100vh;
    object-fit: contain;
    background: #0d1117;
    z-index: 999;
    border-radius: 0;
    border: none;
  }}
  .page-badge {{
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(13,17,23,0.85);
    color: #a0a0b0;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    border: 1px solid #333;
    pointer-events: none;
  }}
</style>
</head>
<body>
<div class="page-wrapper">
  <img
    id="page-img"
    src="data:image/png;base64,{image_b64}"
    alt="Manual page {page}"
    onclick="this.classList.toggle('zoomed')"
  />
  {highlight_overlay}
  <div class="page-badge">Page {page}</div>
</div>
</body>
</html>"""
