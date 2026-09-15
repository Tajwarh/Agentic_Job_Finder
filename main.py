from tools.job_search import search_jobs
from agents.job_analyzer import analyze_job


def is_duplicate(job, existing_jobs):
    """
    Treat a job as a duplicate when the title, company,
    and location are all the same.
    """
    for existing_job in existing_jobs:
        same_title = (
            job.get("title", "").strip().lower()
            == existing_job.get("title", "").strip().lower()
        )

        same_company = (
            job.get("company", "").strip().lower()
            == existing_job.get("company", "").strip().lower()
        )

        same_location = (
            job.get("location", "").strip().lower()
            == existing_job.get("location", "").strip().lower()
        )

        if same_title and same_company and same_location:
            return True

    return False


def main():
    print("\n=== AGENTIC JOB FINDER ===")

    roles_input = input(
        "Enter job roles (comma-separated): "
    )

    location = input(
        "Enter location (example: United States, New Mexico, Texas): "
    )

    skills_input = input(
        "Enter your skills (comma-separated): "
    )

    roles = [
        role.strip()
        for role in roles_input.split(",")
        if role.strip()
    ]

    user_skills = [
        skill.strip()
        for skill in skills_input.split(",")
        if skill.strip()
    ]

    print("\nSearching for jobs...")

    all_jobs = []

    for role in roles:
        print(f"\nSearching for: {role}")

        jobs = search_jobs(
            role=role,
            location=location,
            results_per_page=3
        )

        for job in jobs:
            job["searched_role"] = role

            if not is_duplicate(job, all_jobs):
                all_jobs.append(job)
            else:
                print(
                    f"Skipping duplicate: "
                    f"{job['title']} - {job['company']}"
                )

    if not all_jobs:
        print("\nNo jobs found.")
        return

    print(f"\nFound {len(all_jobs)} unique jobs total.")

    for number, job in enumerate(all_jobs, start=1):

        print("\n" + "=" * 60)
        print(f"JOB {number}")
        print("=" * 60)

        print(f"Searched Role: {job['searched_role']}")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")

        print("\nAnalyzing job match...")

        analysis = analyze_job(
            job,
            user_skills
        )

        print("\nMATCH ANALYSIS")
        print("-" * 60)
        print(analysis)


if __name__ == "__main__":
    main()