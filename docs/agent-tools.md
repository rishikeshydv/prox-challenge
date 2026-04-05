# Agent & Tools

## System Prompt

```
You are a technical assistant for the Vulcan OmniPro 220 multiprocess welder made by Vulcan (sold at Harbor Freight, model 57812).

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

## Tone

- Talk like a knowledgeable friend in the shop, not a technical writer.
- Use "you" and "your" — it's their welder, their project.
- Be specific: "Connect the torch lead to the negative (−) Dinse connector" not "Connect the appropriate lead to the correct terminal."
- If something is dangerous, say so directly: "Don't skip this — wrong polarity can damage the torch."
```

## Tool Definitions

### search_manual

```json
{
    "name": "search_manual",
    "description": "Search the Vulcan OmniPro 220 owner's manual. ALWAYS call this first before answering any technical question. Returns relevant text, tables, and page references.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query. Be specific: 'TIG polarity setup connections' not just 'TIG'."
            },
            "process_filter": {
                "type": "string",
                "enum": ["MIG", "TIG", "Stick", "Flux-Cored"],
                "description": "Optional: filter results to a specific welding process."
            },
            "topic_filter": {
                "type": "string",
                "enum": ["setup", "polarity", "troubleshooting", "safety", "duty-cycle", "specifications", "parts", "maintenance", "wiring"],
                "description": "Optional: filter results to a specific topic."
            }
        },
        "required": ["query"]
    }
}
```

### get_manual_page_image

```json
{
    "name": "get_manual_page_image",
    "description": "Retrieve a specific page image from the manual. Use when the user should see the actual manual page — parts diagrams, wiring schematics, weld diagnosis photos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "page_number": {
                "type": "integer",
                "description": "The manual page number to retrieve."
            },
            "highlight_region": {
                "type": "string",
                "description": "Optional: describe the region to highlight."
            }
        },
        "required": ["page_number"]
    }
}
```

### render_polarity_diagram

```json
{
    "name": "render_polarity_diagram",
    "description": "Generate an SVG diagram showing cable-to-socket connections for a welding process. Use when the user asks about setup, polarity, connections, or 'where does X go'. ALL connection data must come from search_manual results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "process": {
                "type": "string",
                "enum": ["MIG", "TIG", "Stick", "Flux-Cored"]
            },
            "polarity": {
                "type": "string",
                "description": "e.g. 'DCEP (DC Electrode Positive)' or 'DCEN (DC Electrode Negative)'"
            },
            "connections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "from_component": {"type": "string"},
                        "to_socket": {"type": "string"},
                        "cable_color": {"type": "string"}
                    },
                    "required": ["from_component", "to_socket"]
                }
            },
            "gas_required": {"type": "boolean"},
            "gas_type": {"type": "string"},
            "notes": {"type": "array", "items": {"type": "string"}},
            "source_pages": {"type": "array", "items": {"type": "integer"}}
        },
        "required": ["process", "polarity", "connections", "source_pages"]
    }
}
```

### render_duty_cycle_calculator

```json
{
    "name": "render_duty_cycle_calculator",
    "description": "Generate an interactive duty cycle lookup widget. Use when users ask about duty cycle, how long they can weld, or amperage limits. ALL data must come from manual's duty cycle tables.",
    "input_schema": {
        "type": "object",
        "properties": {
            "duty_cycle_data": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "voltage_input": {"type": "string", "enum": ["120V", "240V"]},
                        "process": {"type": "string"},
                        "amperage": {"type": "number"},
                        "voltage_output": {"type": "number"},
                        "duty_cycle_percent": {"type": "number"}
                    },
                    "required": ["voltage_input", "process", "amperage", "duty_cycle_percent"]
                }
            },
            "source_pages": {"type": "array", "items": {"type": "integer"}}
        },
        "required": ["duty_cycle_data", "source_pages"]
    }
}
```

### render_troubleshooting_flow

