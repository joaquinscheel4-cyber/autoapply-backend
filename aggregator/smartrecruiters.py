"""
SmartRecruiters Public API connector.
No authentication required for public job postings.
Docs: https://dev.smartrecruiters.com/customer-api/live-docs/job-api/
"""
import asyncio
import aiohttp
from .base import BaseConnector, NormalizedJob
from .companies_chile import SMARTRECRUITERS_COMPANIES
from .greenhouse import extract_skills_from_content, detect_seniority


def map_sr_modality(job: dict) -> str | None:
    remote = (job.get("workplace", {}).get("wfhPolicy") or "").lower()
    if remote == "fully":
        return "remote"
    if remote == "hybrid":
        return "hybrid"
    if remote == "office":
        return "presencial"
    return None


class SmartRecruitersConnector(BaseConnector):
    name = "smartrecruiters"
    rate_limit_seconds = 0.5

    async def _fetch_company_jobs(
        self, session: aiohttp.ClientSession, company: dict
    ) -> list[NormalizedJob]:
        slug = company["slug"]
        company_name = company["name"]
        url = (
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
            "?limit=100&offset=0"
        )

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status in (404, 403):
                    return []
                if resp.status != 200:
                    self.log(f"HTTP {resp.status} for {slug}")
                    return []
                data = await resp.json()
        except Exception as e:
            self.log(f"Error fetching {slug}: {e}")
            return []

        postings = data.get("content", [])
        normalized = []

        for p in postings:
            title = p.get("name") or ""
            description = (p.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text") or "")
            location_parts = [
                p.get("location", {}).get("city") or "",
                p.get("location", {}).get("country") or "",
            ]
            location = ", ".join(x for x in location_parts if x) or "Chile"

            normalized.append(NormalizedJob(
                external_id=f"sr_{p['id']}",
                source="smartrecruiters",
                title=title,
                company=company_name,
                location=location,
                country="CL",
                modality=map_sr_modality(p),
                description=description[:3000],
                apply_link=f"https://jobs.smartrecruiters.com/{slug}/{p['id']}",
                skills=extract_skills_from_content(description),
                seniority=detect_seniority(title, description),
                posted_at=p.get("releasedDate"),
            ))

        if normalized:
            self.log(f"{company_name}: {len(normalized)} jobs")
        return normalized

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        self.log(f"Fetching from {len(SMARTRECRUITERS_COMPANIES)} companies...")
        all_jobs = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_company_jobs(session, company)
                for company in SMARTRECRUITERS_COMPANIES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
