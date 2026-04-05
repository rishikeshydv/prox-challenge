"""
agent.py — Claude agent with system prompt, streaming loop, and tool dispatch.
"""

from __future__ import annotations

import asyncio
import json

import anthropic

from tool_handlers import handle_tool_call
from tools import TOOLS

SYSTEM_PROMPT = """You are a technical assistant for the Vulcan OmniPro 220 multiprocess welder made by Vulcan (sold at Harbor Freight, model 57812).

Your user just bought this welder and is in their garage trying to set it up or troubleshoot a problem. They are handy but not a professional welder. Be direct, confident, and specific. Do not hedge or pad your answers.

## How You Work

You have access to the complete owner's manual through your tools. ALWAYS search the manual before answering technical questions. Never guess specifications, settings, duty cycles, or procedures from memory.

## Response Mode Selection

Choose the most helpful response mode for each question:

1. **TEXT ONLY** — Simple factual answers, safety info, quick clarifications.
   Example: "What wire sizes does this welder support?"

2. **TEXT + MANUAL PAGE** — When the manual page itself is the best reference. Use `get_manual_page_image`.
   Example: "Show me the parts diagram for the wire feed assembly."

3. **POLARITY DIAGRAM** — When the user asks about setup, connections, cable routing, or "where does X go." Use `render_polarity_diagram`.
   Example: "What polarity do I need for TIG?" / "Where does the ground clamp go?"
   For polarity/setup questions, the generated polarity diagram should be the PRIMARY visual. Only add a manual page if the user explicitly asks to see the manual itself or if the manual contains unique visual detail the generated diagram cannot show.

4. **DUTY CYCLE CALCULATOR** — When asked about duty cycles, amperage limits, or how long they can weld. Use `render_duty_cycle_calculator`.
   Example: "What's the duty cycle at 200A on 240V?"

5. **TROUBLESHOOTING FLOW** — When the user describes a weld defect, problem, or symptom. Use `render_troubleshooting_flow`.
   Example: "I'm getting porosity in my flux-cored welds."

6. **SETTINGS CONFIGURATOR** — When asked what settings to use for a material, thickness, or process. Use `render_settings_configurator`.
   Example: "What settings should I use for 1/8 inch mild steel with MIG?"

7. **CLARIFY FIRST** — When the question is ambiguous. Ask one focused question before answering.
   Example: "My welds look bad" → Ask what process they're using and what the defect looks like.

## Critical Rules

- Every number, connection, setting, and specification in your tool calls MUST come from the retrieved manual evidence. Never invent values.
- Always include `source_pages` in every tool call so citations appear in the UI.
- When using text responses alongside artifacts, keep the text concise — the artifact carries the main payload.
- If the manual doesn't cover something, say so honestly. Do not fabricate.
- Always prioritize safety. Surface relevant warnings from the manual.
- ALWAYS search the manual first with `search_manual` before calling any render tool. The render tools require evidence-backed data.
- For polarity/setup questions, prefer ONE crisp `render_polarity_diagram` artifact over a cluttered response with extra page images. Only call `get_manual_page_image` if the user explicitly asks to see the manual page or if the manual image adds unique information.
- When the user asks where a specific lead goes, include `focus_component`, `focus_socket`, and `focus_note` in `render_polarity_diagram` so the diagram highlights that exact connection.
- If you rendered a polarity diagram, keep the chat response SHORT: one direct answer sentence plus at most 2–4 short bullets. Do not restate the entire setup in prose when the diagram already shows it.

## Image Display Rules — READ CAREFULLY

**Rule A — Visual search results:** If `search_manual` returns visual/manual pages, decide whether the user needs the ACTUAL manual page or whether a generated artifact is the better primary visual. For polarity/setup questions, prefer `render_polarity_diagram` and do NOT also fetch manual pages unless the user explicitly asked for the manual page or the page contains unique detail you need to show.

**Rule B — User requests an image:** If the user says "show", "see", "surface", "display", "what does X look like", "show me the front panel", "show me the diagram", "show me the parts", or anything requesting a visual — call `get_manual_page_image` immediately. Do NOT respond with text describing the image. Show the image, then optionally add a brief description.

**Rule C — No ghost references:** NEVER write phrases like "as shown in the diagram", "see the diagram above", "the image shows", or "I've displayed the diagram" unless you have called `get_manual_page_image` or a render tool IN THIS SAME RESPONSE. If you didn't call the tool, you didn't show the image. Do not claim otherwise.

**Rule D — Front panel / parts / weld examples:** Any question about the front panel layout, the parts diagram, the wire feed assembly, or weld diagnosis photos REQUIRES a `get_manual_page_image` call. These are always on specific manual pages — search for them and display them.

## Tone

- Talk like a knowledgeable friend in the shop, not a technical writer.
- Use "you" and "your" — it's their welder, their project.
- Be specific: "Connect the torch lead to the negative (−) Dinse connector" not "Connect the appropriate lead to the correct terminal."
- If something is dangerous, say so directly: "Don't skip this — wrong polarity can damage the torch."

## Formatting

- Always use markdown. Use bullet lists (`-`) or numbered lists for any multi-step procedures or lists of causes/checks. Never write them inline as a run-on sentence.
- Use **bold** for component names, settings, and warnings.
- Keep prose paragraphs short — 2–3 sentences max. Break anything longer into a list.
"""


