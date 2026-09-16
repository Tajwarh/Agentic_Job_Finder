import os
import warnings
from typing import Literal, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from config import DEFAULT_MODEL, ROUTER_PROMPT, RESUME_PROMPT_TEMPLATE

# Suppress fixed sampling warning for models that do not support custom temperature
warnings.filterwarnings("ignore", message=".*uses fixed sampling defaults.*")

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = API_KEY


# Blueprint for structured output using Pydantic
class JobRequest(BaseModel):
    intent: Literal[
        "handler_resume_creator",
        "handler_match_jobs",
        "handler_list_jobs"
    ] = Field(
        default="handler_match_jobs",
        description="The detected handler to execute based on user intent."
    )
    roles: list[str] = Field(
        default_factory=list,
        description="Target job roles or titles extracted from the user's prompt."
    )
    location: list[str] = Field(
        default_factory=lambda: ["United States"],
        description="Location(s) extracted from the user's prompt, defaulting to ['United States'] if unspecified."
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Candidate skills extracted from the user's prompt."
    )

    @field_validator("roles", "location", "skills", mode="before")
    @classmethod
    def coerce_to_clean_list(cls, v: Any) -> list[str]:
        """
        Coerce string or list input into a clean list of individual strings,
        splitting any comma-separated values and stripping whitespace.
        """
        if v is None:
            return []
        if isinstance(v, str):
            items = [item.strip() for item in v.split(",") if item.strip()]
            return items if items else [v.strip()] if v.strip() else []
        if isinstance(v, list):
            flattened = []
            for item in v:
                if isinstance(item, str):
                    for sub_item in item.split(","):
                        cleaned = sub_item.strip()
                        if cleaned and cleaned not in flattened:
                            flattened.append(cleaned)
                elif item is not None:
                    cleaned = str(item).strip()
                    if cleaned and cleaned not in flattened:
                        flattened.append(cleaned)
            return flattened
        return [str(v)]


# router llm object
def get_router_llm(temperature: float = 0.0):
    """
    Instantiate LangChain ChatGoogleGenerativeAI client for routing and parameter extraction.
    """
    kwargs = {
        "model": DEFAULT_MODEL,
        "google_api_key": API_KEY,
    }
    if temperature is not None:
        kwargs["temperature"] = temperature
    return ChatGoogleGenerativeAI(**kwargs)


# Initialize Router Chain with structured output
llm = get_router_llm()
structured_llm = llm.with_structured_output(JobRequest)

router_prompt = ChatPromptTemplate.from_messages([
    ("system", ROUTER_PROMPT),
    ("human", "{user_prompt}")
])

router_chain = router_prompt | structured_llm

# Build LangChain Resume Generation Chain
resume_prompt = ChatPromptTemplate.from_template(RESUME_PROMPT_TEMPLATE)
resume_chain = resume_prompt | llm | StrOutputParser()


def extract_job_parameters_and_intent(user_prompt: str) -> JobRequest:
    """
    Use LangChain with structured output to analyze the user's prompt,
    extract search parameters (roles, location, skills), and detect the intent handler.
    """
    try:
        result = router_chain.invoke({"user_prompt": user_prompt})
        if isinstance(result, JobRequest):
            return result
        elif isinstance(result, dict):
            return JobRequest.model_validate(result)
    except Exception as e:
        print(f"Error during LangChain routing extraction: {e}")

    # Fallback default if extraction fails
    return JobRequest(
        intent="handler_match_jobs",
        roles=[],
        location=["United States"],
        skills=[]
    )


def generate_resume_draft(roles: list[str], skills: list[str]) -> str:
    """
    Generate a tailored resume draft and ATS guide using LangChain LCEL.
    """
    roles_str = ", ".join(roles) if roles else "General Professional"
    skills_str = ", ".join(skills) if skills else "General Skills"

    try:
        return resume_chain.invoke({
            "roles": roles_str,
            "skills": skills_str
        })
    except Exception as e:
        print(f"Error during LangChain resume generation: {e}")
        return "Resume generation could not be completed due to an error."
