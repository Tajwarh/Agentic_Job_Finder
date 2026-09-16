import os
import warnings
import concurrent.futures
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import DEFAULT_MODEL
from tools.job_search import search_jobs
from utils import is_duplicate_job, deduplicate_jobs

# Suppress fixed sampling warning for models that do not support custom temperature
warnings.filterwarnings("ignore", message=".*uses fixed sampling defaults.*")

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = API_KEY


def get_search_agent_llm():
    """
    Instantiate LangChain LLM for the Tool Calling Search Agent.
    """
    return ChatGoogleGenerativeAI(
        model=DEFAULT_MODEL,
        google_api_key=API_KEY,
    )


# Tools available for the LLM to pick
tools = [search_jobs]
tools_by_name = {t.name: t for t in tools}

llm = get_search_agent_llm()
llm_with_tools = llm.bind_tools(tools)

SEARCH_AGENT_SYSTEM_PROMPT = """You are an agent with access to external tools.
Your task is to review the routed job search requirements and decide which tools to call.

Available tools:
- search_jobs: Searches the Adzuna job board for real postings given a role and location.

Based on the requested roles and locations, generate a `search_jobs` tool call for each role and location requested.
"""


def _execute_tool_call(tool_call: dict) -> list[dict]:
    """
    Worker function to execute a single tool call concurrently.
    """
    tool_name = tool_call.get("name")
    tool_args = tool_call.get("args", {})

    print(f"[Parallel Tool Call] Executing '{tool_name}' with parameters: {tool_args}")

    if tool_name in tools_by_name:
        tool_instance = tools_by_name[tool_name]
        result = tool_instance.invoke(tool_args)
        searched_role = tool_args.get("role", "Job Role")

        if isinstance(result, list):
            for job in result:
                job["searched_role"] = searched_role
            return result
    return []


def run_job_search_agent(roles: list[str], locations: list[str], results_per_page: int = 3) -> list[dict]:
    """
    Executes Tool Selection and Parallel Tool Use:
    1. The routed search request is presented to the LLM bound with tools.
    2. The LLM decides which tool to call and produces tool call(s).
    3. Multiple tool calls are executed concurrently in parallel via ThreadPoolExecutor.
    4. Retrieved postings are aggregated and deduplicated.
    """
    all_raw_jobs = []

    clean_roles = roles if isinstance(roles, list) else [roles]
    clean_locations = locations if isinstance(locations, list) else [locations]
    if not clean_locations:
        clean_locations = ["United States"]

    roles_str = ", ".join(clean_roles)
    locs_str = ", ".join(clean_locations)

    user_query = (
        f"The user needs to find job postings.\n"
        f"Target Roles: [{roles_str}]\n"
        f"Target Locations: [{locs_str}]\n"
        f"Results requested per search: {results_per_page}\n\n"
        f"Please pick and invoke the `search_jobs` tool for each role and location."
    )

    print("\n[Tool Selection] Presenting routed request to LLM with available tools: ['search_jobs']...")

    try:
        messages = [
            SystemMessage(content=SEARCH_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=user_query)
        ]
        response = llm_with_tools.invoke(messages)

        # Inspect which tool(s) the LLM decided to pick
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = response.tool_calls
            print(f"\n[Parallel Tool Use] LLM generated {len(tool_calls)} tool call(s).")
            print(f"[Parallel Tool Use] Launching concurrent execution across threads...")

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tool_calls), 5)) as executor:
                results = list(executor.map(_execute_tool_call, tool_calls))

            for res in results:
                if isinstance(res, list):
                    all_raw_jobs.extend(res)
        else:
            print("[Tool Selection] Fallback: Executing parallel tool calls for roles and locations...")
            fallback_calls = []
            for role in clean_roles:
                for loc in clean_locations:
                    fallback_calls.append({
                        "name": "search_jobs",
                        "args": {
                            "role": role,
                            "location": loc,
                            "results_per_page": results_per_page
                        }
                    })

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(fallback_calls), 5)) as executor:
                results = list(executor.map(_execute_tool_call, fallback_calls))

            for res in results:
                if isinstance(res, list):
                    all_raw_jobs.extend(res)

    except Exception as e:
        print(f"Error during LLM tool selection: {e}")
        # Fallback concurrent invocation
        fallback_calls = []
        for role in clean_roles:
            for loc in clean_locations:
                fallback_calls.append({
                    "name": "search_jobs",
                    "args": {
                        "role": role,
                        "location": loc,
                        "results_per_page": results_per_page
                    }
                })

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(fallback_calls), 5)) as executor:
            results = list(executor.map(_execute_tool_call, fallback_calls))

        for res in results:
            if isinstance(res, list):
                all_raw_jobs.extend(res)

    # Deduplicate all collected postings
    print(f"\n[Deduplication] Filtering duplicate postings from {len(all_raw_jobs)} total results...")
    return deduplicate_jobs(all_raw_jobs)
