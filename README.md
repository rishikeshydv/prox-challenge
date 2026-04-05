# Vulcan OmniPro 220 Workshop Assistant

An agentic support assistant for the Vulcan OmniPro 220 welder. It answers setup and troubleshooting questions from the owner's manual, renders visual artifacts when text is not enough, and can optionally launch a Tavus live specialist for guided walkthroughs.

The product is built around one idea: for this kind of machine, a good answer is often not just a paragraph. Sometimes the best response is a polarity diagram, a duty-cycle lookup, a troubleshooting flow, or the exact manual page.

## What The Agent Does

The assistant helps with:

- setup and polarity questions
- duty cycle lookups
- troubleshooting flows
- settings recommendations
- exact manual-page visuals

Example questions:

- `What polarity setup do I need for TIG welding?`
- `What's the duty cycle for MIG welding at 200A on 240V?`
- `Show me the front panel controls`
- `My weld has porosity. Troubleshoot it step by step.`

## How It Works

The system has three layers:

1. A streaming Claude-based agent decides how to answer the question.
2. A retrieval layer pulls evidence from a structured manual knowledge base.
3. The frontend renders either text or a workbench artifact.

The main runtime path is:

- FastAPI backend receives the chat request
- Claude is prompted to always search the manual first
- Claude may call one of several tools
- tool output is streamed to the frontend over SSE
- the frontend pins the latest artifact in a persistent workbench

### Response modes

The agent chooses among these response modes:

- text only
- text + manual page image
- polarity diagram
- duty cycle calculator
- troubleshooting flow
- settings configurator

This selection logic lives in [backend/agent.py](/Users/rishi/Desktop/prox-challenge/backend/agent.py).

## Architecture

### Backend

- `backend/main.py`
  FastAPI app, SSE chat endpoint, manual-knowledge specialist endpoint, static page image hosting.
- `backend/agent.py`
  Claude loop, system prompt, tool calling, streamed text/artifact events.
- `backend/tool_handlers.py`
  Dispatches tool calls to retrieval or renderers and attaches artifact metadata.
- `backend/knowledge/store.py`
  Hybrid retrieval over the extracted manual.
- `backend/renderers/*`
  HTML/SVG renderers for polarity, duty cycle, troubleshooting, and settings.

### Frontend

- `frontend/app/page.tsx`
  Orchestrates the split layout.
- `frontend/app/hooks/useAgentStream.ts`
  Manages SSE parsing, conversation state, current workbench item, and mobile sheet state.
- `frontend/app/components/ChatPane.tsx`
  Chat UI and streaming experience.
- `frontend/app/components/ArtifactPane.tsx`
  Persistent workbench plus optional Tavus specialist modal.

### Optional live specialist

The Tavus specialist is not the primary response surface. The workbench stays primary. Tavus is an optional second layer for cases where the user wants a live walkthrough.

That decision was intentional:

- the manual-backed artifact remains the source of truth
- the UI does not become an always-on avatar product
- Tavus is only offered when a live explanation adds value

The Tavus flow lives in:

- [frontend/app/api/tavus/session/start/route.ts](/Users/rishi/Desktop/prox-challenge/frontend/app/api/tavus/session/start/route.ts)
- [frontend/app/api/tavus/session/[id]/end/route.ts](/Users/rishi/Desktop/prox-challenge/frontend/app/api/tavus/session/[id]/end/route.ts)
- [frontend/lib/tavus/client.ts](/Users/rishi/Desktop/prox-challenge/frontend/lib/tavus/client.ts)

## Design Decisions

### 1. Artifact-first, not chatbot-first

The earliest version felt too much like a generic chat app. I redesigned the frontend around a workbench model:

- chat on the left
- latest artifact pinned on the right on desktop
- bottom sheet on mobile

This better fits the actual use case. A welder setup question is often a visual task, not a text task.

### 2. The agent must search the manual before answering

The system prompt in [backend/agent.py](/Users/rishi/Desktop/prox-challenge/backend/agent.py) forces the agent to use `search_manual` before any technical answer. This was a deliberate guardrail to reduce confident hallucinations about:

- polarity
- settings
- duty cycle
- machine controls

### 3. Generated visuals are preferred only when they add clarity

I did not treat all images the same.

- For polarity/setup questions, a generated diagram is usually better than dumping a raw PDF page.
- For front-panel layouts, parts diagrams, and actual manual illustrations, the exact manual page is better.

That distinction keeps the response crisp instead of cluttered.

### 4. Tavus is grounded, not free-floating

The Tavus specialist is launched with context pulled from `backend/knowledge`, not just from the current UI text. I added a backend endpoint that extracts grounded facts, relevant pages, and section titles so Tavus starts from manual evidence instead of improvising from a vague summary.

### 5. Conversations are kept simple on purpose

Conversation history is stored in memory. There is no database, auth, or persistence layer. For this challenge, I chose simplicity over infrastructure because the important work here is:

- retrieval quality
- artifact rendering
- UI clarity

not multi-user production plumbing.

## Knowledge Extraction And Representation

The source document is the Vulcan OmniPro 220 manual in `files/`.

The extraction pipeline is two-pass:

### Pass 1: structural extraction

Implemented in [scripts/extract_knowledge.py](/Users/rishi/Desktop/prox-challenge/scripts/extract_knowledge.py).

Using PyMuPDF, the script:

- opens the PDF
- extracts raw text and layout blocks
- renders every page to a PNG

Outputs:

