# Contains some utility functions for job postings, such as deduplication and duplicate checking.

def is_duplicate_job(job: dict, existing_jobs: list[dict]) -> bool:
    """
    Check if a job posting is a duplicate of one in existing_jobs
    based on matching title, company, and location.
    """
    for existing in existing_jobs:
        same_title = (
            job.get("title", "").strip().lower()
            == existing.get("title", "").strip().lower()
        )
        same_company = (
            job.get("company", "").strip().lower()
            == existing.get("company", "").strip().lower()
        )
        same_location = (
            job.get("location", "").strip().lower()
            == existing.get("location", "").strip().lower()
        )
        if same_title and same_company and same_location:
            return True
    return False


def deduplicate_jobs(jobs: list[dict]) -> list[dict]:
    """
    Filter a list of job postings, removing duplicates while
    preserving the original order.
    """
    unique_jobs = []
    for job in jobs:
        if not is_duplicate_job(job, unique_jobs):
            unique_jobs.append(job)
        else:
            print(f"Skipping duplicate: {job.get('title')} - {job.get('company')}")
    return unique_jobs

