"""
Greenhouse Job Board API connector.
No authentication required — completely public.
Docs: https://developers.greenhouse.io/job-board.html
"""
import asyncio
import aiohttp
from .base import BaseConnector, NormalizedJob
from .companies_chile import GREENHOUSE_COMPANIES


CHILE_KEYWORDS = {
    "chile", "santiago", "latam", "latin america", "latinoamerica",
    "remote", "remoto", "anywhere", "worldwide"
}


def is_chile_relevant(job: dict) -> bool:
    """Return True if the job is relevant for the Chilean market."""
    location = (job.get("location", {}).get("name") or "").lower()
    title = (job.get("title") or "").lower()
    content = str(job.get("content") or "").lower()

    # Explicit Chile/LATAM mention
    for kw in CHILE_KEYWORDS:
        if kw in location or kw in content:
            return True

    # Remote jobs from Chilean companies are always relevant
    if "remote" in location or "remoto" in location:
        return True

    # If no location info, include it (company is Chilean)
    if not location or location in ("", "none", "null"):
        return True

    return False


def extract_skills_from_content(content: str) -> list[str]:
    """Extract tech skills from job description."""
    SKILL_KEYWORDS = [
        "python", "javascript", "typescript", "java", "c#", ".net", "ruby", "go",
        "react", "vue", "angular", "node.js", "nextjs", "django", "fastapi", "flask",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
        "git", "ci/cd", "jenkins", "github actions",
        "machine learning", "deep learning", "nlp", "data science",
        "sql", "spark", "airflow", "dbt", "tableau", "power bi",
        "figma", "sketch", "photoshop",
        "scrum", "agile", "kanban", "jira",
        "excel", "sap", "salesforce",
    ]
    content_lower = content.lower()
    return [skill for skill in SKILL_KEYWORDS if skill in content_lower]


def detect_seniority(title: str, content: str) -> str | None:
    text = (title + " " + content).lower()
    if any(w in text for w in ["lead", "staff", "principal", "director", "head of"]):
        return "lead"
    if any(w in text for w in ["senior", "sr.", "sr ", "ssr"]):
        return "senior"
    if any(w in text for w in ["semi-senior", "mid-level", "mid level", "pleno"]):
        return "semi-senior"
    if any(w in text for w in ["junior", "jr.", "jr ", "trainee", "intern", "practicante"]):
        return "junior"
    return None


def parse_salary(job: dict) -> tuple[int | None, int | None]:
    """Try to extract salary from Greenhouse metadata."""
    metadata = job.get("metadata") or []
    for m in metadata:
        name = (m.get("name") or "").lower()
        if "salary" in name or "salario" in name or "sueldo" in name:
            value = m.get("value")
            if isinstance(value, dict):
                return value.get("min_value"), value.get("max_value")
    return None, None


class GreenhouseConnector(BaseConnector):
    name = "greenhouse"
    rate_limit_seconds = 0.3

    async def _fetch_company_jobs(
        self, session: aiohttp.ClientSession, company: dict
    ) -> list[NormalizedJob]:
        slug = company["slug"]
        company_name = company["name"]
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return []  # Company no longer on Greenhouse
                if resp.status != 200:
                    self.log(f"HTTP {resp.status} for {slug}")
                    return []

                data = await resp.json()
                jobs = data.get("jobs", [])

        except Exception as e:
            self.log(f"Error fetching {slug}: {e}")
            return []

        normalized = []
        for job in jobs:
            if not is_chile_relevant(job):
                continue

            content = job.get("content") or ""
            title = job.get("title") or ""
            location_name = (job.get("location") or {}).get("name") or "Chile"

            salary_min, salary_max = parse_salary(job)

            normalized.append(NormalizedJob(
                external_id=f"gh_{job['id']}",
                source="greenhouse",
                title=title,
                company=company_name,
                location=location_name,
                country="CL",
                modality="remote" if any(
                    w in location_name.lower() for w in ["remote", "remoto", "anywhere"]
                ) else None,
                description=content[:3000],
                apply_link=job.get("absolute_url"),
                skills=extract_skills_from_content(content),
                seniority=detect_seniority(title, content),
                salary_min=salary_min,
                salary_max=salary_max,
                posted_at=job.get("updated_at"),
            ))

        if normalized:
            self.log(f"{company_name}: {len(normalized)} Chile-relevant jobs")
        return normalized

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        self.log(f"Fetching from {len(GREENHOUSE_COMPANIES)} companies...")
        all_jobs = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_company_jobs(session, company)
                for company in GREENHOUSE_COMPANIES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
