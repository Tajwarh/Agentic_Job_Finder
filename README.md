# Agentic Job Finder

Agentic Job Finder is an Agentic AI class project that searches for real job postings and uses AI to evaluate how well a candidate's skills match those jobs.

## Current Workflow

The user enters:

- Job roles
- Location
- Skills

The system then:

1. Searches for real jobs using the Adzuna API.
2. Supports multiple job roles and locations.
3. Removes duplicate job postings.
4. Uses Gemini to extract requirements from each job.
5. Passes the extracted requirements to a second prompt.
6. Compares the requirements with the user's skills.
7. Produces a match score, matching skills, missing skills, and an explanation.

## Agentic AI Design Patterns

The final project demonstrates five Agentic AI design patterns.

### 1. Prompt Chaining

Implemented using LangChain LCEL (LangChain Expression Language).

Prompt 1 extracts important requirements from the job description via `requirements_prompt | llm | StrOutputParser()`.

Prompt 2 receives the extracted requirements and compares them with the candidate's skills via `matching_prompt | llm | StrOutputParser()`.

Flow:

```text
Job Description
      ↓
Prompt 1
Extract Requirements
      ↓
Extracted Requirements
      ↓
Prompt 2
Candidate Matching
      ↓
Match Score + Analysis
```

### 2. Routing

Implemented using LangChain `with_structured_output(JobRequest)`.

The system extracts parameters (`roles`, `location`, `skills`) and detects intent from natural language user prompts via `router_prompt | llm.with_structured_output(JobRequest)`, routing to one of three specialized handlers:
- `handler_match_jobs`: Searches jobs and executes LangChain Prompt Chaining match analysis.
- `handler_list_jobs`: Searches and lists relevant job postings without full match scoring.
- `handler_resume_creator`: Drafts a tailored resume profile with ATS recommendations via LangChain LCEL.

### 3. Parallelization

Implemented via **Parallel Tool Calling**.

When searches across multiple roles or locations are requested, the LLM generates multiple tool calls that are executed concurrently in parallel via `ThreadPoolExecutor`, speeding up retrieval.

### 4. Reflection

To be implemented.

A critic/reflection step will review generated recommendations and identify unsupported or inconsistent results.

### 5. Tool Use

Implemented with LangChain `@tool` (`search_jobs`).

The LLM is bound with external tools (`llm.bind_tools([search_jobs])`), inspects the user query, autonomously selects the tool, formulates arguments, and executes the search against the Adzuna API.

## Current Features

- Real job search using Adzuna
- Multiple job-role search
- Flexible location search
- Related job discovery
- Duplicate job filtering
- Gemini AI integration
- Two-step prompt chaining
- Candidate-job skill matching
- Match scores
- Matching skill identification
- Missing skill identification
- API error handling for temporary server and quota errors

## Project Structure

```text
Agentic_Job_Finder/
├── agents/
│   ├── job_analyzer.py
│   ├── router.py
│   └── search_agent.py
├── tools/
│   └── job_search.py
├── .env.example
├── .gitignore
├── config.py
├── main.py
├── README.md
├── requirements.txt
└── utils.py
```

## Setup

Install the required packages:

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root and add:

```text
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit the `.env` file or share your actual API keys.

## Run

Run the application with:

```bash
python main.py
```

Example input:

```text
Enter job roles (comma-separated): Business Analyst, Product Manager
Enter location (example: United States, New Mexico, Texas): Texas
Enter your skills (comma-separated): Python, SQL, Excel, Agile, Communication
```

The system searches for real job postings and analyzes how well the candidate's skills match the retrieved jobs.

## API Error Handling

The system handles common Gemini API errors.

- Temporary server errors are retried.
- Request/quota limit errors are handled without crashing the entire application.
- If an analysis cannot be completed, the program can continue processing other jobs.

## Remaining Development

The next development stage will add:

- Routing
- Parallel job analysis
- Reflection/critic agent
- Final job ranking
- User interface