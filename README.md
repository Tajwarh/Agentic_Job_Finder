# Agentic Job Finder
# Team Members:
# Asim Upreti
# Tajwar-Ul Hoque

**Agentic Job Finder** is an autonomous, multi-agent AI system that searches real-world job postings via the Adzuna API and uses Google Gemini (via LangChain) to evaluate, critique, and match candidates' skills against live job opportunities.

The project demonstrates all five core **Agentic AI Design Patterns**:
1. **Prompt Chaining**
2. **Routing**
3. **Parallelization (Parallel Tool Calling)**
4. **Reflection (Critic & Refinement)**
5. **Tool Use (LangChain Tool Calling)**

---

## Workflow Overview

1. **User Prompt**: The user enters a single freeform natural-language request (e.g., *"Find and match Senior Business Analyst jobs in Texas for Python and SQL"*).
2. **Routing & Parameter Extraction**: A LangChain routing agent extracts structured parameters (`roles`, `location`, `skills`) and identifies the user's intent (`handler_match_jobs`, `handler_list_jobs`, or `handler_resume_creator`).
3. **Tool Calling & Parallel Search**: For job searches, an agent bound with the `search_jobs` tool autonomously generates tool calls and executes them concurrently in parallel across threads.
4. **Deduplication**: Results are de-duplicated by title, company, and location.
5. **Prompt Chaining Analysis**:
   - **Step 1**: Extracts hard and soft requirements, responsibilities, and qualifications from the raw posting.
   - **Step 2**: Evaluates candidate fit, producing an initial match score, matching skills, missing skills, and explanation.
6. **Reflection & Self-Correction**: A reflection critic audits the match analysis to prevent hallucinated candidate skills or unsupported claims, refining the analysis if inconsistencies are found before presenting the final result.

---

## Agentic AI Design Patterns

### 1. Prompt Chaining
**Implemented** using LangChain LCEL in [`agents/job_analyzer.py`](agents/job_analyzer.py).

The analysis workflow breaks complex evaluation into a sequential two-step pipeline:
- **Prompt 1 (Requirements Extraction)**: Analyzes raw job descriptions and extracts required/preferred skills and key responsibilities via `requirements_prompt | llm | StrOutputParser()`.
- **Prompt 2 (Candidate Matching)**: Compares the extracted requirements against candidate skills to generate an evidence-grounded score (0–100) and gap analysis via `matching_prompt | llm | StrOutputParser()`.

```text
Raw Job Description
       ↓
[Prompt 1: Extract Requirements]
       ↓
Extracted Job Requirements
       ↓
[Prompt 2: Candidate Match Evaluation]
       ↓
Initial Match Analysis
```

### 2. Routing
**Implemented** using LangChain Structured Outputs in [`agents/router.py`](agents/router.py).

The router inspects natural language prompts and classifies intent into one of three specialized handlers using `router_prompt | llm.with_structured_output(JobRequest)`:
- `handler_match_jobs`: Full end-to-end pipeline (search + prompt chaining + reflection).
- `handler_list_jobs`: Fast search and clean job listing without deep matching.
- `handler_resume_creator`: Generates a targeted resume draft and ATS keyword optimization plan.

### 3. Parallelization
**Implemented** via **Parallel Tool Calling** in [`agents/search_agent.py`](agents/search_agent.py).

When queries involve multiple roles (e.g., *"Business Analyst and Data Scientist"*) or multiple locations, the LLM emits multiple tool calls simultaneously. The search agent executes these tool calls concurrently in parallel using Python's `concurrent.futures.ThreadPoolExecutor`, significantly reducing latency.

### 4. Reflection
**Implemented** via a **Critic & Refinement Loop** in [`agents/reflection_agent.py`](agents/reflection_agent.py).

After an initial match analysis is generated, the Reflection Agent acts as an evaluator:
1. **Critique (`reflect_on_analysis`)**: Checks whether the analysis invented candidate skills, asserted unsupported missing requirements, or produced an inconsistent match score. Decides either `DECISION: APPROVE` or `DECISION: REVISE` with rationale.
2. **Refinement (`refine_analysis`)**: If revision is required, a second pass regenerates the analysis correcting all flagged inaccuracies.
3. **Approval**: If approved, the initial analysis is confirmed and displayed.

### 5. Tool Use
**Implemented** with LangChain `@tool` in [`tools/job_search.py`](tools/job_search.py).

The `search_jobs` tool wraps the real-world Adzuna Job Search API. The LLM is equipped with this tool (`llm.bind_tools([search_jobs])`), interprets query requirements, formulates arguments, and executes live queries.

---

## Project Structure

```text
Agentic_Job_Finder/
├── agents/
│   ├── job_analyzer.py      # Prompt Chaining (Step 1 requirements & Step 2 matching)
│   ├── reflection_agent.py  # Reflection (Critic evaluation & Refinement loop)
│   ├── router.py            # Intent classification & parameter extraction
│   └── search_agent.py      # Tool Use & Parallel Tool Calling agent
├── tools/
│   └── job_search.py        # LangChain @tool wrapping the Adzuna API
├── .env.example             # Environment variable template
├── .gitignore
├── config.py                # Centralized prompts and model settings
├── main.py                  # CLI entry point and handler dispatching
├── README.md                # Project documentation
├── report.md                # Detailed technical report on design patterns
├── requirements.txt         # Project dependencies
└── utils.py                 # Centralized deduplication utilities
```

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+ (tested with Python 3.11 - 3.14)
- Google Gemini API key ([Google AI Studio](https://aistudio.google.com/))
- Adzuna API credentials ([Adzuna Developer Portal](https://developer.adzuna.com/))

### 2. Environment Setup

Clone or open the project folder, then create and activate a virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

Create a `.env` file in the project root:

```text
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GEMINI_API_KEY=your_gemini_api_key
```

*(Optional: configure `GEMINI_MODEL=gemini-2.0-flash` or `gemini-3.6-flash` in `.env` if desired).*

---

## How to Run

Launch the application:

```bash
python main.py
```

### Example Usage Scenarios

#### Scenario A: Full Job Match (Routing + Parallel Tool Calling + Prompt Chaining + Reflection)
```text
Enter your request: Find and match Data Analyst and Business Analyst jobs in Texas for Python, SQL, Tableau
```
- **Routing**: Detects `handler_match_jobs`, `roles=['Data Analyst', 'Business Analyst']`, `location=['Texas']`, `skills=['Python', 'SQL', 'Tableau']`.
- **Parallel Tool Calling**: Launches 2 concurrent calls to `search_jobs` simultaneously.
- **Prompt Chaining**: Extracts requirements and evaluates skills for each job.
- **Reflection**: Evaluates the analysis for accuracy and applies revisions if needed.

#### Scenario B: Quick Job Listing (Tool Use)
```text
Enter your request: List remote Software Engineer jobs
```
- **Routing**: Detects `handler_list_jobs`.
- **Tool Use**: Invokes `search_jobs` and prints structured job previews with descriptions and URLs.

#### Scenario C: Tailored Resume Creation (Routing + Generation)
```text
Enter your request: Build a resume for a Machine Learning Engineer with skills Python, PyTorch, Docker
```
- **Routing**: Detects `handler_resume_creator`.
- **Generation**: Produces a professional summary, core competencies, bullet points, and ATS keywords.