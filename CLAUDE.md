# CLAUDE.md — Vulcan OmniPro 220 Welding Agent

## What This Is

A multimodal reasoning agent for the Vulcan OmniPro 220 welder. Answers technical questions from the 48-page owner's manual using text, interactive diagrams, calculators, troubleshooting flows, and manual page references. Artifact generation is a first-class output mode, not an afterthought.

## Stack

- **Backend:** Python 3.12+, FastAPI, Anthropic SDK, SSE streaming, httpx
- **Frontend:** Next.js 14+ (App Router), TypeScript, Tailwind CSS
- **Knowledge:** Structured JSON + ChromaDB for semantic search
- **Artifacts:** Self-contained HTML/SVG rendered in sandboxed iframes; CSS stagger animations, no postMessage
- **TTS:** Hume AI REST API (`/v0/tts`) — proxied through FastAPI to keep API key server-side
- **PDF Processing:** PyMuPDF + Claude Vision API

## Project Structure

```
├── claude.md                    # This file (always loaded)
├── docs/
│   ├── architecture.md          # System architecture and data flow
│   ├── knowledge-pipeline.md    # PDF extraction, schema, retrieval
│   ├── agent-tools.md           # Tool schemas, system prompt, agent loop
│   ├── renderers.md             # Artifact renderer specs and design system
│   ├── frontend.md              # UI layout, SSE protocol, state management
│   └── testing.md               # Test queries and quality checklist
├── files/                       # Source manuals (provided)
├── backend/
│   ├── main.py                  # FastAPI app, SSE endpoint
│   ├── agent.py                 # Claude agent, system prompt, tool dispatch
│   ├── tools.py                 # Tool definitions (schemas)
│   ├── tool_handlers.py         # Tool execution logic
│   ├── knowledge/
│   │   ├── extractor.py         # PDF → structured JSON
│   │   ├── store.py             # Retrieval (semantic + keyword)
│   │   ├── knowledge_base.json  # Pre-extracted knowledge
│   │   └── embeddings/          # ChromaDB store
│   ├── renderers/
│   │   ├── polarity_diagram.py
│   │   ├── duty_cycle_calculator.py
│   │   ├── troubleshooting_flow.py
│   │   ├── settings_configurator.py
│   │   └── manual_page.py
│   └── static/page_images/      # Extracted page PNGs
├── frontend/
│   └── app/
│       ├── page.tsx             # Main layout
│       ├── components/          # ChatPane, ArtifactPane, etc.
│       ├── hooks/               # useAgentStream
│       └── types/               # Shared types
└── scripts/
    ├── extract_knowledge.py     # One-time PDF processing
    ├── build_embeddings.py      # One-time vector store build
    └── test_queries.py          # Test suite
```

## Core Rules

1. **Evidence-first.** The agent MUST call `search_manual` before answering any technical question. It never guesses specs, settings, or procedures from memory.

2. **Structured tool data → deterministic rendering.** Claude fills structured tool schemas with manual-backed data. Python renderers turn that data into HTML/SVG. Claude never writes raw UI code.

3. **Every fact is grounded.** Every number, connection, and setting traces back to a page number and section in the manual. Source pages are cited in every artifact.

4. **Six response modes.** The agent chooses: text only, manual page image, polarity diagram, duty cycle calculator, troubleshooting flow, settings configurator, or clarification question. Not a binary text/image toggle.

5. **Safety first.** Surface manual warnings whenever relevant. Wrong polarity or wiring can damage the machine or injure the user.

## Detailed Specs

Reference these files when working on specific layers:

| Working on...            | Read                        |
|--------------------------|-----------------------------|
| Overall system design    | `docs/architecture.md`      |
| PDF extraction / RAG     | `docs/knowledge-pipeline.md`|
| Agent, prompts, tools    | `docs/agent-tools.md`       |
| Artifact renderers       | `docs/renderers.md`         |
| Frontend UI              | `docs/frontend.md`          |
| Testing / QA             | `docs/testing.md`           |

## Quick Start

```bash
cp .env.example .env           # Add ANTHROPIC_API_KEY and HUME_API_KEY
cd backend && pip install -r requirements.txt
python ../scripts/extract_knowledge.py
python ../scripts/build_embeddings.py
uvicorn main:app --reload --port 8000
# In another terminal:
cd frontend && npm install && npm run dev
```

## Tone

The user is in their garage with a new welder. They're handy but not a pro. Talk like a knowledgeable friend in the shop — direct, specific, confident. "Connect the torch to the negative Dinse connector" not "connect the appropriate lead to the correct terminal."