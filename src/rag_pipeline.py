from __future__ import annotations

from dataclasses import dataclass

from src.document_loader import LoadedDocument
from src.llm import Answer, generate_answer
from src.text_splitter import TextChunk, chunk_text
from src.vector_store import InMemoryVectorStore, SearchResult


@dataclass(frozen=True)
class IndexSummary:
    document_count: int
    chunk_count: int


@dataclass(frozen=True)
class RagResponse:
    answer: Answer
    sources: list[SearchResult]


class RagPipeline:
    def __init__(self) -> None:
        self._store = InMemoryVectorStore()
        self._summary = IndexSummary(document_count=0, chunk_count=0)

    @property
    def summary(self) -> IndexSummary:
        return self._summary

    def build_index(self, documents: list[LoadedDocument], chunk_size: int, overlap: int) -> IndexSummary:
        chunks: list[TextChunk] = []
        for document in documents:
            chunks.extend(chunk_text(document.filename, document.text, chunk_size=chunk_size, overlap=overlap))

        self._store.build(chunks)
        self._summary = IndexSummary(document_count=len(documents), chunk_count=len(chunks))
        return self._summary

    def ask(self, question: str, top_k: int) -> RagResponse:
        results = self._store.search(question, top_k=top_k)
        answer = generate_answer(question, results)
        return RagResponse(answer=answer, sources=results)

