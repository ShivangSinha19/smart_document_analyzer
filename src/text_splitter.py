from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    source: str
    text: str


def chunk_text(source: str, text: str, chunk_size: int = 900, overlap: int = 150) -> list[TextChunk]:
    """Split text into overlapping word chunks."""
    words = text.split()
    if not words:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[TextChunk] = []
    start = 0
    index = 1
    step = chunk_size - overlap

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_id = f"{source}-chunk-{index}"
        chunks.append(TextChunk(chunk_id=chunk_id, source=source, text=" ".join(chunk_words)))

        if end == len(words):
            break

        start += step
        index += 1

    return chunks