- `backend/static/page_images/page_N.png`
- structural page data in memory for the second pass

### Pass 2: semantic extraction

The same script sends each rendered page image to Claude Vision and asks for structured JSON extraction.

It extracts:

- section title
- content blocks
- tables
- diagram labels
- warnings

The extracted page knowledge is assembled into:

- `backend/knowledge/knowledge_base.json`

### How knowledge is represented

The knowledge base is organized as sections with item-level records. Each item carries metadata such as:

- page number
- type
- region
- related welding process
- topic tags

Common item types include:

- `text`
- `procedure`
- `warning`
- `specification`
- `table`
- `visual`

This representation matters because the agent is not just doing plain-text RAG. It can retrieve:

- text chunks for direct answers
- tables for exact numerical lookups
- page images for manual visuals
- diagram descriptions for visual grounding

## Retrieval Strategy

Retrieval is hybrid, implemented in [backend/knowledge/store.py](/Users/rishi/Desktop/prox-challenge/backend/knowledge/store.py):

- Chroma semantic search over item-level embeddings
- keyword search over item content and metadata
- optional process/topic filters

The results are packaged into an `EvidencePack` with:

- `text_chunks`
- `tables`
- `page_images`
- `source_pages`
- `section_titles`

I chose hybrid retrieval because a manual contains both fuzzy language and exact facts:

- semantic search helps with natural-language questions
- keyword and metadata filters help with exact process/topic targeting
- tables must remain available in structured form for things like duty cycle answers

## Tooling

The agent has a small set of purpose-built tools in [backend/tools.py](/Users/rishi/Desktop/prox-challenge/backend/tools.py):

- `search_manual`
- `get_manual_page_image`
- `render_polarity_diagram`
- `render_duty_cycle_calculator`
- `render_troubleshooting_flow`
- `render_settings_configurator`

These tools are intentionally narrow. I wanted the model to choose among a few high-value actions rather than having many loosely overlapping tools.

## Run The Project

### Prerequisites

- Python 3.10+
- Node.js 18+
- Anthropic API key
- Tavus credentials if you want the live specialist

### 1. Configure environment variables

Backend env in the repo root:

Create `.env` in the project root:

```bash
cp .env.example .env
```

At minimum, set:

```bash
ANTHROPIC_API_KEY=...
```

Frontend env for Tavus:

Create `frontend/.env.local`:

```bash
TAVUS_API_KEY=...
TAVUS_PERSONA_ID=...
TAVUS_REPLICA_ID=...
BACKEND_API_BASE_URL=http://127.0.0.1:8000
```

Optional Tavus variables:

```bash
TAVUS_CALLBACK_URL=
TAVUS_MEMORY_STORE=
TAVUS_DOCUMENT_IDS=
```

Important note:

- the FastAPI backend reads the repo-root `.env`
- the Next app reads `frontend/.env.local`

If Tavus says it is not configured, the variables are usually in the wrong file or the Next dev server needs a restart.

### 2. Install backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Build the knowledge base

If `backend/knowledge/knowledge_base.json` and `backend/static/page_images/` do not already exist, run:

```bash
cd /Users/rishi/Desktop/prox-challenge
./backend/.venv/bin/python scripts/extract_knowledge.py
./backend/.venv/bin/python scripts/build_embeddings.py
```

This step can take time because the semantic extraction pass uses Claude Vision on every page.

### 4. Start the backend

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
```

### 6. Start the frontend

```bash
cd frontend
npm run dev
```

Open:

- `http://localhost:3000`

### 7. Build checks

Frontend:

```bash
cd frontend
npm run build
```

Backend import smoke test:

```bash
cd backend
./.venv/bin/python -c 'import main; print("backend import ok")'
```

## Typical Flow

1. User asks a question in chat.
2. Frontend posts to `/api/chat`.
3. Next rewrites `/api/chat` to FastAPI.
4. FastAPI streams events back over SSE.
5. Claude searches the manual, then either answers directly or calls a render/manual tool.
6. The frontend turns artifact events into a workbench item and pins it.
7. If the user wants a live walkthrough, `Talk me through this` launches a Tavus session with grounded manual context.

## Known Limitations

- Conversation history is in memory only.
- Retrieval quality depends on extraction quality from the PDF.
- Some manual pages mix unrelated topics, which can make retrieval noisy.
- Tavus is grounded strongly at session creation time, but it is not doing backend retrieval on every Tavus turn.
- The troubleshooting renderer is intentionally lightweight and still has room to improve visually.

## What I Would Improve Next

- add stronger per-turn grounding for Tavus, not just session-start grounding
- improve retrieval ranking around mixed-topic manual pages
- add automated tests for artifact metadata and retrieval correctness
- make troubleshooting artifacts more visual and less text-driven
- persist conversations and workbench state

## Project Structure

```text
prox-challenge/
├── backend/
│   ├── agent.py
│   ├── main.py
│   ├── tool_handlers.py
│   ├── tools.py
│   ├── knowledge/
│   ├── renderers/
│   └── static/page_images/
├── frontend/
│   ├── app/
│   ├── lib/tavus/
│   └── next.config.mjs
├── files/
├── scripts/
│   ├── extract_knowledge.py
│   └── build_embeddings.py
└── README.md
```

## Final Note

The core design principle in this project is that "grounded" should mean more than citing a page number. The agent should choose the right response shape for the job, keep the manual as the source of truth, and make visual help feel like a first-class part of the experience.
