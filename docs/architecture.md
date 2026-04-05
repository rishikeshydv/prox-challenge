# Architecture

## System Diagram

```
┌──────────────────────────────────────────┐
│           Next.js Frontend               │
│  Chat Pane  │  Artifact Pane (iframe)    │
│             │  Source Citation Badges     │
└──────┬──────┴────────────────────────────┘
       │ SSE stream
┌──────▼───────────────────────────────────┐
│         FastAPI Agent Server             │
│                                          │
│  ┌─────────────────────────────────┐     │
│  │   Claude Agent (System Prompt)  │     │
│  │   with tools:                   │     │
│  │   ├─ search_manual              │     │
│  │   ├─ get_manual_page_image      │     │
│  │   ├─ render_polarity_diagram    │     │
│  │   ├─ render_duty_cycle_calc     │     │
│  │   ├─ render_troubleshoot_flow   │     │
│  │   ├─ render_settings_config     │     │
│  │   └─ ask_clarification          │     │
│  └─────────────┬───────────────────┘     │
│                │                         │
│  ┌─────────────▼───────────────────┐     │
│  │   Deterministic Renderers       │     │
│  │   (tool input → HTML/SVG)       │     │
│  └─────────────┬───────────────────┘     │
│                │                         │
│  ┌─────────────▼───────────────────┐     │
│  │   Knowledge Layer               │     │
│  │   structured JSON + ChromaDB    │     │
│  │   + extracted page images       │     │
│  └─────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

## Request Flow

1. User sends message via chat UI
2. Frontend opens SSE connection to `POST /api/chat`
3. Backend adds message to conversation history
4. Claude agent is invoked with system prompt + tools + history
5. Agent streams text tokens → SSE `text_delta` events → frontend renders incrementally
6. Agent calls `search_manual` tool → backend executes retrieval → returns evidence to agent
7. Agent decides response mode and calls appropriate render tool with structured data
8. Backend catches render tool call → runs deterministic renderer → emits `artifact` SSE event
9. Agent produces final text summary referencing the artifact
10. Frontend renders artifact in iframe pane with source citations

## Key Principle: Separation of Concerns

- **Claude decides WHAT** — which response mode, which data to include, which connections to show
- **Deterministic code decides HOW** — HTML structure, SVG layout, colors, animations, interactivity
- **Knowledge layer provides TRUTH** — every fact traceable to page + section + region

This separation prevents hallucinated diagrams while keeping artifacts visually consistent.

## Prompt Caching Strategy

The system prompt and manual context are large and static. Use Anthropic's prompt caching:

```python
system_with_cache = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"}
    }
]
```

For multi-turn conversations, Anthropic automatically caches repeated message prefixes. Maintaining full conversation history benefits from this — subsequent turns are cheaper and faster.