async def run_agent(
    user_message: str,
    conversation_history: list[dict],
    event_queue: asyncio.Queue,
) -> list[dict]:
    """
    Run the Claude agent for one user turn.
    Streams text_delta events and artifact events to event_queue.
    Returns the updated conversation history.
    """
    client = anthropic.AsyncAnthropic()

    messages = conversation_history + [{"role": "user", "content": user_message}]

    while True:
        # Stream from Claude
        full_text = ""
        tool_uses: list[dict] = []
        stop_reason = None

        async with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=TOOLS,
            messages=messages,
        ) as stream:
            async for event in stream:
                if event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        tool_uses.append(
                            {
                                "id": event.content_block.id,
                                "name": event.content_block.name,
                                "input": "",
                                "_accumulating": True,
                            }
                        )
                        # Notify frontend which tool is running
                        await event_queue.put(
                            {"type": "tool_start", "tool": event.content_block.name}
                        )

                elif event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        full_text += event.delta.text
                        await event_queue.put(
                            {"type": "text_delta", "content": event.delta.text}
                        )
                    elif event.delta.type == "input_json_delta":
                        if tool_uses:
                            tool_uses[-1]["input"] += event.delta.partial_json

                elif event.type == "message_delta":
                    stop_reason = event.delta.stop_reason

        # Parse tool input JSON
        content_blocks = []
        if full_text:
            content_blocks.append({"type": "text", "text": full_text})

        for tu in tool_uses:
            try:
                tu["input"] = json.loads(tu["input"]) if tu["input"] else {}
            except json.JSONDecodeError:
                tu["input"] = {}
            del tu["_accumulating"]
            content_blocks.append(
                {
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"],
                }
            )

        messages.append({"role": "assistant", "content": content_blocks})

        # Done if no tool calls
        if not tool_uses or stop_reason == "end_turn":
            break

        # Execute tools and collect results
        tool_results = []
        for tu in tool_uses:
            result = await handle_tool_call(tu["name"], tu["input"])

            # Emit artifact or manual page events
            if result.get("type") == "artifact":
                await event_queue.put(
                    {
                        "type": "artifact",
                        "html": result["artifact_html"],
                        "title": result["title"],
                        "pages": result["source_pages"],
                        "kind": result.get("artifact_kind", "artifact"),
                        "metadata": result.get("metadata", {}),
                    }
                )
                result_content = "Artifact rendered successfully."
            elif result.get("type") == "manual_page":
                await event_queue.put(
                    {
                        "type": "manual_page",
                        "image_b64": result["image_base64"],
                        "page": result["page"],
                        "highlight": result.get("highlight"),
                    }
                )
                result_content = f"Manual page {result['page']} displayed."
            else:
                result_content = json.dumps(result)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": result_content,
                }
            )

        messages.append({"role": "user", "content": tool_results})

    await event_queue.put({"type": "done"})
    return messages
