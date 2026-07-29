# Agentic RAG for Matcha Knowledge Base

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

## Output Files

Each demo query produces three outputs:

* PNG (`outputs/answers_png/`) - user query and final answer, clean and screenshot-ready.
* TXT (`outputs/answers_txt/`) - plain-text query and final answer.
* Debug log (`outputs/debug_logs/`) - full trace: retrieved chunks, scores, matched keywords, generator output, and an execution summary. The console prints the same content live.

---

## Sample User Queries

1. `How was matcha introduced to Japan?` - tests the History section.
2. `Why is matcha more expensive than ordinary green tea?` - tests Production and Cultivation.
3. `How is matcha traditionally prepared during the Japanese tea ceremony?` - tests Tea Ceremony and History.

---


## Knowledge Base and Sources

The knowledge base was rewritten in original language by AI based on facts from the two reference articles below, then split into 8 sections (History, Cultivation, Production, Grades, Health Benefits, Tea Ceremony, Zen Buddhism, Preparation). `knowledge_base.txt` intentionally excludes citations, URLs, and footnotes so retrieval content stays clean; full source attribution lives here in the README instead.

### References (APA)

McNamee, G. L. (2025, February 21). *Matcha*. Encyclopaedia Britannica. https://www.britannica.com/topic/matcha

Britannica Editors. (2022, February 19). *Tea ceremony*. Encyclopaedia Britannica. https://www.britannica.com/topic/tea-ceremony

---



## Author

Pichsinee Jarusawee

