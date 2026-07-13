"""
=============================================================================
Stage 1: Document Ingestion & Text Segmentation
=============================================================================

PURPOSE
-------
Transforms raw enterprise documents (PDFs, plain text, Markdown) into a structured
corpus of overlapping text chunks ready for embedding and semantic search.

ROLE IN THE RAG PIPELINE
------------------------
  Input:  data/raw/*.pdf, *.txt, *.md
  Output: data/processed/chunks.json

  Each chunk is the atomic retrieval unit for Stages 2–5. Metadata attached here
  (source_file, doc_type, section_hint) flows through to API source citations.

PROCESSING PIPELINE (per document):
  1. extract_text_from_file()  — pdfplumber (PDF) or UTF-8 read (txt/md)
  2. clean_text()              — strip headers/footers via utils.py
  3. detect_document_type()    — heuristic SOP/policy/compliance classification
  4. split_into_sections()     — heading-aware logical segmentation
  5. chunk_text()              — tiktoken token windows with overlap
  6. Save all chunks → chunks.json

INTERVIEW TALKING POINTS
------------------------
1. **Two-level segmentation:** Section split (semantic boundaries) THEN token
   chunking (embedding model limits) — better than naive fixed-character splits.
2. **tiktoken cl100k_base:** Token-accurate chunking aligned with GPT tokenizer
   family; chunk_size=512 in settings.yaml means real LLM context units.
3. **Overlap (64 tokens):** Prevents sentences at chunk boundaries from being
   split across chunks with no retrieval hit — classic RAG engineering detail.
4. **Heading heuristics:** ALL-CAPS lines, SOP/SYMPTOM prefixes, numbered sections
   (1. PASSWORD REQUIREMENTS) — tuned for enterprise SOP/policy layout.
5. **chunk_id format:** {filename_stem}__{index:04d} — stable, human-readable IDs
   for ChromaDB and debugging.
6. **min_chunk_chars filter:** Drops tiny fragments that add noise without information.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pdfplumber
import tiktoken

from src.utils import (
    clean_text,
    detect_document_type,
    load_config,
    resolve_path,
    save_json,
    setup_logging,
)

logger = setup_logging("ingest")


# -----------------------------------------------------------------------------
# Data model — one searchable document chunk
# -----------------------------------------------------------------------------
@dataclass
class DocumentChunk:
    """
    One searchable piece of a document — the atomic unit of the RAG index.

    Serialized to chunks.json, then embedded in Stage 2, retrieved in Stage 3.
    """
    chunk_id: str        # unique ID, e.g. "corporate_security_policy__0003"
    source_file: str     # original filename for citation
    doc_type: str        # SOP, policy, compliance, etc. (from detect_document_type)
    section_hint: str    # heading this chunk came from (for UI context)
    text: str            # chunk body sent to embedding model
    token_count: int     # tiktoken count (monitoring / context budgeting)
    chunk_index: int     # sequential position within source file


# -----------------------------------------------------------------------------
# Text extraction — format-specific readers
# -----------------------------------------------------------------------------
def extract_text_from_file(path: Path) -> str:
    """
    Read raw text from a PDF, .txt, or .md file.

    PDFs: pdfplumber page-by-page extraction (handles layout better than PyPDF2).
    Text: direct UTF-8 read with errors='ignore' for robustness.

    Raises ValueError for unsupported extensions.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
        return "\n\n".join(pages)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type: {path.suffix}")


# -----------------------------------------------------------------------------
# Section splitting — heading-aware logical segmentation
# -----------------------------------------------------------------------------
def split_into_sections(text: str) -> list[tuple[str, str]]:
    """
    Split document text into logical sections based on heading heuristics.

    A line is treated as a heading if it is:
      - ALL CAPS and short (< 80 chars)
      - Starts with SOP, SYMPTOM, PHASE, CAUSE
      - A numbered heading like "1. PASSWORD REQUIREMENTS"

    Returns list of (heading, section_text) pairs.
    Interview: preserves policy structure so chunks inherit meaningful section_hint.
    """
    blocks = [block.strip() for block in text.split("\n\n") if block.strip()]
    sections: list[tuple[str, str]] = []
    current_heading = "general"
    buffer: list[str] = []

    for block in blocks:
        first_line = block.split("\n", 1)[0].strip()
        is_heading = (
            len(first_line) < 80
            and (
                first_line.isupper()
                or first_line.startswith(("SOP", "SYMPTOM", "PHASE", "CAUSE"))
                or bool(__import__("re").match(r"^\d+\.\s+[A-Z]", first_line))
            )
        )
        if is_heading and buffer:
            sections.append((current_heading, "\n\n".join(buffer)))
            buffer = [block]
            current_heading = first_line[:60]
        else:
            if is_heading and not buffer:
                current_heading = first_line[:60]
            buffer.append(block)

    if buffer:
        sections.append((current_heading, "\n\n".join(buffer)))
    return sections or [("general", text)]


