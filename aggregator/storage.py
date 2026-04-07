"""
Supabase storage layer for the aggregator.
Uses service role key to bypass RLS.
"""
import os
from datetime import datetime, timedelta
from supabase import create_client, Client
from .base import NormalizedJob

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def get_client() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_existing_external_ids() -> set[str]:
    """Return all external_ids currently in the jobs table."""
    supabase = get_client()
    result = supabase.table("jobs").select("external_id").execute()
    return {row["external_id"] for row in (result.data or [])}


def upsert_jobs(jobs: list[NormalizedJob]) -> tuple[int, int]:
    """
    Upsert jobs to Supabase. Returns (inserted, updated) counts.
    """
    if not jobs:
        return 0, 0

    supabase = get_client()
    existing_ids = get_existing_external_ids()

    new_jobs = [j for j in jobs if j.external_id not in existing_ids]
    update_jobs = [j for j in jobs if j.external_id in existing_ids]

    inserted = 0
    updated = 0

    # Insert new jobs in batches of 50
    batch_size = 50
    for i in range(0, len(new_jobs), batch_size):
        batch = [j.to_dict() for j in new_jobs[i:i + batch_size]]
        try:
            supabase.table("jobs").insert(batch).execute()
            inserted += len(batch)
        except Exception as e:
            print(f"[STORAGE] Insert error batch {i}: {e}")

    # Update existing jobs (refresh description, skills, etc.)
    for job in update_jobs:
        try:
            supabase.table("jobs").update({
                "title": job.title,
                "description": job.description,
                "skills": job.skills,
                "seniority": job.seniority,
                "modality": job.modality,
                "apply_link": job.apply_link,
                "fetched_at": job.fetched_at,
            }).eq("external_id", job.external_id).execute()
            updated += 1
        except Exception as e:
            print(f"[STORAGE] Update error {job.external_id}: {e}")

    return inserted, updated


def expire_old_jobs(days: int = 30) -> int:
    """
    Mark jobs as expired if they haven't been seen in `days` days.
    Returns count of expired jobs.
    """
    supabase = get_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

    try:
        result = (
            supabase.table("jobs")
            .delete()
            .lt("fetched_at", cutoff)
            .execute()
        )
        return len(result.data or [])
    except Exception as e:
        print(f"[STORAGE] Expire error: {e}")
        return 0


def save_ingestion_log(
    source: str,
    fetched: int,
    inserted: int,
    updated: int,
    duration_seconds: float,
    error: str | None = None,
):
    """Save a record of each aggregation run for monitoring."""
    supabase = get_client()
    try:
        supabase.table("ingestion_logs").insert({
            "source": source,
            "fetched": fetched,
            "inserted": inserted,
            "updated": updated,
            "duration_seconds": round(duration_seconds, 2),
            "error": error,
            "ran_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass  # Log table may not exist yet, don't fail
