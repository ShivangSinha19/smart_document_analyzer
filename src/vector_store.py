from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from src.text_splitter import TextChunk


@dataclass(frozen=True)
class SearchResult:
    chunk: TextChunk
    score: float


class InMemoryVectorStore:
    """Small local vector index for internship prototypes and demos."""

    def __init__(self) -> None:
        self._chunks: list[TextChunk] = []
        self._idf: dict[str, float] = {}
        self._vectors: list[dict[str, float]] = []

    @property
    def chunks(self) -> list[TextChunk]:
        return self._chunks

    def build(self, chunks: list[TextChunk]) -> None:
        if not chunks:
            raise ValueError("Cannot build an index without text chunks")

        self._chunks = chunks
        tokenized_chunks = [_tokenize(chunk.text) for chunk in chunks]
        document_frequency: dict[str, int] = defaultdict(int)

        for tokens in tokenized_chunks:
            for token in set(tokens):
                document_frequency[token] += 1

        total_documents = len(tokenized_chunks)
        self._idf = {
            token: math.log((1 + total_documents) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        self._vectors = [self._to_tfidf_vector(tokens) for tokens in tokenized_chunks]

    def search(self, query: str, top_k: int = 4) -> list[SearchResult]:
        if not self._vectors:
            raise RuntimeError("Vector store has not been built yet")

        query_vector = self._to_tfidf_vector(_tokenize(query))
        similarities = [
            _cosine_similarity(query_vector, document_vector)
            for document_vector in self._vectors
        ]

        ranked = sorted(enumerate(similarities), key=lambda item: item[1], reverse=True)[:top_k]
        return [
            SearchResult(chunk=self._chunks[index], score=score)
            for index, score in ranked
            if score > 0
        ]

    def _to_tfidf_vector(self, tokens: list[str]) -> dict[str, float]:
        counts = Counter(tokens)
        if not counts:
            return {}

        total_terms = sum(counts.values())
        vector = {}
        for token, count in counts.items():
            if token in self._idf:
                term_frequency = count / total_terms
                vector[token] = term_frequency * self._idf[token]
        return vector


def _tokenize(text: str) -> list[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "was",
        "were",
        "with",
    }
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return [token for token in tokens if token not in stop_words and len(token) > 2]


def _cosine_similarity(first: dict[str, float], second: dict[str, float]) -> float:
    if not first or not second:
        return 0.0

    shared_terms = set(first).intersection(second)
    dot_product = sum(first[token] * second[token] for token in shared_terms)
    first_norm = math.sqrt(sum(value * value for value in first.values()))
    second_norm = math.sqrt(sum(value * value for value in second.values()))
    if first_norm == 0 or second_norm == 0:
        return 0.0

    return dot_product / (first_norm * second_norm)
