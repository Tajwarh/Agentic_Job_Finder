import os
from dotenv import load_dotenv

load_dotenv()

# Model configuration
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Prompt for Router & Parameter Extraction
ROUTER_PROMPT = """You are an intelligent job assistant routing agent.
Analyze the user's input prompt and extract:
1. The user's primary intent:
   - "handler_resume_creator": The user wants to build, create, or tailor a resume/CV for specific roles and skills.
   - "handler_match_jobs": The user wants to search for jobs and see how well their skills match the job requirements.
   - "handler_list_jobs": The user simply wants to search, list, or browse available job postings without detailed candidate matching.

2. Key job search parameters:
   - roles: A list of clean, specific job titles or roles mentioned (e.g., ["Data Scientist", "Software Engineer"]). Do not include full sentences or adjectives. If none mentioned, leave as an empty list.
   - location: A list of locations mentioned (e.g., ["Texas"], ["New York"], ["Remote"]). If none mentioned, default to ["United States"].
   - skills: A list of candidate skills or technologies mentioned (e.g., ["Python", "SQL", "Excel"]). If none mentioned, leave as an empty list.
"""

# Prompt for Job Requirements Extraction (Prompt Chain Step 1)
REQUIREMENTS_PROMPT_TEMPLATE = """You are a job requirements extraction assistant.

Analyze the following real job posting:

Job Title: {title}
Company: {company}
Job Description:
{description}

Extract only the important requirements mentioned in the job description.
Return a concise list containing:
1. Required or important skills
2. Preferred or desired skills
3. Important responsibilities

Do not invent requirements that are not supported by the job description.
"""

# Prompt for Candidate Matching (Prompt Chain Step 2)
MATCHING_PROMPT_TEMPLATE = """You are a job matching assistant.

The previous AI step extracted these requirements from the job posting:
{requirements}

Candidate Skills:
{skills}

Job Title: {title}
Company: {company}

Using the extracted requirements and candidate skills, evaluate how well the candidate matches this job.
Return a concise analysis containing:
1. Match Score: a number from 0 to 100
2. Matching Skills
3. Missing or Desired Skills
4. Short Explanation

Only use the candidate skills provided above. Do not invent candidate experience or skills.
"""

# Prompt for Resume Generation
RESUME_PROMPT_TEMPLATE = """You are an expert career advisor and professional resume writer.

Create a tailored resume draft and ATS optimization guide for the candidate based on:
Target Roles: {roles}
Candidate Skills: {skills}

Please structure your response with:
1. Professional Summary (a compelling 3-4 sentence elevator pitch)
2. Core Competencies & Skills Matrix
3. Recommended Experience Bullet Points (demonstrating how to showcase these skills in action)
4. ATS Keywords to include for these specific target roles
"""