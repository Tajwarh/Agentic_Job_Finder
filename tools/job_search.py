import os
import requests
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")


def search_jobs(role, location, results_per_page=5):
    url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": results_per_page,
        "what": role,
        "where": location,
        "content-type": "application/json",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
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
    jobs = search_jobs(
        role="Business Analyst",
        location="New Mexico"
    )

    for number, job in enumerate(jobs, start=1):
        print(f"\nJOB {number}")
        print("-" * 50)
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Description: {job['description'][:300]}...")
        print(f"URL: {job['url']}")
        