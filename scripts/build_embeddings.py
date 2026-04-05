#!/usr/bin/env python3
"""
build_embeddings.py — Build ChromaDB vector store from knowledge_base.json.

Embeds at the item level so each fact, table, and diagram description
gets its own embedding with full metadata for hybrid retrieval.

Run after extract_knowledge.py.
"""

import json
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "backend" / "knowledge" / "knowledge_base.json"
EMBEDDINGS_DIR = PROJECT_ROOT / "backend" / "knowledge" / "embeddings"

COLLECTION_NAME = "vulcan_omnipro_220"


def build_embeddings():
    if not KNOWLEDGE_BASE_PATH.exists():
        print(f"ERROR: {KNOWLEDGE_BASE_PATH} not found. Run extract_knowledge.py first.")
        sys.exit(1)

    with open(KNOWLEDGE_BASE_PATH) as f:
        kb = json.load(f)

    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(EMBEDDINGS_DIR))

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print("  Deleted existing collection")
    except Exception:
        pass

    ef = embedding_functions.DefaultEmbeddingFunction()
    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )

    documents = []
    metadatas = []
    ids = []

    for section in kb["sections"]:
        for item in section["items"]:
            # Build document text
            if isinstance(item.get("content"), dict):
                # Table: embed title + header + row text
                content_dict = item["content"]
                doc_text = content_dict.get("title", "") + " "
                doc_text += " | ".join(content_dict.get("headers", [])) + " "
                for row in content_dict.get("rows", []):
                    doc_text += " | ".join(str(c) for c in row) + " "
            elif item.get("type") == "visual":
                doc_text = item.get("description", "")
                if item.get("labels"):
                    doc_text += " Labels: " + ", ".join(item["labels"])
            else:
                doc_text = str(item.get("content", ""))

            doc_text = doc_text.strip()
            if not doc_text:
                continue

            # Build metadata (ChromaDB requires flat string/int/float/bool values)
            topics = item.get("topics") or section.get("topics", [])
            meta = {
                "page": item.get("page", 0),
                "section": section["id"],
                "section_title": section["title"],
                "type": item.get("type", "text"),
                "process": item.get("related_process") or section.get("process", "all") or "all",
                "topics": ",".join(topics),
                "region": item.get("region", ""),
                "source_type": item.get("source_type", "text"),
            }

            documents.append(doc_text)
            metadatas.append(meta)
            ids.append(item["id"])

    # Upsert in batches
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        collection.add(documents=batch_docs, metadatas=batch_meta, ids=batch_ids)
        print(f"  Embedded items {i + 1}–{min(i + batch_size, len(documents))}")

    print(f"\nCollection '{COLLECTION_NAME}' built with {len(documents)} embeddings.")
    print(f"Stored at: {EMBEDDINGS_DIR}")


if __name__ == "__main__":
    build_embeddings()
