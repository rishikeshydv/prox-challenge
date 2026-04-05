#!/usr/bin/env python3
"""
extract_knowledge.py — Two-pass extraction pipeline for the Vulcan OmniPro 220 manual.

Pass 1: PyMuPDF structural extraction (text + layout blocks + page images)
Pass 2: Claude Vision semantic extraction (diagrams, tables, labels)

Output: backend/knowledge/knowledge_base.json
        backend/static/page_images/page_N.png
"""

import asyncio
import base64
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
import fitz  # PyMuPDF
from dotenv import load_dotenv
import time

load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.parent
FILES_DIR = PROJECT_ROOT / "files"
PAGE_IMAGES_DIR = PROJECT_ROOT / "backend" / "static" / "page_images"
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "backend" / "knowledge" / "knowledge_base.json"

PAGE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Claude extraction prompt
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """\
You are extracting structured information from page {page_num} of the Vulcan OmniPro 220 owner's manual (Harbor Freight model 57812).

Extract ALL information on this page into the following JSON structure. Return ONLY valid JSON, no markdown fences.

{{
  "page_number": {page_num},
  "section_title": "<string or null>",
  "content_blocks": [
    {{
      "type": "text" | "table" | "diagram_description" | "warning" | "procedure" | "specification",
      "content": "<extracted text or structured data>",
      "region": "<descriptive label like 'duty-cycle-matrix' or 'front-panel-diagram'>",
      "related_process": "MIG" | "TIG" | "Stick" | "Flux-Cored" | "all" | null,
      "topics": ["setup", "polarity", "troubleshooting", "safety", "duty-cycle", "specifications", "parts", "maintenance"]
    }}
  ],
  "tables": [
    {{
      "title": "<table title>",
      "headers": ["col1", "col2"],
      "rows": [["val1", "val2"]],
      "region": "<label>"
    }}
  ],
  "diagram_labels": ["<every labeled component, connector, port, or indicator visible in diagrams>"],
  "warnings": ["<any safety warnings on this page>"]
}}

Be exhaustive. Extract every fact, every number, every label. Do not summarize — preserve specifics.
For tables, capture every row and column exactly as shown.
For diagrams, list every labeled component, connector, port, and indicator you can identify.
"""

# ---------------------------------------------------------------------------
# Pass 1: Structural extraction with PyMuPDF
# ---------------------------------------------------------------------------

def extract_structural(pdf_path: Path) -> dict[int, dict]:
    """Extract text and layout blocks from all pages. Save page images."""
    doc = fitz.open(str(pdf_path))
    structural: dict[int, dict] = {}

    print(f"  PDF has {len(doc)} pages")
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_1based = page_num + 1

        # Save high-res page image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        image_path = PAGE_IMAGES_DIR / f"page_{page_1based}.png"
        pix.save(str(image_path))

        # Raw text
        text = page.get_text("text")

        # Layout blocks (useful for table detection)
        blocks = page.get_text("dict")["blocks"]

        structural[page_1based] = {
            "page_number": page_1based,
            "raw_text": text,
            "blocks": blocks,
            "image_path": str(image_path),
        }

    doc.close()
    return structural


# ---------------------------------------------------------------------------
# Pass 2: Semantic extraction with Claude Vision
# ---------------------------------------------------------------------------

async def extract_page_knowledge(
    client: anthropic.AsyncAnthropic, image_path: Path, page_num: int
) -> dict:
    """Send page image to Claude for structured semantic extraction, with retry on 429."""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    prompt = EXTRACTION_PROMPT.format(page_num=page_num)

    max_retries = 5
    backoff = 15  # seconds — start conservative given 8k token/min limit
    for attempt in range(max_retries):
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            break  # success
        except anthropic.RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait = backoff * (2 ** attempt)
            print(f"  Rate limited on page {page_num}, retrying in {wait}s (attempt {attempt + 1}/{max_retries})...")
            await asyncio.sleep(wait)

    raw = response.content[0].text.strip()
    # Strip any accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


