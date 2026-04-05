"""
main.py — FastAPI server with SSE streaming endpoint.
"""

from __future__ import annotations

import asyncio
import json
import uuid
import re
from pathlib import Path
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import run_agent
from knowledge.store import knowledge_store


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading knowledge store...")
    knowledge_store.load()
    print("Knowledge store ready.")
    yield


app = FastAPI(title="Vulcan OmniPro 220 Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# In-memory conversation store (per conversation_id)
_conversations: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class SpecialistContextRequest(BaseModel):
    current_question: Optional[str] = None
    title: Optional[str] = None
    source_pages: list[int] = []
    process: Optional[str] = None
    polarity: Optional[str] = None
    symptom: Optional[str] = None


def _infer_process_filter(request: SpecialistContextRequest) -> str | None:
    if request.process:
        return request.process

    query = " ".join(
        part for part in [
            request.current_question or "",
            request.title or "",
        ]
        if part
    ).lower()

    for label in ("mig", "tig", "stick", "flux-cored", "flux cored"):
        if label in query:
            return "Flux-Cored" if label in ("flux-cored", "flux cored") else label.upper() if label != "stick" else "Stick"

    return None


def _infer_topic_filter(request: SpecialistContextRequest) -> str | None:
    query = " ".join(
        part for part in [
            request.current_question or "",
            request.title or "",
            request.polarity or "",
            request.symptom or "",
        ]
        if part
    ).lower()

    if request.symptom:
        return "troubleshooting"
    if "duty cycle" in query or "how long can i weld" in query:
        return "duty-cycle"
    if request.polarity or "polarity" in query or "ground clamp" in query or "socket" in query:
        return "polarity"
    if "manual" in query or "page" in query or "panel" in query:
        return "parts"
    if any(token in query for token in ("settings", "voltage", "wire speed", "amperage", "thickness")):
        return "setup"
    if request.process:
        return "setup"
    return None


def _query_numbers(query: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", query)


def _extract_voltage_and_amperage(query: str) -> tuple[str | None, str | None]:
    voltage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:v|vac)\b", query, re.IGNORECASE)
    amperage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:a|amp|amps)\b", query, re.IGNORECASE)
    return (
        voltage_match.group(1) if voltage_match else None,
        amperage_match.group(1) if amperage_match else None,
    )


def _row_text(row: list) -> str:
    return " ".join(str(cell) for cell in row)


def _build_grounded_facts(
    request: SpecialistContextRequest,
    process_filter: str | None,
    evidence,
) -> list[str]:
    query = " ".join(
        part for part in [
            request.current_question or "",
            request.title or "",
            request.polarity or "",
            request.symptom or "",
        ]
        if part
    )
    query_lower = query.lower()
    numbers = _query_numbers(query)
    voltage, amperage = _extract_voltage_and_amperage(query)
    facts: list[str] = []

    if "duty cycle" in query_lower:
        for table in evidence.tables:
            headers = table.get("headers", [])
            for row in table.get("rows", []):
                row_text = _row_text(row)
                row_lower = row_text.lower()
                has_exact_voltage = voltage is None or voltage in row_text
                has_exact_amperage = amperage is None or amperage in row_text
                has_all_numbers = all(number in row_text for number in numbers)
                if has_exact_voltage and has_exact_amperage and has_all_numbers and ("vac" in row_lower or "v" in row_lower):
                    facts.append(
                        f"Manual table match on page {table.get('page', '?')}: "
                        f"{', '.join(f'{headers[i]}={row[i]}' for i in range(min(len(headers), len(row))))}"
                    )
        for chunk in evidence.text_chunks:
            content = str(chunk.get("content", ""))
            if all(number in content for number in numbers):
                facts.append(
                    f"Manual text on page {chunk.get('page', '?')}: {content[:220]}"
                )

    if ("polarity" in query_lower or "ground clamp" in query_lower or "socket" in query_lower) and not facts:
        for chunk in evidence.text_chunks:
            content = str(chunk.get("content", ""))
            content_lower = content.lower()
            if "ground" in content_lower or "polarity" in content_lower or "socket" in content_lower:
                facts.append(
                    f"Manual guidance on page {chunk.get('page', '?')}: {content[:220]}"
                )

    # Fallback to top snippets if no exact facts were found.
    if not facts:
        for chunk in evidence.text_chunks[:3]:
            content = str(chunk.get("content", "")).strip().replace("\n", " ")
            if content:
                facts.append(
                    f"Manual evidence on page {chunk.get('page', '?')}: {content[:220]}"
                )

    # Deduplicate while preserving order.
    deduped: list[str] = []
    seen: set[str] = set()
    for fact in facts:
        if fact not in seen:
            deduped.append(fact)
            seen.add(fact)
    return deduped[:4]


# ---------------------------------------------------------------------------
# SSE endpoint
# ---------------------------------------------------------------------------

async def event_generator(
    message: str,
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    event_queue: asyncio.Queue = asyncio.Queue()
    history = _conversations.get(conversation_id, [])

    # Run agent in background task
    agent_task = asyncio.create_task(
        run_agent(message, history, event_queue)
    )

    try:
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                yield "data: {\"type\":\"error\",\"message\":\"Timeout\"}\n\n"
                break

            yield f"data: {json.dumps(event)}\n\n"

            if event["type"] in ("done", "error"):
                break
    finally:
        # Store updated history
        try:
            updated_history = await agent_task
            _conversations[conversation_id] = updated_history
        except Exception as e:
            print(f"Agent error: {e}")
            agent_task.cancel()


@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    conversation_id = request.conversation_id or str(uuid.uuid4())

    return StreamingResponse(
        event_generator(request.message, conversation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Conversation-Id": conversation_id,
        },
    )


@app.delete("/api/chat/{conversation_id}")
async def clear_conversation(conversation_id: str):
    _conversations.pop(conversation_id, None)
    return {"status": "cleared"}


@app.post("/api/specialist-context")
async def specialist_context(request: SpecialistContextRequest):
    if knowledge_store._kb is None:
        knowledge_store.load()

    query_parts = [
        request.current_question or "",
        request.title or "",
        request.process or "",
        request.polarity or "",
        request.symptom or "",
    ]
    query = " ".join(part.strip() for part in query_parts if part and part.strip())
    if not query:
        raise HTTPException(status_code=400, detail="Missing context query")

    process_filter = _infer_process_filter(request)
    topic_filter = _infer_topic_filter(request)

    evidence = knowledge_store.search(
        query=query,
        process_filter=process_filter,
        topic_filter=topic_filter,
        top_k=6,
    )

    facts = _build_grounded_facts(request, process_filter, evidence)

    snippets = []
    for chunk in evidence.text_chunks[:5]:
        content = str(chunk.get("content", "")).strip().replace("\n", " ")
        if not content:
            continue
        snippets.append(
            {
                "page": chunk.get("page"),
                "section": chunk.get("section", ""),
                "content": content[:500],
                "type": chunk.get("type", "text"),
            }
        )

    table_summaries = []
    for table in evidence.tables[:2]:
        rows = table.get("rows", [])[:3]
        row_preview = " | ".join(
            ", ".join(str(cell) for cell in row[:4]) for row in rows
        )
        table_summaries.append(
            {
                "page": table.get("page"),
                "section": table.get("section", ""),
                "title": table.get("title", ""),
                "preview": row_preview[:500],
            }
        )

    return {
        "query": query,
        "process_filter": process_filter,
        "topic_filter": topic_filter,
        "source_pages": evidence.source_pages,
        "section_titles": evidence.section_titles,
        "facts": facts,
        "snippets": snippets,
        "tables": table_summaries,
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
