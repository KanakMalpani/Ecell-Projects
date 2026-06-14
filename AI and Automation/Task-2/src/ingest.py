"""Stage 1: Document ingestion and text segmentation."""

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


@dataclass
class DocumentChunk:
    chunk_id: str
    source_file: str
    doc_type: str
    section_hint: str
    text: str
    token_count: int
    chunk_index: int


def extract_text_from_file(path: Path) -> str:
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


def split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split on blank lines / numbered headings to preserve structure."""
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


def chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_chars: int,
    encoding_name: str = "cl100k_base",
) -> list[str]:
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


def ingest_corpus(raw_dir: Path, processed_dir: Path) -> list[DocumentChunk]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 1: ingest and chunk documents")
    parser.add_argument("--raw-dir", default=None, help="Override raw document directory")
    args = parser.parse_args()

    config = load_config()
    raw_dir = Path(args.raw_dir) if args.raw_dir else resolve_path(config["paths"]["raw_dir"])
    processed_dir = resolve_path(config["paths"]["processed_dir"])
    ingest_corpus(raw_dir, processed_dir)


if __name__ == "__main__":
    main()
