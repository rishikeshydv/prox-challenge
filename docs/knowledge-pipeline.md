# Knowledge Pipeline

## Overview

Process the 48-page manual into a structured, grounded knowledge base where every fact links back to its source page, section, and region type. This is the foundation — everything downstream depends on extraction quality.

## Two-Pass Extraction

### Pass 1 — Structural Extraction (PyMuPDF)

Extract raw data from the PDF without AI interpretation:

```python
import fitz  # PyMuPDF

def extract_structural(pdf_path: str, output_dir: str):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]

        # Save page as high-res image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution
        pix.save(f"{output_dir}/page_{page_num + 1}.png")

        # Extract raw text
        text = page.get_text("text")

        # Extract text with layout preservation (helps with tables)
        blocks = page.get_text("dict")["blocks"]

    doc.close()
```

This gives us: page images (for the artifact pane), raw text (for keyword search), and layout blocks (for table detection).

### Pass 2 — Semantic Extraction (Claude Vision)

Send each page image to Claude with a structured extraction prompt. This is the critical step that captures diagrams, tables, labels, and visual content that text extraction misses.

#### Extraction Prompt Template

```
You are extracting structured information from page {page_num} of the Vulcan OmniPro 220 owner's manual.

Extract ALL information on this page into the following JSON structure:

{
  "page_number": <int>,
  "section_title": "<string or null>",
  "content_blocks": [
    {
      "type": "text" | "table" | "diagram_description" | "warning" | "procedure" | "specification",
      "content": "<extracted text or structured data>",
      "region": "<descriptive label like 'duty-cycle-matrix' or 'front-panel-diagram'>",
      "related_process": "MIG" | "TIG" | "Stick" | "Flux-Cored" | "all" | null,
      "topics": ["setup", "polarity", "troubleshooting", "safety", "duty-cycle", "specifications", "parts", "maintenance"]
    }
  ],
  "tables": [
    {
      "title": "<table title>",
      "headers": ["col1", "col2", ...],
      "rows": [["val1", "val2", ...], ...],
      "region": "<label>"
    }
  ],
  "diagram_labels": ["<list of all labeled components visible in any diagram>"],
  "warnings": ["<any safety warnings on this page>"]
}

Be exhaustive. Extract every fact, every number, every label. Do not summarize — preserve specifics.
For tables, capture every row and column exactly as shown.
For diagrams, list every labeled component, connector, port, and indicator you can identify.
```

#### Batch Processing

Process pages in small batches to manage API costs. Consider grouping related pages (e.g., all MIG setup pages together) for better context.

```python
async def extract_page_knowledge(client, page_image_path: str, page_num: int) -> dict:
    with open(page_image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                {"type": "text", "text": EXTRACTION_PROMPT.format(page_num=page_num)}
            ]
        }]
    )

    return json.loads(response.content[0].text)
```

## Knowledge Base Schema

```json
{
  "manual_metadata": {
    "product": "Vulcan OmniPro 220",
    "model": "57812",
    "total_pages": 48,
    "extraction_date": "2025-XX-XX"
  },
  "sections": [
    {
      "id": "section_mig_setup",
      "title": "MIG Welding Setup",
      "pages": [12, 13, 14],
      "content_type": "procedural",
      "process": "MIG",
      "topics": ["setup", "polarity", "connections"],
      "text_content": "Full text of section...",
      "items": [
        {
          "id": "mig_polarity",
          "type": "fact",
          "content": "MIG welding uses DCEP. Connect gun to positive terminal, ground clamp to negative.",
          "page": 13,
          "region": "setup-steps",
          "source_type": "text"
        },
        {
          "id": "mig_duty_cycle_table",
          "type": "table",
          "content": {
            "headers": ["Amperage", "Voltage", "Duty Cycle %"],
            "rows": [[200, 24, 25], [155, 21, 60]]
          },
          "page": 14,
          "region": "duty-cycle-matrix",
          "source_type": "table"
        },
        {
          "id": "mig_front_panel_diagram",
          "type": "visual",
          "description": "Front panel showing positive and negative Dinse connectors, gas inlet, power switch, LCD",
          "labels": ["Positive (+) Dinse", "Negative (-) Dinse", "Gas inlet", "Power switch"],
          "page": 12,
          "region": "front-panel",
          "source_type": "diagram",
          "image_path": "page_images/page_12.png"
        }
      ]
    }
  ]
}
```

## Retrieval Layer

### Hybrid Approach

For a 48-page manual, use a combination rather than pure vector search:

1. **Section metadata filtering** — narrow by process (MIG/TIG/Stick/Flux-Cored) and topic (setup/troubleshooting/duty-cycle/etc.)
2. **Semantic search** — ChromaDB embeddings for natural language matching
3. **Keyword matching** — exact term lookup for part names, error codes, specific values
4. **Table-aware lookup** — direct access to duty cycle matrices and spec tables by structured query

### Evidence Pack

The retrieval function returns an evidence pack, not raw chunks:

```python
@dataclass
class EvidencePack:
    text_chunks: list[dict]       # [{content, page, section, region}]
    tables: list[dict]            # [{headers, rows, page, title}]
    page_images: list[str]        # paths to relevant page PNGs
    source_pages: list[int]       # all referenced pages
    section_titles: list[str]     # sections the evidence comes from
```

### Search Function

```python
def search_manual(query: str, process_filter: str = None, topic_filter: str = None, top_k: int = 5) -> EvidencePack:
    # 1. Semantic search
    semantic_results = chroma_collection.query(query_texts=[query], n_results=top_k * 2)

    # 2. Metadata filtering
    if process_filter:
        semantic_results = [r for r in semantic_results
                          if r.metadata.get("process") in [process_filter, "all"]]
    if topic_filter:
        semantic_results = [r for r in semantic_results
                          if topic_filter in r.metadata.get("topics", [])]

    # 3. Keyword boost
    keyword_results = keyword_search(query, knowledge_base)

    # 4. Merge, deduplicate, rank
    evidence = merge_and_rank(semantic_results, keyword_results, top_k=top_k)

    return EvidencePack(
        text_chunks=evidence.texts,
        tables=evidence.tables,
        page_images=[f"page_images/page_{p}.png" for p in evidence.visual_pages],
        source_pages=sorted(set(evidence.all_pages)),
        section_titles=list(set(evidence.sections))
    )
```

### Embedding Strategy

Embed at the **item level** (individual facts, table descriptions, procedure steps), not at the page or section level. Each embedding carries metadata:

```python
chroma_collection.add(
    documents=[item["content"] if isinstance(item["content"], str) else json.dumps(item["content"])],
    metadatas=[{
        "page": item["page"],
        "section": section["id"],
        "section_title": section["title"],
        "type": item["type"],
        "process": section.get("process", "all"),
        "topics": ",".join(section.get("topics", [])),
        "region": item.get("region", ""),
        "source_type": item.get("source_type", "text")
    }],
    ids=[item["id"]]
)
```