# -----------------------------------------------------------------------------
# Token chunking — overlapping windows via tiktoken
# -----------------------------------------------------------------------------
def chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_chars: int,
    encoding_name: str = "cl100k_base",
) -> list[str]:
    """
    Split a section into overlapping token-sized chunks.

    Uses tiktoken (GPT-family tokenizer) for accurate token counting.
    Overlap ensures sentences at chunk boundaries appear in multiple chunks.

    Example with chunk_size=512, overlap=64:
      Chunk 1: tokens [0, 512)
      Chunk 2: tokens [448, 960)   — 64-token overlap with chunk 1

    Chunks shorter than min_chunk_chars are discarded (noise reduction).
    """
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    if not tokens:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        piece = enc.decode(tokens[start:end]).strip()
        if len(piece) >= min_chunk_chars:
            chunks.append(piece)
        if end >= len(tokens):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


# -----------------------------------------------------------------------------
# ingest_corpus — process all documents in raw_dir
# -----------------------------------------------------------------------------
def ingest_corpus(raw_dir: Path, processed_dir: Path) -> list[DocumentChunk]:
    """
    Process every document in raw_dir and persist chunks to processed_dir/chunks.json.

    Raises FileNotFoundError if raw_dir contains no supported documents.

    Returns the full list of DocumentChunk objects (also saved to disk).
    """
    config = load_config()
    chunk_cfg = config["chunking"]
    all_chunks: list[DocumentChunk] = []

    files = sorted(
        list(raw_dir.glob("*.pdf"))
        + list(raw_dir.glob("*.txt"))
        + list(raw_dir.glob("*.md"))
    )
    if not files:
        raise FileNotFoundError(f"No documents found in {raw_dir}")

    logger.info("Found %d source documents", len(files))

    for file_path in files:
        raw_text = extract_text_from_file(file_path)
        cleaned = clean_text(raw_text)
        doc_type = detect_document_type(file_path.name, cleaned)
        sections = split_into_sections(cleaned)

        chunk_index = 0
        for section_hint, section_text in sections:
            pieces = chunk_text(
                section_text,
                chunk_size=chunk_cfg["chunk_size"],
                chunk_overlap=chunk_cfg["chunk_overlap"],
                min_chunk_chars=chunk_cfg["min_chunk_chars"],
            )
            for piece in pieces:
                enc = tiktoken.get_encoding("cl100k_base")
                token_count = len(enc.encode(piece))
                chunk_id = f"{file_path.stem}__{chunk_index:04d}"
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source_file=file_path.name,
                        doc_type=doc_type,
                        section_hint=section_hint,
                        text=piece,
                        token_count=token_count,
                        chunk_index=chunk_index,
                    )
                )
                chunk_index += 1

        logger.info(
            "Processed %s | type=%s | chunks=%d",
            file_path.name,
            doc_type,
            chunk_index,
        )

    payload = [asdict(chunk) for chunk in all_chunks]
    save_json(processed_dir / "chunks.json", payload)
    logger.info("Saved %d chunks to %s", len(all_chunks), processed_dir / "chunks.json")
    return all_chunks


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: python scripts/run_ingest.py [--raw-dir PATH]"""
    parser = argparse.ArgumentParser(description="Stage 1: ingest and chunk documents")
    parser.add_argument("--raw-dir", default=None, help="Override raw document directory")
    args = parser.parse_args()

    config = load_config()
    raw_dir = Path(args.raw_dir) if args.raw_dir else resolve_path(config["paths"]["raw_dir"])
    processed_dir = resolve_path(config["paths"]["processed_dir"])
    ingest_corpus(raw_dir, processed_dir)


if __name__ == "__main__":
    main()
