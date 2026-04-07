"""
Deduplication engine.
Detects duplicate jobs across sources using fuzzy matching.
"""
import re
import unicodedata
from .base import NormalizedJob


def normalize_text(text: str) -> str:
    """Lowercase, remove accents, collapse whitespace."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def title_similarity(a: str, b: str) -> float:
    """
    Simple token-based similarity (Jaccard).
    Returns 0.0 to 1.0.
    """
    tokens_a = set(normalize_text(a).split())
    tokens_b = set(normalize_text(b).split())

    # Remove very common words
    stopwords = {"de", "en", "para", "y", "o", "a", "el", "la", "los", "las", "un", "una"}
    tokens_a -= stopwords
    tokens_b -= stopwords

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def company_similarity(a: str, b: str) -> float:
    """Check if two company names are the same entity."""
    na = normalize_text(a)
    nb = normalize_text(b)

    if na == nb:
        return 1.0

    # One is contained in the other (e.g. "Banco Santander" vs "Banco Santander Chile")
    if na in nb or nb in na:
        return 0.85

    # First word match (usually the distinctive part)
    wa = na.split()
    wb = nb.split()
    if wa and wb and wa[0] == wb[0]:
        return 0.7

    return 0.0


def is_duplicate(job_a: NormalizedJob, job_b: NormalizedJob) -> bool:
    """
    Return True if two jobs are likely duplicates.
    Rules:
      - Same external_id from same source → always duplicate
      - Same company + very similar title (>0.8) + same country → duplicate
      - Same company + same title + different location → NOT duplicate
    """
    if job_a.external_id == job_b.external_id:
        return True

    comp_score = company_similarity(job_a.company, job_b.company)
    if comp_score < 0.7:
        return False

    title_score = title_similarity(job_a.title, job_b.title)
    if title_score < 0.75:
        return False

    # Same company + very similar title = duplicate
    return True


def deduplicate(jobs: list[NormalizedJob]) -> list[NormalizedJob]:
    """
    Remove duplicates from a list of jobs.
    When duplicates are found, keep the one with more complete data
    (longer description, more skills).
    """
    if not jobs:
        return []

    # Priority order — prefer ATS sources (more structured data)
    SOURCE_PRIORITY = {
        "greenhouse": 1,
        "lever": 2,
        "smartrecruiters": 3,
        "workday": 4,
        "laborum": 5,
        "computrabajo": 6,
    }

    def job_quality_score(job: NormalizedJob) -> int:
        score = 0
        score += len(job.description) // 100
        score += len(job.skills) * 5
        if job.seniority:
            score += 5
        if job.salary_min:
            score += 10
        if job.apply_email:
            score += 20
        # Prefer ATS sources
        score += (10 - SOURCE_PRIORITY.get(job.source, 9)) * 3
        return score

    kept: list[NormalizedJob] = []

    for job in jobs:
        merged = False
        for i, existing in enumerate(kept):
            if is_duplicate(job, existing):
                # Keep the higher quality one
                if job_quality_score(job) > job_quality_score(existing):
                    kept[i] = job
                merged = True
                break

        if not merged:
            kept.append(job)

    return kept


def deduplicate_with_existing(
    new_jobs: list[NormalizedJob],
    existing_external_ids: set[str],
) -> list[NormalizedJob]:
    """Filter out jobs that already exist in the database by external_id."""
    return [j for j in new_jobs if j.external_id not in existing_external_ids]
