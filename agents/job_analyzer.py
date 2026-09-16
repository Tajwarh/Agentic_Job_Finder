import os
import warnings
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import DEFAULT_MODEL, REQUIREMENTS_PROMPT_TEMPLATE, MATCHING_PROMPT_TEMPLATE

# Suppress fixed sampling warning for models that do not support custom temperature
warnings.filterwarnings("ignore", message=".*uses fixed sampling defaults.*")

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = API_KEY


def get_llm(temperature: float = 0.2):
    """
    Instantiate LangChain ChatGoogleGenerativeAI client.
    """
    kwargs = {
        "model": DEFAULT_MODEL,
        "google_api_key": API_KEY,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatGoogleGenerativeAI(**kwargs)


# LangChain LCEL Chains
llm = get_llm()

requirements_prompt = ChatPromptTemplate.from_template(REQUIREMENTS_PROMPT_TEMPLATE)
requirements_chain = requirements_prompt | llm | StrOutputParser()

matching_prompt = ChatPromptTemplate.from_template(MATCHING_PROMPT_TEMPLATE)
matching_chain = matching_prompt | llm | StrOutputParser()


def extract_requirements(job: dict) -> str:
    """
    PROMPT CHAIN - STEP 1 (LangChain LCEL)
    Extract important requirements from the real job posting.
    """
    try:
        return requirements_chain.invoke({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "description": job.get("description", "")
        })
    except Exception as e:
        print(f"Error during LangChain requirements extraction: {e}")
        return ""


def match_candidate(job: dict, requirements: str, user_skills: list[str]) -> str:
    """
    PROMPT CHAIN - STEP 2 (LangChain LCEL)
    Evaluate the candidate match against the extracted requirements.
    """
    try:
        skills_str = ", ".join(user_skills) if user_skills else "None specified"
        return matching_chain.invoke({
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "requirements": requirements,
            "skills": skills_str
        })
    except Exception as e:
        print(f"Error during LangChain candidate matching: {e}")
        return ""


def analyze_job(job: dict, user_skills: list[str]) -> str:
    """
    Complete two-step LangChain prompt chaining workflow.

    Step 1:
    Job description -> Extract requirements via LCEL

    Step 2:
    Extracted requirements + candidate skills -> Match analysis via LCEL
    """
    print("LangChain Prompt Chain Step 1: Extracting job requirements...")
    requirements = extract_requirements(job)

    if not requirements:
        return (
            "Job analysis could not be completed because "
            "the LLM request failed or limit was reached."
        )

    print("LangChain Prompt Chain Step 2: Evaluating candidate match...")
    analysis = match_candidate(job, requirements, user_skills)

    if not analysis:
        return (
            "Job requirements were extracted, but the final match "
            "analysis could not be completed."
        )

    return analysis


if __name__ == "__main__":
    test_job = {
        "title": "Business Analyst",
        "company": "Test Company",
        "description": """
        We are looking for a Business Analyst with experience in
        SQL, Excel, Python, data analysis, requirements gathering,
        and communication.
        """
    }

    test_skills = [
        "Python",
        "SQL",
        "Excel",
        "Communication"
    ]

    result = analyze_job(
        test_job,
        test_skills
    )

    print("\nJOB ANALYSIS")
    print("-" * 50)
    print(result)