import warnings

# Suppress fixed sampling warning for models that do not support custom temperature
warnings.filterwarnings("ignore", message=".*uses fixed sampling defaults.*")

from agents.job_analyzer import analyze_job
from agents.reflection_agent import apply_reflection
from agents.router import (
    extract_job_parameters_and_intent,
    generate_resume_draft,
    JobRequest
)
from agents.search_agent import run_job_search_agent


# ==========================
# Handlers for each detected intent
# ==========================

def handler_match_jobs(request: JobRequest):
    """
    Handler responsible for searching jobs via Parallel Tool Calling
    and matching candidate skills using LangChain prompt chaining
    followed by reflection.
    """

    print("\n--- [Handler: Match Jobs] ---")

    roles = request.roles

    if not roles:
        role_fallback = input(
            "No job roles were detected. Please enter a job role: "
        ).strip()

        if role_fallback:
            roles = [
                r.strip()
                for r in role_fallback.split(",")
                if r.strip()
            ]
        else:
            print("No job roles provided. Cannot proceed with job match.")
            return

    skills = request.skills

    if not skills:
        print("\nNote: No candidate skills were detected in your request.")

        skills_fallback = input(
            "Enter your skills (comma-separated), or press Enter to skip: "
        ).strip()

        if skills_fallback:
            skills = [
                s.strip()
                for s in skills_fallback.split(",")
                if s.strip()
            ]

    # Execute Parallel Tool Calling Search Agent
    all_jobs = run_job_search_agent(
        roles=roles,
        locations=request.location,
        results_per_page=3
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
        print(
            f"\nDescription:\n"
            f"{job.get('description', '').strip()}"
        )

        print("\nAnalyzing job match...")

        # Generate initial analysis using existing prompt chaining
        analysis = analyze_job(
            job,
            skills
        )

        print("\nINITIAL MATCH ANALYSIS")
        print("-" * 60)
        print(analysis)

        # ==========================
        # REFLECTION
        # ==========================

        final_analysis = apply_reflection(
            job,
            skills,
            analysis
        )

        print("\nFINAL MATCH ANALYSIS")
        print("-" * 60)
        print(final_analysis)


def handler_list_jobs(request: JobRequest):
    """
    Handler responsible for searching and listing jobs via
    Parallel Tool Calling without full match evaluation.
    """

    print("\n--- [Handler: List Jobs] ---")

    roles = request.roles

    if not roles:
        role_fallback = input(
            "No job roles were detected. Please enter a job role: "
        ).strip()

        if role_fallback:
            roles = [
                r.strip()
                for r in role_fallback.split(",")
                if r.strip()
            ]
        else:
            print("No job roles provided. Cannot proceed with job search.")
            return

    # Execute Parallel Tool Calling Search Agent
    all_jobs = run_job_search_agent(
        roles=roles,
        locations=request.location,
        results_per_page=5
    )

    if not all_jobs:
        print("\nNo jobs found.")
        return

    print(f"\nFound {len(all_jobs)} unique jobs total:\n")

    for number, job in enumerate(all_jobs, start=1):

        print(f"{number}. {job['title']} at {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['url']}")

        desc_snippet = (
            job.get("description", "")
            .replace("\n", " ")[:150]
        )

        if desc_snippet:
            print(f"   Preview: {desc_snippet}...")

        print("-" * 50)


def handler_resume_creator(request: JobRequest):
    """
    Handler responsible for creating or tailoring a resume
    based on candidate skills and target roles.
    """

    print("\n--- [Handler: Resume Creator] ---")
    print(
        "Generating tailored resume recommendations "
        "using LangChain...\n"
    )

    resume_text = generate_resume_draft(
        roles=request.roles,
        skills=request.skills
    )

    print("=" * 60)
    print("RESUME DRAFT & ATS RECOMMENDATIONS")
    print("=" * 60)
    print(resume_text)


HANDLERS = {
    "handler_match_jobs": handler_match_jobs,
    "handler_list_jobs": handler_list_jobs,
    "handler_resume_creator": handler_resume_creator,
}


def main():

    print("\n=== AGENTIC JOB FINDER ===")

    user_prompt = input(
        "\nEnter your request "
        "(e.g. 'Match Python Developer jobs in Texas for Python, SQL'): "
    ).strip()

    if not user_prompt:
        print("No request entered. Exiting.")
        return

    print(
        "\nProcessing request and extracting parameters "
        "with LangChain..."
    )

    job_request = extract_job_parameters_and_intent(
        user_prompt
    )

    print("\n" + "=" * 60)
    print("REQUEST EXTRACTION & ROUTING")
    print("=" * 60)

    print(
        f"Detected Intent : "
        f"{job_request.intent}"
    )

    print(
        f"Target Roles    : "
        f"{', '.join(job_request.roles) if job_request.roles else 'None detected'}"
    )

    print(
        f"Target Location : "
        f"{', '.join(job_request.location) if job_request.location else 'United States'}"
    )

    print(
        f"Candidate Skills: "
        f"{', '.join(job_request.skills) if job_request.skills else 'None detected'}"
    )

    print("=" * 60)

    handler = HANDLERS.get(
        job_request.intent,
        handler_match_jobs
    )

    handler(job_request)


if __name__ == "__main__":
    main()