def _load_existing_semantic(kb_path: Path) -> dict[int, dict]:
    """Load successfully extracted pages from an existing knowledge base."""
    if not kb_path.exists():
        return {}
    with open(kb_path) as f:
        kb = json.load(f)
    existing = {}
    for section in kb.get("sections", []):
        for page_num in section.get("pages", []):
            # Only keep pages that were extracted without error
            if not any(
                item.get("_extraction_error") for item in section.get("items", [])
            ) and section.get("title") != f"Page {page_num}" or section.get("items"):
                # Reconstruct minimal semantic dict so assemble_knowledge_base still works
                existing[page_num] = {
                    "page_number": page_num,
                    "section_title": section.get("title"),
                    "content_blocks": [
                        {
                            "type": item.get("type", "text"),
                            "content": item.get("content", ""),
                            "region": item.get("region", ""),
                            "related_process": item.get("related_process"),
                            "topics": item.get("topics", []),
                        }
                        for item in section.get("items", [])
                        if item.get("type") not in ("visual", "warning")
                    ],
                    "tables": [
                        {
                            "title": item["content"].get("title", ""),
                            "headers": item["content"].get("headers", []),
                            "rows": item["content"].get("rows", []),
                            "region": item.get("region", ""),
                        }
                        for item in section.get("items", [])
                        if item.get("type") == "table" and isinstance(item.get("content"), dict)
                    ],
                    "diagram_labels": section.get("diagram_labels", []),
                    "warnings": section.get("warnings", []),
                }
    return existing


async def extract_all_pages(
    structural: dict[int, dict],
    concurrency: int = 1,
    existing_semantic: Optional[dict] = None,
) -> dict[int, dict]:
    """Extract semantic knowledge from all pages with controlled concurrency.

    Pages already present in existing_semantic (no error) are skipped.
    """
    client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    sem = asyncio.Semaphore(concurrency)
    results: dict[int, dict] = dict(existing_semantic or {})

    pages_to_extract = {
        p: i for p, i in structural.items() if p not in results
    }

    if existing_semantic:
        skipped = len(structural) - len(pages_to_extract)
        print(f"  Skipping {skipped} already-extracted pages, processing {len(pages_to_extract)} remaining.")

    async def extract_one(page_num: int, info: dict):
        async with sem:
            print(f"  Extracting page {page_num}...")
            try:
                data = await extract_page_knowledge(
                    client, Path(info["image_path"]), page_num
                )
                results[page_num] = data
            except Exception as e:
                print(f"  ERROR on page {page_num}: {e}")
                results[page_num] = {
                    "page_number": page_num,
                    "section_title": None,
                    "content_blocks": [],
                    "tables": [],
                    "diagram_labels": [],
                    "warnings": [],
                    "_extraction_error": str(e),
                }

    await asyncio.gather(*[extract_one(p, i) for p, i in sorted(pages_to_extract.items())])
    return results


# ---------------------------------------------------------------------------
# Assemble knowledge base
# ---------------------------------------------------------------------------

def _make_item_id(page_num: int, block_idx: int, suffix: str = "") -> str:
    return f"p{page_num}_b{block_idx}{('_' + suffix) if suffix else ''}"


