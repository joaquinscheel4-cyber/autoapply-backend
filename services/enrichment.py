"""
Background enrichment service: resolves recruiter contacts for jobs using Apollo.io.
Rate limit: 5 requests/minute → 13s between calls.
"""
import asyncio
import logging

logger = logging.getLogger(__name__)

RATE_LIMIT_SECONDS = 13  # 5 req/min with a small safety margin


async def enrich_single_job(job_id: str, company: str) -> bool:
    """
    Enrich one job with Apollo recruiter data. Updates jobs table directly.
    Returns True if a recruiter was found.
    """
    from services.apollo_service import search_recruiter
    from aggregator.storage import get_client

    supabase = get_client()

    try:
        result = await search_recruiter(company)
        if result:
            supabase.table("jobs").update({
                "recruiter_email": result["email"],
                "recruiter_name": result.get("name"),
                "recruiter_title": result.get("title"),
                "email_source": "apollo",
            }).eq("id", job_id).execute()
            logger.info(f"[ENRICH] {company} → {result['email']} ({result.get('title', '')})")
            return True
        else:
            # Mark as searched so we don't retry on every request
            supabase.table("jobs").update({
                "email_source": "not_found",
            }).eq("id", job_id).execute()
            logger.info(f"[ENRICH] {company} → no recruiter found")
            return False

    except Exception as e:
        logger.error(f"[ENRICH] Error enriching job {job_id} ({company}): {e}")
        return False


async def enrich_jobs_batch(jobs: list[dict]) -> None:
    """
    Enrich a list of jobs with Apollo, respecting rate limits.
    Each item in jobs must have: {"id": ..., "company": ...}
    Skips jobs that already have recruiter data or email_source set.
    """
    # Filter out jobs already enriched
    pending = [j for j in jobs if not j.get("recruiter_email") and not j.get("email_source")]

    if not pending:
        logger.info("[ENRICH] All jobs already enriched, nothing to do")
        return

    logger.info(f"[ENRICH] Starting batch enrichment for {len(pending)} jobs")

    for i, job in enumerate(pending):
        if i > 0:
            # Rate limit: wait before each call except the first
            await asyncio.sleep(RATE_LIMIT_SECONDS)

        await enrich_single_job(job["id"], job["company"])


async def enrich_jobs_without_recruiter(limit: int = 30) -> None:
    """
    Enrich all jobs that have no recruiter data yet.
    Safe to call after /aggregate since it queries Supabase for unenriched jobs.
    """
    from aggregator.storage import get_client

    supabase = get_client()
    try:
        result = (
            supabase.table("jobs")
            .select("id, company, recruiter_email, email_source")
            .is_("recruiter_email", "null")
            .is_("email_source", "null")
            .order("fetched_at", desc=True)
            .limit(limit)
            .execute()
        )
        jobs = result.data or []
    except Exception as e:
        logger.error(f"[ENRICH] Failed to fetch unenriched jobs: {e}")
        return

    if not jobs:
        logger.info("[ENRICH] No unenriched jobs found")
        return

    logger.info(f"[ENRICH] Found {len(jobs)} unenriched jobs")
    await enrich_jobs_batch(jobs)