```json
{
    "name": "render_troubleshooting_flow",
    "description": "Generate an interactive troubleshooting flowchart. Use when users describe weld defects, problems, or symptoms. Build the decision tree from the manual's troubleshooting section.",
    "input_schema": {
        "type": "object",
        "properties": {
            "symptom": {"type": "string"},
            "steps": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["question", "fix", "check"]},
                        "text": {"type": "string"},
                        "yes_next": {"type": "string"},
                        "no_next": {"type": "string"},
                        "fix_text": {"type": "string"}
                    },
                    "required": ["id", "type", "text"]
                }
            },
            "source_pages": {"type": "array", "items": {"type": "integer"}}
        },
        "required": ["symptom", "steps", "source_pages"]
    }
}
```

### render_settings_configurator

```json
{
    "name": "render_settings_configurator",
    "description": "Generate a settings recommendation widget. Use when users ask what settings for a material, thickness, or process. ALL values from manual.",
    "input_schema": {
        "type": "object",
        "properties": {
            "process": {"type": "string"},
            "material": {"type": "string"},
            "thickness_range": {"type": "string"},
            "settings_options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string"},
                        "voltage": {"type": "string"},
                        "wire_speed": {"type": "string"},
                        "amperage": {"type": "string"},
                        "gas_type": {"type": "string"},
                        "gas_flow_rate": {"type": "string"},
                        "wire_type": {"type": "string"},
                        "wire_diameter": {"type": "string"}
                    }
                }
            },
            "tips": {"type": "array", "items": {"type": "string"}},
            "source_pages": {"type": "array", "items": {"type": "integer"}}
        },
        "required": ["process", "settings_options", "source_pages"]
    }
}
```

## Agent Loop

```python
async def run_agent(user_message: str, conversation_history: list, event_queue: asyncio.Queue):
    messages = conversation_history + [{"role": "user", "content": user_message}]

    while True:
        # Call Claude with streaming
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
            stream=True
        )

        full_response = await process_stream(response, event_queue)

        # Check for tool calls
        tool_calls = [b for b in full_response.content if b.type == "tool_use"]

        if not tool_calls:
            break  # Agent is done

        # Execute tools
        messages.append({"role": "assistant", "content": full_response.content})

        tool_results = []
        for tc in tool_calls:
            result = await handle_tool_call(tc.name, tc.input)

            # Emit artifacts to frontend
            if result.get("type") == "artifact":
                await event_queue.put({
                    "type": "artifact",
                    "html": result["artifact_html"],
                    "title": result["title"],
                    "pages": result["source_pages"]
                })

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": json.dumps(result) if result.get("type") != "artifact"
                           else "Artifact rendered successfully."
            })

        messages.append({"role": "user", "content": tool_results})

    await event_queue.put({"type": "done"})
```

## Tool Handler Dispatch

```python
RENDERERS = {
    "render_polarity_diagram": render_polarity_svg,
    "render_duty_cycle_calculator": render_duty_cycle_widget,
    "render_troubleshooting_flow": render_troubleshooting_widget,
    "render_settings_configurator": render_settings_widget,
}

async def handle_tool_call(tool_name: str, tool_input: dict) -> dict:
    if tool_name == "search_manual":
        evidence = knowledge_store.search(
            query=tool_input["query"],
            process_filter=tool_input.get("process_filter"),
            topic_filter=tool_input.get("topic_filter")
        )
        return evidence.to_dict()

    elif tool_name == "get_manual_page_image":
        page = tool_input["page_number"]
        image_b64 = encode_image_base64(f"static/page_images/page_{page}.png")
        return {
            "type": "manual_page",
            "page": page,
            "image_base64": image_b64,
            "highlight": tool_input.get("highlight_region")
        }

    elif tool_name in RENDERERS:
        html = RENDERERS[tool_name](tool_input)
        return {
            "type": "artifact",
            "artifact_html": html,
            "title": generate_title(tool_name, tool_input),
            "source_pages": tool_input.get("source_pages", [])
        }
```
