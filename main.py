from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from agents import (
    OpenAIChatCompletionsModel,
    Runner,
    set_default_openai_api,
    set_default_openai_client,
    set_tracing_disabled,
)

from agent_defs.report_generator import build_report_generator_agent
from agent_defs.retriever import build_retriever_agent
from tools.search_tool import search_knowledge

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

OUTPUT_ROOT = Path(__file__).resolve().parent / "outputs"
PNG_DIR = OUTPUT_ROOT / "answers_png"
TXT_DIR = OUTPUT_ROOT / "answers_txt"
DEBUG_DIR = OUTPUT_ROOT / "debug_logs"

DEMO_QUERIES = [
    "How was matcha introduced to Japan?",
    "Why is matcha more expensive than ordinary green tea?",
    "How is matcha traditionally prepared during the Japanese tea ceremony?",
]


@dataclass
class RunRecord:
    query: str
    retrieved_chunks: list[str] = field(default_factory=list)
    final_answer: str = ""


def configure_ollama_client() -> OpenAIChatCompletionsModel:
    """Point the Agents SDK at the local Ollama server instead of OpenAI."""

    client = AsyncOpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
    set_default_openai_client(client)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(True)
    return OpenAIChatCompletionsModel(model=OLLAMA_MODEL, openai_client=client)


def slugify(text: str) -> str:
    """filesystem-safe slug for output filenames"""

    keep = [c if c.isalnum() else "_" for c in text.lower()]
    slug = "".join(keep).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug[:60]


def save_txt(record: RunRecord, path: Path) -> None:
    path.write_text(
        f"USER QUERY\n{record.query}\n\nFINAL ANSWER\n{record.final_answer}\n",
        encoding="utf-8",
    )


def save_png(record: RunRecord, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    width, padding = 900, 40
    font = ImageFont.load_default()

    def wrap(text: str, max_chars: int = 100) -> list[str]:
        words = text.split()
        lines, current = [], ""
        for word in words:
            trial = f"{current} {word}".strip()
            if len(trial) > max_chars:
                lines.append(current)
                current = word
            else:
                current = trial
        if current:
            lines.append(current)
        return lines

    query_lines = wrap(f"User Query: {record.query}")
    answer_lines = wrap(record.final_answer)
    total_lines = len(query_lines) + len(answer_lines) + 4
    height = padding * 2 + total_lines * 22

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    y = padding
    for line in query_lines:
        draw.text((padding, y), line, fill="black", font=font)
        y += 22

    y += 20
    draw.text((padding, y), "Final Answer:", fill="black", font=font)
    y += 26

    for line in answer_lines:
        draw.text((padding, y), line, fill="black", font=font)
        y += 22

    img.save(path)


async def run_query(query: str, report_generator, retriever) -> RunRecord:
    record = RunRecord(query=query)

    print(f"USER QUERY\n{query}\n")
    print("Retriever running...")

    scored_chunks = search_knowledge(query, top_k=3)

    for rank, sc in enumerate(scored_chunks, start=1):
        record.retrieved_chunks.append(
            f"[Chunk {rank}] {sc.chunk.title} (score={sc.score}, "
            f"keywords={', '.join(sc.matched_keywords) or 'none'})"
        )

    print("\n".join(record.retrieved_chunks))
    print("\nGenerator running...")

    result = await Runner.run(retriever, query)
    record.final_answer = result.final_output

    return record


def save_debug_log(record: RunRecord, path: Path) -> None:
    lines = [
        "USER QUERY",
        record.query,
        "",
        "RETRIEVER: running search_knowledge()",
        *record.retrieved_chunks,
        "",
        "GENERATOR: running Report Generator agent",
        "",
        "FINAL ANSWER",
        record.final_answer,
        "",
        "Execution Summary",
        "-" * 50,
        f"Retrieved Chunks    : {len(record.retrieved_chunks)}",
        f"Model               : {OLLAMA_MODEL}",
    ]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    print(text)
    print()


async def main() -> None:
    model = configure_ollama_client()

    for d in (PNG_DIR, TXT_DIR, DEBUG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    report_generator = build_report_generator_agent(model)
    retriever = build_retriever_agent(report_generator, model)

    for query in DEMO_QUERIES:
        record = await run_query(query, report_generator, retriever)
        slug = slugify(query)

        save_txt(record, TXT_DIR / f"{slug}.txt")
        save_png(record, PNG_DIR / f"{slug}.png")
        save_debug_log(record, DEBUG_DIR / f"{slug}_debug.txt")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
