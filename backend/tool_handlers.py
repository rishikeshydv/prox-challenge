"""
tool_handlers.py — Dispatch tool calls to knowledge store or renderers.
"""

from __future__ import annotations

import base64
import re
from pathlib import Path

from knowledge.store import knowledge_store
from renderers.duty_cycle_calculator import render_duty_cycle_widget
from renderers.polarity_diagram import render_polarity_svg
from renderers.settings_configurator import render_settings_widget
from renderers.troubleshooting_flow import render_troubleshooting_widget

BACKEND_ROOT = Path(__file__).parent
PAGE_IMAGES_DIR = BACKEND_ROOT / "static" / "page_images"

RENDERERS = {
    "render_polarity_diagram": (
        render_polarity_svg,
        "Polarity Diagram",
        "polarity_diagram",
    ),
    "render_duty_cycle_calculator": (
        render_duty_cycle_widget,
        "Duty Cycle Calculator",
        "duty_cycle_calculator",
    ),
    "render_troubleshooting_flow": (
        render_troubleshooting_widget,
        "Troubleshooting Guide",
        "troubleshooting_flow",
    ),
    "render_settings_configurator": (
        render_settings_widget,
        "Settings Configurator",
        "settings_configurator",
    ),
}

ACTIVE_COMPONENT_TERMS = (
    "torch",
    "gun",
    "electrode",
    "stinger",
    "holder",
    "spool",
)
RETURN_COMPONENT_TERMS = (
    "ground",
    "clamp",
    "work lead",
    "work clamp",
    "return",
)


def _generate_title(tool_name: str, tool_input: dict) -> str:
    if tool_name == "render_polarity_diagram":
        return f"{tool_input.get('process', '')} Polarity Setup"
    if tool_name == "render_duty_cycle_calculator":
        return "Duty Cycle Calculator"
    if tool_name == "render_troubleshooting_flow":
        return f"Troubleshooting: {tool_input.get('symptom', 'Issue')}"
    if tool_name == "render_settings_configurator":
        process = tool_input.get("process", "")
        material = tool_input.get("material", "")
        return f"{process} Settings" + (f" — {material}" if material else "")
    return "Manual Reference"


def _artifact_metadata(tool_name: str, tool_input: dict) -> dict:
    if tool_name == "render_polarity_diagram":
        return {
            "process": tool_input.get("process"),
            "polarity": tool_input.get("polarity"),
        }
    if tool_name == "render_duty_cycle_calculator":
        duty_cycle_data = tool_input.get("duty_cycle_data") or []
        first_row = duty_cycle_data[0] if duty_cycle_data else {}
        return {
            "process": first_row.get("process"),
        }
    if tool_name == "render_troubleshooting_flow":
        return {
            "symptom": tool_input.get("symptom"),
            "process": tool_input.get("process"),
        }
    if tool_name == "render_settings_configurator":
        return {
            "process": tool_input.get("process"),
        }
    return {}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _socket_sign(text: str) -> str | None:
    normalized = _normalize(text)
    if any(token in normalized for token in ("positive", "dcep")) or "(+)" in text or "+ dinse" in normalized:
        return "+"
    if any(token in normalized for token in ("negative", "dcen")) or "(-)" in text or "- dinse" in normalized:
        return "-"
    return None


def _matches_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = _normalize(text)
    return any(term in normalized for term in terms)


def _expected_sign_from_polarity(polarity: str, component_name: str) -> str | None:
    normalized_polarity = _normalize(polarity)
    if "dcep" in normalized_polarity:
        if _matches_any(component_name, ACTIVE_COMPONENT_TERMS):
            return "+"
        if _matches_any(component_name, RETURN_COMPONENT_TERMS):
            return "-"
    if "dcen" in normalized_polarity:
        if _matches_any(component_name, ACTIVE_COMPONENT_TERMS):
            return "-"
        if _matches_any(component_name, RETURN_COMPONENT_TERMS):
            return "+"
    return None


def _resolve_focus(tool_input: dict) -> tuple[str | None, str | None, str | None]:
    focus_component = tool_input.get("focus_component")
    focus_socket = tool_input.get("focus_socket")
    focus_note = tool_input.get("focus_note")

    if focus_component or focus_socket or focus_note:
        return focus_component, focus_socket, focus_note

    connections = tool_input.get("connections", [])
    for connection in connections:
        component = connection.get("from_component", "")
        if _matches_any(component, RETURN_COMPONENT_TERMS):
            return (
                component,
                connection.get("to_socket"),
                f"{component} goes to {connection.get('to_socket', 'the highlighted socket')}",
            )

    return None, None, None


