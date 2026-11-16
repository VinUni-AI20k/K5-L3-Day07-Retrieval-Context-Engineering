"""Export the selected Day 6 pgvector strategy as Day 7 chunk JSON."""
import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv

SELECTED_STRATEGY = "C"
EMBEDDING_DIMENSIONS = 1536


def make_chunk(row: tuple[Any, ...]) -> dict[str, Any]:
    chunk_id, document_id, source, page, section, text, metadata, vector_text = row
    embedding = json.loads(vector_text)
    if not isinstance(embedding, list) or len(embedding) != EMBEDDING_DIMENSIONS:
        raise ValueError(f"{chunk_id}: expected a {EMBEDDING_DIMENSIONS}-dimensional saved embedding")
    if not isinstance(metadata, dict):
        raise ValueError(f"{chunk_id}: metadata must be a JSON object")
    metadata = dict(metadata)
    if metadata.get("section") != section:
        raise ValueError(f"{chunk_id}: stored section column does not match metadata.section")
    return {
        "id": chunk_id,
        "text": text,
        "source_id": document_id,
        "source": source,
        "page": page,
        "metadata": metadata,
        "embedding": embedding,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Day 6 strategy C chunks and saved embeddings")
    parser.add_argument("--dotenv", type=Path, help="Day 6 .env path containing DATABASE_URL")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.dotenv:
        load_dotenv(args.dotenv)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing; set it or pass --dotenv for the Day 6 .env file.")

    with psycopg.connect(database_url, connect_timeout=5) as connection:
        rows = connection.execute(
            """
            SELECT chunk_id, document_id, source, page, section, text, metadata, embedding::text
            FROM rag_chunks
            WHERE strategy = %s
            ORDER BY chunk_id
            """,
            (SELECTED_STRATEGY,),
        ).fetchall()
    if not rows:
        raise RuntimeError(f"No Day 6 rows found for selected strategy {SELECTED_STRATEGY}.")

    chunks = [make_chunk(row) for row in rows]
    ids = [chunk["id"] for chunk in chunks]
    if len(ids) != len(set(ids)):
        raise ValueError("Day 6 export contains duplicate chunk IDs.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(chunks, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Exported {len(chunks)} strategy {SELECTED_STRATEGY} chunks to {args.output}")


if __name__ == "__main__":
    main()
