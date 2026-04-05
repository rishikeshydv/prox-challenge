"""
store.py — Hybrid retrieval layer: semantic (ChromaDB) + keyword + table lookup.

Returns EvidencePack objects consumed by tool_handlers.py.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = Path(__file__).parent.parent.parent
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "knowledge_base.json"
EMBEDDINGS_DIR = Path(__file__).parent / "embeddings"
COLLECTION_NAME = "vulcan_omnipro_220"


# ---------------------------------------------------------------------------
# Evidence pack
# ---------------------------------------------------------------------------

@dataclass
class EvidencePack:
    text_chunks: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    page_images: list[str] = field(default_factory=list)
    source_pages: list[int] = field(default_factory=list)
    section_titles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "text_chunks": self.text_chunks,
            "tables": self.tables,
            "page_images": self.page_images,
            "source_pages": self.source_pages,
            "section_titles": self.section_titles,
        }


# ---------------------------------------------------------------------------
# Knowledge store
# ---------------------------------------------------------------------------

class KnowledgeStore:
    def __init__(self):
        self._kb: dict | None = None
        self._collection = None
        self._item_index: dict[str, dict] = {}  # id → item
        self._section_index: dict[str, dict] = {}  # id → section

    def load(self):
        """Load knowledge base and ChromaDB collection."""
        if not KNOWLEDGE_BASE_PATH.exists():
            raise FileNotFoundError(
                f"Knowledge base not found at {KNOWLEDGE_BASE_PATH}. "
                "Run scripts/extract_knowledge.py first."
            )

        with open(KNOWLEDGE_BASE_PATH) as f:
            self._kb = json.load(f)

        # Build item and section indexes
        for section in self._kb["sections"]:
            self._section_index[section["id"]] = section
            for item in section["items"]:
                self._item_index[item["id"]] = {**item, "_section": section}

        # Load ChromaDB
        if EMBEDDINGS_DIR.exists():
            try:
                client = chromadb.PersistentClient(path=str(EMBEDDINGS_DIR))
                ef = embedding_functions.DefaultEmbeddingFunction()
                self._collection = client.get_collection(
                    name=COLLECTION_NAME, embedding_function=ef
                )
                print(f"  ChromaDB loaded: {self._collection.count()} embeddings")
            except Exception as e:
                print(f"  WARNING: ChromaDB unavailable ({e}), falling back to keyword search")
                self._collection = None
        else:
            print("  WARNING: No embeddings found. Run scripts/build_embeddings.py.")

    def search(
        self,
        query: str,
        process_filter: str | None = None,
        topic_filter: str | None = None,
        top_k: int = 8,
    ) -> EvidencePack:
        """Hybrid search: semantic + keyword, with optional metadata filters."""
        seen_ids: set[str] = set()
        candidates: list[dict] = []

        # 1. Semantic search
        if self._collection:
            where_filter = self._build_chroma_filter(process_filter, topic_filter)
            try:
                kwargs: dict = {"query_texts": [query], "n_results": min(top_k * 2, self._collection.count())}
                if where_filter:
                    kwargs["where"] = where_filter
                results = self._collection.query(**kwargs)
                for i, doc_id in enumerate(results["ids"][0]):
                    item = self._item_index.get(doc_id)
                    if item and doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        candidates.append(
                            {**item, "_score": 1.0 - (results["distances"][0][i] if results.get("distances") else 0)}
                        )
            except Exception as e:
                print(f"  Semantic search error: {e}")

        # 2. Keyword search (always runs, boosts matching results)
        keyword_hits = self._keyword_search(query, process_filter, topic_filter)
        for item in keyword_hits:
            iid = item["id"]
            if iid in seen_ids:
                # Boost existing candidate
                for c in candidates:
                    if c["id"] == iid:
                        c["_score"] = c.get("_score", 0) + 0.3
                        break
            else:
                seen_ids.add(iid)
                candidates.append({**item, "_score": 0.3})

        # 3. Sort by score, limit
        candidates.sort(key=lambda x: x.get("_score", 0), reverse=True)
        top = candidates[:top_k]

        return self._build_evidence_pack(top)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_chroma_filter(
        self, process_filter: str | None, topic_filter: str | None
    ) -> dict | None:
        conditions = []
        if process_filter:
            conditions.append(
                {"$or": [{"process": {"$eq": process_filter}}, {"process": {"$eq": "all"}}]}
            )
        if topic_filter:
            conditions.append({"topics": {"$contains": topic_filter}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def _keyword_search(
        self,
        query: str,
        process_filter: str | None = None,
        topic_filter: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Simple keyword matching across all items."""
        terms = re.findall(r"\w+", query.lower())
        hits: list[tuple[int, dict]] = []

        for item_id, item in self._item_index.items():
            section = item.get("_section", {})

            # Apply filters
            if process_filter:
                proc = item.get("related_process") or section.get("process", "all") or "all"
                if proc not in (process_filter, "all"):
                    continue
            if topic_filter:
                topics = item.get("topics", []) or section.get("topics", [])
                if topic_filter not in topics:
                    continue

            # Score by term matches
            content = item.get("content", "")
            if isinstance(content, dict):
                text = json.dumps(content).lower()
            else:
                text = str(content).lower()

            desc = item.get("description", "").lower()
            labels = " ".join(item.get("labels", [])).lower()
            haystack = f"{text} {desc} {labels} {section.get('title', '').lower()}"

            score = sum(1 for t in terms if t in haystack)
            if score > 0:
                hits.append((score, item))

        hits.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in hits[:limit]]

    def _build_evidence_pack(self, items: list[dict]) -> EvidencePack:
        text_chunks: list[dict] = []
        tables: list[dict] = []
        visual_pages: set[int] = set()
        source_pages: set[int] = set()
        section_titles: set[str] = set()

        for item in items:
            section = item.get("_section", {})
            page = item.get("page", 0)
            source_pages.add(page)
            if section.get("title"):
                section_titles.add(section["title"])

            itype = item.get("type", "text")

            if itype == "table":
                content = item.get("content", {})
                if isinstance(content, dict):
                    tables.append(
                        {
                            "title": content.get("title", ""),
                            "headers": content.get("headers", []),
                            "rows": content.get("rows", []),
                            "page": page,
                            "section": section.get("title", ""),
                        }
                    )
            elif itype == "visual":
                visual_pages.add(page)
                text_chunks.append(
                    {
                        "content": item.get("description", ""),
                        "page": page,
                        "section": section.get("title", ""),
                        "region": item.get("region", "diagram"),
                        "type": "visual",
                    }
                )
            else:
                content = item.get("content", "")
                text_chunks.append(
                    {
                        "content": str(content) if not isinstance(content, str) else content,
                        "page": page,
                        "section": section.get("title", ""),
                        "region": item.get("region", ""),
                        "type": itype,
                    }
                )

        return EvidencePack(
            text_chunks=text_chunks,
            tables=tables,
            page_images=[f"page_images/page_{p}.png" for p in sorted(visual_pages)],
            source_pages=sorted(source_pages),
            section_titles=list(section_titles),
        )


# Singleton
knowledge_store = KnowledgeStore()
