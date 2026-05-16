from __future__ import annotations

import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv

from src.vector_store import SearchResult


@dataclass(frozen=True)
class Answer:
    text: str
    mode: str


def generate_answer(question: str, results: list[SearchResult]) -> Answer:
    """Generate an answer with a cloud LLM when configured, otherwise use local extraction."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()

    if api_key and model:
        try:
            return _generate_with_openai(question, results, api_key, model)
        except Exception as exc:
            fallback = _generate_extractive_answer(question, results)
            message = (
                f"{fallback.text}\n\n"
                f"Note: Cloud LLM generation failed, so the app used local extractive mode. Error: {exc}"
            )
            return Answer(text=message, mode="Local extractive fallback")

    return Answer(text=_generate_extractive_answer(question, results).text, mode="Local extractive")


def _generate_with_openai(question: str, results: list[SearchResult], api_key: str, model: str) -> Answer:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    context = _format_context(results)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a smart document analyzer. Answer only from the provided context. "
                    "If the answer is not in the context, say that the document does not contain enough information. "
                    "Mention source chunk IDs when useful."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nContext:\n{context}",
            },
        ],
        temperature=0.2,
    )
    return Answer(text=response.choices[0].message.content or "", mode="Cloud LLM")


def _generate_extractive_answer(question: str, results: list[SearchResult]) -> Answer:
    if not results:
        return Answer(
            text="I could not find relevant information in the uploaded document for this question.",
            mode="Local extractive",
        )

    query_terms = _important_terms(question)
    scored_sentences: list[tuple[float, str, str]] = []

    for result in results:
        sentences = _split_sentences(result.chunk.text)
        for sentence in sentences:
            sentence_terms = _important_terms(sentence)
            overlap = len(query_terms.intersection(sentence_terms))
            score = result.score + overlap
            if overlap > 0 or len(results) == 1:
                scored_sentences.append((score, result.chunk.chunk_id, sentence))

    if not scored_sentences:
        best = results[0]
        return Answer(
            text=(
                "The most relevant passage I found is:\n\n"
                f"{best.chunk.text[:900]}\n\n"
                f"Source: {best.chunk.chunk_id}"
            ),
            mode="Local extractive",
        )

    selected = sorted(scored_sentences, key=lambda item: item[0], reverse=True)[:3]
    answer_lines = [sentence for _, _, sentence in selected]
    source_ids = sorted({chunk_id for _, chunk_id, _ in selected})
    return Answer(
        text=f"{' '.join(answer_lines)}\n\nSources: {', '.join(source_ids)}",
        mode="Local extractive",
    )


def _format_context(results: list[SearchResult]) -> str:
    return "\n\n".join(
        f"[{result.chunk.chunk_id} | {result.chunk.source} | score={result.score:.3f}]\n{result.chunk.text}"
        for result in results
    )


def _important_terms(text: str) -> set[str]:
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
        "how",
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
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "with",
    }
    tokens = re.findall(r"[A-Za-z0-9]+", text.lower())
    return {token for token in tokens if token not in stop_words and len(token) > 2}


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

