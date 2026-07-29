"""Data Retriever agent: retrieves Top-K knowledge base chunks for a query."""

from __future__ import annotations

from agents import Agent, Model, function_tool

from agent_defs.prompts import RETRIEVER_INSTRUCTIONS
from tools.search_tool import search_knowledge


@function_tool
def search_knowledge_tool(query: str) -> str:
    """Search the local matcha knowledge base and return the top 3 relevant chunks. """

    results = search_knowledge(query, top_k=3)

    if not results:
        return "No relevant knowledge base sections were found for this query."

    formatted = []
    for rank, scored in enumerate(results, start=1):
        formatted.append(
            f"[Chunk {rank}] Title: {scored.chunk.title} "
            f"(score: {scored.score}, matched keywords: {', '.join(scored.matched_keywords) or 'none'})\n"
            f"{scored.chunk.body}"
        )

    return "\n\n".join(formatted)


def build_retriever_agent(report_generator: Agent, model: Model | str | None = None) -> Agent:
    """Construct the Data Retriever agent with a handoff to the Report Generator."""
    
    return Agent(
        name="Data Retriever",
        instructions=RETRIEVER_INSTRUCTIONS,
        tools=[search_knowledge_tool],
        handoffs=[report_generator],
        model=model,
    )
