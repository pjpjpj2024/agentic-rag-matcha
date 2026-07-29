"""Custom keyword-based Top-K retrieval tool for the matcha knowledge base.
"""

from __future__ import annotations

import re
import string
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "knowledge_base" / "knowledge_base.txt"

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "on", "at", "to", "for", "with", "from", "by", "as",
    "and", "or", "but", "if", "than", "then", "so", "that", "this",
    "these", "those", "it", "its", "into", "about", "how", "why",
    "what", "when", "where", "who", "does", "do", "did", "can",
    "could", "would", "should", "will", "shall", "has", "have", "had",
}

TITLE_WEIGHT = 3
BODY_WEIGHT = 1
EXACT_PHRASE_WEIGHT = 1
DEFAULT_TOP_K = 3


@dataclass
class Chunk:
    """A single retrievable section of the knowledge base."""

    title: str
    body: str

    @property
    def full_text(self) -> str:
        return f"{self.title}\n{self.body}"


@dataclass
class ScoredChunk:
    """A knowledge base chunk paired with its retrieval score and diagnostics."""

    chunk: Chunk
    score: int
    matched_keywords: list[str]


def normalize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split into words, and remove stop words."""

    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    return [w for w in words if w not in STOP_WORDS and w.strip()]


def load_chunks(path: Path = KNOWLEDGE_BASE_PATH) -> list[Chunk]:
    """Load and parse the knowledge base file into a list of chunks."""

    raw_text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^SECTION\s+\d+\s*$", re.MULTILINE)

    matches = list(pattern.finditer(raw_text))
    chunks: list[Chunk] = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()

        lines = block.splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip()

        chunks.append(Chunk(title=title, body=body))

    return chunks


def compute_document_frequencies(chunks: list[Chunk]) -> dict[str, int]:
    """It counts which words are common across chunks, then makes common words matter less and rare words matter more for scoring."""

    doc_freq: dict[str, int] = {}
    for chunk in chunks:
        unique_words = set(normalize(chunk.full_text))
        for word in unique_words:
            doc_freq[word] = doc_freq.get(word, 0) + 1
    return doc_freq


def score_chunk(
    chunk: Chunk,
    query_words: list[str],
    original_query: str,
    doc_freq: dict[str, int],
    total_chunks: int,
    max_term_frequency: int = 2,
) -> ScoredChunk:
    """It compares the query's words to one chunk, adds up points for matches (title matches worth more, rare words worth more), plus a bonus for an exact phrase match, and returns the chunk's total score.
    
    Scoring logic:
    1. For each query word: weight = (title or body weight) × (how many times it appears, capped at 2) × (how rare that word is across chunks).
    2. Add title-word score + body-word score for every matching query word.
    3. Add a flat bonus if the exact full query phrase appears anywhere in the chunk.
    4. Sum it all up = the chunk's final score.
    
    """

    title_words = normalize(chunk.title)
    body_words = normalize(chunk.body)

    score = 0.0
    matched: list[str] = []

    for word in query_words:
        df = doc_freq.get(word, 1)
        specificity = total_chunks / (df + total_chunks)

        title_hits = min(title_words.count(word), max_term_frequency)
        body_hits = min(body_words.count(word), max_term_frequency)

        if title_hits:
            score += TITLE_WEIGHT * title_hits * specificity
            matched.append(word)
        if body_hits:
            score += BODY_WEIGHT * body_hits * specificity
            if word not in matched:
                matched.append(word)

    if original_query.strip().lower() in chunk.full_text.lower():
        score += EXACT_PHRASE_WEIGHT

    return ScoredChunk(chunk=chunk, score=round(score, 2), matched_keywords=matched)


def search_knowledge(query: str, top_k: int = DEFAULT_TOP_K) -> list[ScoredChunk]:
    """Search the knowledge base and return the top-K most relevant chunks."""
    
    chunks = load_chunks()
    query_words = normalize(query)
    doc_freq = compute_document_frequencies(chunks)

    scored = [
        score_chunk(chunk, query_words, query, doc_freq, total_chunks=len(chunks))
        for chunk in chunks
    ]
    scored.sort(key=lambda sc: sc.score, reverse=True)

    return scored[:top_k]
