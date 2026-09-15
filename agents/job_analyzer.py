import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError, ClientError

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


def call_gemini(prompt):
    """
    Send a prompt to Gemini with basic error handling.
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return response.text

        except ServerError:
            if attempt < 2:
                print("Gemini is busy. Retrying...")
                time.sleep(5)
            else:
                return None

        except ClientError as error:
            error_message = str(error)

            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                print("Gemini request limit reached.")
                return None

            print(f"Gemini API error: {error}")
            return None

    return None


def extract_requirements(job):
    """
    PROMPT CHAIN - STEP 1

    Extract important requirements from the real job posting.
    """

    prompt = f"""
You are a job requirements extraction assistant.

Analyze the following real job posting.

Job title:
{job.get("title")}

Company:
{job.get("company")}

Job description:
{job.get("description")}

Extract only the important requirements mentioned in the job description.

Return a concise list containing:

1. Required or important skills
2. Preferred or desired skills
3. Important responsibilities

Do not invent requirements that are not supported by the job description.
"""

    return call_gemini(prompt)


def match_candidate(job, requirements, user_skills):
    """
    PROMPT CHAIN - STEP 2

    Use the output from Step 1 to evaluate the candidate.
    """

    prompt = f"""
You are a job matching assistant.

The previous AI step extracted these requirements
from the job posting:

{requirements}

Candidate skills:
{", ".join(user_skills)}

Job title:
{job.get("title")}

Company:
{job.get("company")}

Using the extracted requirements and candidate skills,
evaluate how well the candidate matches this job.

Return a concise analysis containing:

1. Match Score: a number from 0 to 100
2. Matching Skills
3. Missing or Desired Skills
4. Short Explanation

Only use the candidate skills provided above.
Do not invent candidate experience or skills.
"""

    return call_gemini(prompt)


def analyze_job(job, user_skills):
    """
    Complete two-step prompt chaining workflow.

    Step 1:
    Job description -> Extract requirements

    Step 2:
    Extracted requirements + candidate skills -> Match analysis
    """

    print("Prompt Chain Step 1: Extracting job requirements...")

    requirements = extract_requirements(job)

    if not requirements:
        return (
            "Job analysis could not be completed because "
            "Gemini is temporarily unavailable or the request limit was reached."
        )

    print("Prompt Chain Step 2: Evaluating candidate match...")

    analysis = match_candidate(
        job,
        requirements,
        user_skills
    )

    if not analysis:
        return (
            "Job requirements were extracted, but the final match "
            "analysis could not be completed because Gemini is "
            "temporarily unavailable or the request limit was reached."
        )

    return analysis


# Simple standalone test
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