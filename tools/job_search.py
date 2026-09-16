import os
import requests
from langchain.tools import tool
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


@tool("search_jobs")
def search_jobs(role, location="United States", results_per_page=5) -> list:
    """
    Search for real job postings on the Adzuna job board matching a role and location.

    Args:
        role: The specific job role or job title to search for (e.g., 'Business Analyst', 'Software Engineer').
        location: City, state, or 'Remote' to search in (e.g., 'Texas', 'New York', 'United States').
        results_per_page: Number of job postings to retrieve (typically 3 to 5).

    Returns:
        List of job posting dicts with title, company, location, description, and url.
    """
    # Normalize role if passed as a list
    if isinstance(role, list):
        role = role[0] if len(role) == 1 else ", ".join(role)
    search_what = str(role or "").strip()

    # Normalize location if passed as a list
    if isinstance(location, list):
        location = location[0] if location else ""
    loc_str = str(location or "").strip()

    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": results_per_page,
        "what": search_what,
        "content-type": "application/json",
    }

    # Adzuna /jobs/us/ API expects city/state for 'where'.
    # If 'where' is set to "United States", Adzuna fails to find any city with that name.
    # Omitting 'where' searches nationwide across the US.
    if loc_str:
        loc_lower = loc_str.lower()
        if loc_lower in ["united states", "us", "usa", "u.s.", "u.s.a.", "nationwide", "any", "all", ""]:
            pass  # Nationwide search: do not add 'where' parameter
        elif "remote" in loc_lower:
            if "remote" not in search_what.lower():
                params["what"] = f"{search_what} remote"
        else:
            params["where"] = loc_str

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Adzuna API request error: {e}")
        return []

    jobs = []
    for job in data.get("results", []):
        description = job.get("description") or ""

        jobs.append({
            "title": job.get("title"),
            "company": job.get("company", {}).get("display_name"),
            "location": job.get("location", {}).get("display_name"),
            "description": description,
            "url": job.get("redirect_url"),
        })

    return jobs


if __name__ == "__main__":
    jobs = search_jobs.invoke({
        "role": "Business Analyst",
        "location": "New Mexico"
    })

    for number, job in enumerate(jobs, start=1):
        print(f"\nJOB {number}")
        print("-" * 50)
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Description: {job['description'][:300]}...")
        print(f"URL: {job['url']}")