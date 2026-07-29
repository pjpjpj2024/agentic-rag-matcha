# Agentic RAG for Matcha Knowledge Base

> AI Engineer Programming Test - Agentic AI with Retrieval-Augmented Generation (RAG)

A lightweight Retrieval-Augmented Generation (RAG) system built using the OpenAI Agents SDK with a two-agent architecture. A Data Retriever agent searches a local knowledge base with a custom keyword-based tool and hands the results off to a Report Generator agent, which synthesizes a polished final answer.

The system uses a custom keyword-based Top-K retrieval algorithm, a local text-based knowledge base, and Ollama (Qwen3:8B) as the LLM, so the entire project runs locally without paid API access.

---

## Project Objectives

* Multi-agent AI using the OpenAI Agents SDK
* Retrieval-Augmented Generation (RAG)
* A custom retrieval tool
* Agent orchestration using the Handoff pattern
* Modular Python project structure
* Local LLM inference using Ollama

---

## System Architecture

```text
                        User
                          |
                          v
                Data Retriever Agent
                          |
          search_knowledge() Tool
                          |
                 Top 3 Relevant Chunks
                          |
                     HANDOFF
                          |
                          v
               Report Generator Agent
                          |
                          v
                  Final Polished Answer
```

---

## Agent Responsibilities

### Agent 1 - Data Retriever
Receives the user's question, calls the `search_knowledge` tool, ranks knowledge base chunks by keyword relevance, and hands the Top-3 snippets to the Report Generator. It never answers the question itself.

### Agent 2 - Report Generator
Receives the retrieved snippets, removes redundancy, and synthesizes a coherent, well-structured answer. It has no retrieval capability of its own.

---

## Retrieval Method

A keyword-based Top-K retriever is used, as permitted by the assignment. No embeddings or vector databases are involved.

Pipeline:

1. Read `knowledge_base.txt` and split it into its 8 labeled sections.
2. Normalize the query: lowercase, strip punctuation, split into words, remove stop words.
3. For each section, score keyword overlap between the query and that section's title and body.
4. Dampen the contribution of words that appear across most sections (e.g. "tea", "matcha"), so common domain words don't let a long, repetitive section outrank the section that's actually relevant.
5. Sort sections by score and return the Top 3.

### Scoring

| Condition                        | Weight |
| --------------------------------- | -----: |
| Keyword found in section title    |     +3 |
| Keyword found in section body     |     +1 |
| Exact phrase match                |     +1 |

Term frequency is capped at 2 occurrences per word, and each word's contribution is scaled by how many of the 8 sections it appears in, so a word unique to one section counts far more than a word found throughout the knowledge base.

---

## Repository Structure

```text
agentic-rag-matcha/
|
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
|
├── main.py
|
├── agent_defs/
│   ├── retriever.py
│   ├── report_generator.py
│   └── prompts.py
|
├── tools/
│   └── search_tool.py
|
├── knowledge_base/
│   └── knowledge_base.txt
|
└── outputs/
    ├── answers_png/
    ├── answers_txt/
    └── debug_logs/
```

Naming note: the folder holding the two agent definitions is called `agent_defs/`, not `agents/`. The OpenAI Agents SDK's own installed package is also named `agents`, so a local folder with that same name shadows the SDK on `sys.path` and breaks every `from agents import ...` line the moment you run `python main.py` from the project root. Renaming the local folder avoids that collision.

---

## Technologies

| Component      | Technology                     |
| -------------- | ------------------------------ |
| Framework      | OpenAI Agents SDK              |
| LLM            | Ollama                         |
| Model          | Qwen3:8B                       |
| Language       | Python 3.12                    |
| Retrieval      | Keyword Search (Top-K Ranking) |
| Knowledge Base | Local TXT file (8 sections)    |

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd agentic-rag-matcha
```

### 2. Create a virtual environment

Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS / Linux
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Ollama and pull the model

```bash
ollama pull qwen3:8b
ollama serve
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and adjust if needed.

### 6. Run the project

```bash
python main.py
```

---

## Running Against Ollama: Why the Client Setup Matters

Ollama's OpenAI-compatible server only implements the older `/v1/chat/completions` endpoint. The OpenAI Agents SDK defaults to the newer `/v1/responses` endpoint and, when no model is explicitly set on an Agent, falls back to an OpenAI-only model name that Ollama has never heard of, so a naive setup fails with a 404 model-not-found error the moment the Report Generator tries to run.

`main.py` avoids this in `configure_ollama_client()` by:

1. Calling `set_default_openai_api("chat_completions")` so the SDK talks to `/v1/chat/completions` instead of `/v1/responses`.
2. Building an explicit `OpenAIChatCompletionsModel(model=OLLAMA_MODEL, openai_client=client)` bound to the Ollama client and model name, and passing it into both agents (`model=model` in `build_retriever_agent` and `build_report_generator_agent`) instead of relying on the SDK's default model.

---

## Output Files

Each demo query produces three outputs:

* PNG (`outputs/answers_png/`) - user query and final answer, clean and screenshot-ready.
* TXT (`outputs/answers_txt/`) - plain-text query and final answer.
* Debug log (`outputs/debug_logs/`) - full trace: retrieved chunks, scores, matched keywords, generator output, and an execution summary. The console prints the same content live.

---

## Demo Queries

1. `How was matcha introduced to Japan?` - tests the History section.
2. `Why is matcha more expensive than ordinary green tea?` - tests Production and Cultivation.
3. `How is matcha traditionally prepared during the Japanese tea ceremony?` - tests Tea Ceremony and History.

---

## Design Decisions

Why OpenAI Agents SDK? It provides a clean abstraction for agents, tools, and handoffs. For two collaborating agents, it's simpler than a full graph-based framework while still clearly demonstrating orchestration.

Why Ollama? Enables local, offline inference with an open-source model, no paid API access required.

Why keyword search? The assignment explicitly allows it. It's simple, deterministic, and easy to explain, without introducing vector infrastructure the task doesn't need.

Why Handoff, not agent-as-tool? It matches the assignment's wording more directly: the Retriever finishes its job, then hands off to the Generator, rather than being called as a subroutine.

---

## Future Improvements

* Semantic search using embeddings
* Vector databases (FAISS, Chroma, Pinecone)
* Hybrid retrieval and metadata filtering
* Conversation memory across turns
* Multi-document / PDF ingestion

---

## Knowledge Base and Sources

The knowledge base was rewritten in original language based on facts from the two reference articles below, then split into 8 sections (History, Cultivation, Production, Grades, Health Benefits, Tea Ceremony, Zen Buddhism, Preparation). No sentences were copied verbatim from the source articles. `knowledge_base.txt` intentionally excludes citations, URLs, and footnotes so retrieval content stays clean; full source attribution lives here in the README instead.

### References (APA)

McNamee, G. L. (2025, February 21). *Matcha*. Encyclopaedia Britannica. https://www.britannica.com/topic/matcha

Britannica Editors. (2022, February 19). *Tea ceremony*. Encyclopaedia Britannica. https://www.britannica.com/topic/tea-ceremony

---

## Academic Integrity

This repository was created for an AI engineering programming assessment. The knowledge base was rewritten and summarized from publicly available reference materials to demonstrate Retrieval-Augmented Generation; the original sources are acknowledged above. No sentences were copied verbatim from either source; both were read in full and then re-explained from scratch.

---

## Author

Pichsinee Jarusawee
Mahidol University - Faculty of Information and Communication Technology (ICT)
