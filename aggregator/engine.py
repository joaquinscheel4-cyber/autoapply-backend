"""
Aggregation engine — orchestrates all connectors.
"""
import asyncio
import time
from .base import NormalizedJob
from .greenhouse import GreenhouseConnector
from .lever import LeverConnector
from .smartrecruiters import SmartRecruitersConnector
from .workday import WorkdayConnector
from .computrabajo import ComputrabajoConnector
from .laborum import LaborumConnector
from .deduplicator import deduplicate, deduplicate_with_existing
from .storage import upsert_jobs, expire_old_jobs, save_ingestion_log, get_existing_external_ids


def get_all_connectors(fast_mode: bool = False) -> list:
    """
    Return all enabled connectors.
    fast_mode=True: only API-based sources (skip slow scrapers).
    """
    connectors = [
        GreenhouseConnector(),
        LeverConnector(),
        SmartRecruitersConnector(),
    ]

    if not fast_mode:
        connectors += [
            WorkdayConnector(),
            ComputrabajoConnector(max_per_role=8, roles_to_fetch=15),
            LaborumConnector(),
        ]

    return connectors


async def run_aggregation(
    roles: list[str] | None = None,
    fast_mode: bool = False,
    dry_run: bool = False,
) -> dict:
    """
    Main aggregation function.

    Args:
        roles: Target job roles to search for (from user preferences).
               If None, uses a broad default set.
        fast_mode: Only use API sources (faster, fewer jobs).
        dry_run: Fetch but don't save to database.

    Returns:
        Summary dict with counts per source.
    """
    if roles is None:
        roles = [
            "desarrollador", "ingeniero", "analista",
            "product manager", "diseñador", "contador",
        ]

    print(f"\n{'='*50}")
    print(f"AGGREGATION START — roles: {roles[:5]}")
    print(f"fast_mode={fast_mode}, dry_run={dry_run}")
    print(f"{'='*50}\n")

    start_time = time.time()
    connectors = get_all_connectors(fast_mode=fast_mode)

    # Run all connectors in parallel
    tasks = [connector.fetch_jobs(roles) for connector in connectors]
    all_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results with source tracking
    all_jobs: list[NormalizedJob] = []
    source_counts: dict[str, int] = {}

    for connector, result in zip(connectors, all_results):
        if isinstance(result, Exception):
            print(f"[ENGINE] {connector.name} FAILED: {result}")
            source_counts[connector.name] = 0
        else:
            source_counts[connector.name] = len(result)
            all_jobs.extend(result)
            print(f"[ENGINE] {connector.name}: {len(result)} jobs fetched")

    print(f"\n[ENGINE] Total raw jobs: {len(all_jobs)}")

    # Deduplication — first across sources
    deduped = deduplicate(all_jobs)
    print(f"[ENGINE] After deduplication: {len(deduped)} unique jobs")

    if dry_run:
        print("[ENGINE] DRY RUN — skipping database save")
        return {
            "total_fetched": len(all_jobs),
            "after_dedup": len(deduped),
            "inserted": 0,
            "updated": 0,
            "sources": source_counts,
            "duration_seconds": round(time.time() - start_time, 2),
        }

    # Filter already-existing IDs for efficiency
    existing_ids = get_existing_external_ids()
    new_jobs = deduplicate_with_existing(deduped, existing_ids)
    existing_to_update = [j for j in deduped if j.external_id in existing_ids]

    print(f"[ENGINE] New jobs: {len(new_jobs)}, to update: {len(existing_to_update)}")

    # Save to Supabase
    inserted, updated = upsert_jobs(new_jobs + existing_to_update)

    # Expire old jobs (not seen in 30 days)
    expired = expire_old_jobs(days=30)
    if expired:
        print(f"[ENGINE] Expired {expired} old jobs")

    duration = round(time.time() - start_time, 2)
    print(f"\n[ENGINE] DONE in {duration}s — inserted={inserted}, updated={updated}")

    # Log to monitoring table
    for connector_name, count in source_counts.items():
        save_ingestion_log(
            source=connector_name,
            fetched=count,
            inserted=0,  # We don't track per-source inserts
            updated=0,
            duration_seconds=duration,
        )

    return {
        "total_fetched": len(all_jobs),
        "after_dedup": len(deduped),
        "new_jobs": len(new_jobs),
        "inserted": inserted,
        "updated": updated,
        "expired": expired,
        "sources": source_counts,
        "duration_seconds": duration,
    }