def assemble_knowledge_base(
    structural: dict[int, dict],
    semantic: dict[int, dict],
    pdf_name: str,
) -> dict:
    """Merge structural + semantic data into the knowledge base schema."""
    sections = []

    for page_num in sorted(structural.keys()):
        sem = semantic.get(page_num, {})
        raw_text = structural[page_num]["raw_text"]

        section_title = sem.get("section_title") or f"Page {page_num}"
        content_blocks = sem.get("content_blocks", [])
        tables = sem.get("tables", [])
        diagram_labels = sem.get("diagram_labels", [])
        warnings = sem.get("warnings", [])

        # Derive topic + process tags from content
        all_topics: set[str] = set()
        all_processes: set[str] = set()
        for block in content_blocks:
            for topic in block.get("topics", []):
                all_topics.add(topic)
            proc = block.get("related_process")
            if proc and proc != "all":
                all_processes.add(proc)

        items = []

        # Content block items
        for idx, block in enumerate(content_blocks):
            item_id = _make_item_id(page_num, idx)
            content = block.get("content", "")
            items.append(
                {
                    "id": item_id,
                    "type": block.get("type", "text"),
                    "content": content,
                    "page": page_num,
                    "region": block.get("region", ""),
                    "source_type": "text",
                    "related_process": block.get("related_process"),
                    "topics": block.get("topics", []),
                }
            )

        # Table items
        for t_idx, table in enumerate(tables):
            item_id = _make_item_id(page_num, t_idx, "table")
            items.append(
                {
                    "id": item_id,
                    "type": "table",
                    "content": {
                        "title": table.get("title", ""),
                        "headers": table.get("headers", []),
                        "rows": table.get("rows", []),
                    },
                    "page": page_num,
                    "region": table.get("region", ""),
                    "source_type": "table",
                    "topics": list(all_topics),
                }
            )

        # Visual / diagram item if labels were found
        if diagram_labels:
            item_id = _make_item_id(page_num, 0, "diagram")
            desc = f"Diagram on page {page_num}. Labeled components: {', '.join(diagram_labels)}."
            items.append(
                {
                    "id": item_id,
                    "type": "visual",
                    "description": desc,
                    "labels": diagram_labels,
                    "page": page_num,
                    "region": "diagram",
                    "source_type": "diagram",
                    "image_path": f"page_images/page_{page_num}.png",
                }
            )

        # Warnings as separate items for priority retrieval
        for w_idx, warning in enumerate(warnings):
            item_id = _make_item_id(page_num, w_idx, "warn")
            items.append(
                {
                    "id": item_id,
                    "type": "warning",
                    "content": warning,
                    "page": page_num,
                    "region": "safety",
                    "source_type": "text",
                    "topics": ["safety"],
                }
            )

        section_id = f"section_p{page_num}"
        sections.append(
            {
                "id": section_id,
                "title": section_title,
                "pages": [page_num],
                "content_type": "mixed",
                "process": list(all_processes)[0] if len(all_processes) == 1 else "all",
                "topics": list(all_topics),
                "text_content": raw_text,
                "diagram_labels": diagram_labels,
                "warnings": warnings,
                "items": items,
            }
        )

    return {
        "manual_metadata": {
            "product": "Vulcan OmniPro 220",
            "model": "57812",
            "source_pdf": pdf_name,
            "total_pages": len(structural),
            "extraction_date": date.today().isoformat(),
        },
        "sections": sections,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    # Find the owner's manual
    pdf_path = FILES_DIR / "owner-manual.pdf"
    if not pdf_path.exists():
        # Fall back to any PDF in files/
        pdfs = list(FILES_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"ERROR: No PDFs found in {FILES_DIR}")
            sys.exit(1)
        pdf_path = pdfs[0]
        print(f"Using: {pdf_path.name}")

    print(f"\n=== Pass 1: Structural extraction ({pdf_path.name}) ===")
    structural = extract_structural(pdf_path)
    print(f"  Saved {len(structural)} page images to {PAGE_IMAGES_DIR}")

    print(f"\n=== Pass 2: Semantic extraction (Claude Vision) ===")
    # Allow limiting pages for testing: EXTRACT_PAGES=1-5 python extract_knowledge.py
    pages_env = os.environ.get("EXTRACT_PAGES")
    if pages_env:
        start, end = map(int, pages_env.split("-"))
        structural = {k: v for k, v in structural.items() if start <= k <= end}
        print(f"  Limited to pages {start}-{end} (EXTRACT_PAGES env var)")

    existing_semantic = _load_existing_semantic(KNOWLEDGE_BASE_PATH)
    semantic = await extract_all_pages(structural, existing_semantic=existing_semantic)

    print(f"\n=== Assembling knowledge base ===")
    kb = assemble_knowledge_base(structural, semantic, pdf_path.name)

    KNOWLEDGE_BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(KNOWLEDGE_BASE_PATH, "w") as f:
        json.dump(kb, f, indent=2)

    total_items = sum(len(s["items"]) for s in kb["sections"])
    print(f"  Written: {KNOWLEDGE_BASE_PATH}")
    print(f"  Sections: {len(kb['sections'])}")
    print(f"  Total items: {total_items}")
    print("\nDone. Run scripts/build_embeddings.py next.")


if __name__ == "__main__":
    asyncio.run(main())