def _validate_polarity_diagram_input(tool_input: dict) -> dict:
    process = tool_input.get("process", "")
    polarity = tool_input.get("polarity", "")
    connections = tool_input.get("connections") or []
    source_pages = tool_input.get("source_pages") or []

    if not process:
        return {"type": "error", "message": "Polarity diagram requires a welding process."}
    if not polarity:
        return {"type": "error", "message": "Polarity diagram requires explicit polarity from the manual."}
    if len(connections) < 2:
        return {"type": "error", "message": "Polarity diagram needs at least two manual-backed connections."}
    if not source_pages:
        return {"type": "error", "message": "Polarity diagram must include source pages."}

    normalized_connections = []
    seen_components: set[str] = set()
    sign_map: dict[str, set[str]] = {}

    for connection in connections:
        component = (
            connection.get("from_component")
            or connection.get("component")
            or ""
        ).strip()
        socket = (
            connection.get("to_socket")
            or connection.get("socket")
            or ""
        ).strip()
        cable_color = connection.get("cable_color", "#3b82f6")

        if not component or not socket:
            return {"type": "error", "message": "Each polarity connection requires both a component and socket."}

        component_key = _normalize(component)
        if component_key in seen_components:
            return {"type": "error", "message": f"Duplicate connection for '{component}' in polarity diagram input."}
        seen_components.add(component_key)

        sign = _socket_sign(socket)
        if sign is None:
            return {
                "type": "error",
                "message": f"Socket '{socket}' is missing an identifiable positive/negative label.",
            }

        expected_sign = _expected_sign_from_polarity(polarity, component)
        if expected_sign and expected_sign != sign:
            return {
                "type": "error",
                "message": (
                    f"Connection mismatch: '{component}' conflicts with polarity '{polarity}' "
                    f"when assigned to '{socket}'."
                ),
            }

        sign_map.setdefault(sign, set()).add(component_key)
        normalized_connections.append(
            {
                "from_component": component,
                "to_socket": socket,
                "cable_color": cable_color,
            }
        )

    if len(sign_map.keys()) < 2:
        return {
            "type": "error",
            "message": "Polarity diagram needs both positive and negative socket assignments.",
        }

    focus_component, focus_socket, focus_note = _resolve_focus(
        {**tool_input, "connections": normalized_connections}
    )

    return {
        **tool_input,
        "connections": normalized_connections,
        "focus_component": focus_component,
        "focus_socket": focus_socket,
        "focus_note": focus_note,
    }


async def handle_tool_call(tool_name: str, tool_input: dict) -> dict:
    """Dispatch a tool call and return a result dict."""

    if tool_name == "search_manual":
        evidence = knowledge_store.search(
            query=tool_input["query"],
            process_filter=tool_input.get("process_filter"),
            topic_filter=tool_input.get("topic_filter"),
        )
        return evidence.to_dict()

    elif tool_name == "get_manual_page_image":
        page = tool_input["page_number"]
        image_path = PAGE_IMAGES_DIR / f"page_{page}.png"

        if not image_path.exists():
            return {
                "type": "error",
                "message": f"Page image {page} not found. Run extract_knowledge.py first.",
            }

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        return {
            "type": "manual_page",
            "image_base64": image_b64,
            "page": page,
            "highlight": tool_input.get("highlight_region"),
        }

    elif tool_name in RENDERERS:
        if tool_name == "render_polarity_diagram":
            validated = _validate_polarity_diagram_input(tool_input)
            if validated.get("type") == "error":
                return validated
            tool_input = validated
        renderer_fn, _, artifact_kind = RENDERERS[tool_name]
        html = renderer_fn(tool_input)
        return {
            "type": "artifact",
            "artifact_html": html,
            "title": _generate_title(tool_name, tool_input),
            "source_pages": tool_input.get("source_pages", []),
            "artifact_kind": artifact_kind,
            "metadata": _artifact_metadata(tool_name, tool_input),
        }

    else:
        return {"type": "error", "message": f"Unknown tool: {tool_name}"}
