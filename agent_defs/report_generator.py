"""Report Generator agent: synthesizes retrieved chunks into a final answer. This agent has no tools; it only writes a polished final answer based on
    handed snippets by the Data Retriever agent."""

from __future__ import annotations

from agents import Agent, Model

from agent_defs.prompts import REPORT_GENERATOR_INSTRUCTIONS


def build_report_generator_agent(model: Model | str | None = None) -> Agent:
    return Agent(
        name="Report Generator",
        instructions=REPORT_GENERATOR_INSTRUCTIONS,
        tools=[],
        model=model,
    )
