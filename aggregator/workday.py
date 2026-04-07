"""
Workday JSON API connector.
Workday exposes a public JSON API for all companies' career sites.
No authentication required.
"""
import asyncio
import aiohttp
from .base import BaseConnector, NormalizedJob
from .companies_chile import WORKDAY_COMPANIES
from .greenhouse import extract_skills_from_content, detect_seniority


class WorkdayConnector(BaseConnector):
    name = "workday"
    rate_limit_seconds = 1.0

    async def _fetch_company_jobs(
        self, session: aiohttp.ClientSession, company: dict
    ) -> list[NormalizedJob]:
        company_name = company["name"]
        base_url = company["base_url"]
        tenant = company["tenant"]
        board = company["board"]

        url = f"{base_url}/wday/cxs/{tenant}/{board}/jobs"
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": "",
        }

        try:
            async with session.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    self.log(f"HTTP {resp.status} for {company_name}")
                    return []
                data = await resp.json()
        except Exception as e:
            self.log(f"Error fetching {company_name}: {e}")
            return []

        job_postings = data.get("jobPostings", [])
        normalized = []

        for jp in job_postings:
            title = jp.get("title") or ""
            external_path = jp.get("externalPath") or ""
            job_id = external_path.split("/")[-1] if external_path else jp.get("bulletFields", [""])[0]

            location_data = jp.get("locationsText") or jp.get("location") or "Chile"

            normalized.append(NormalizedJob(
                external_id=f"wd_{tenant}_{job_id}",
                source="workday",
                title=title,
                company=company_name,
                location=str(location_data),
                country="CL",
                modality=None,
                description=jp.get("jobDescription") or title,
                apply_link=f"{base_url}{external_path}" if external_path else None,
                skills=extract_skills_from_content(title),
                seniority=detect_seniority(title, ""),
                posted_at=jp.get("postedOn"),
            ))

        if normalized:
            self.log(f"{company_name}: {len(normalized)} jobs")
        return normalized

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        self.log(f"Fetching from {len(WORKDAY_COMPANIES)} companies...")
        all_jobs = []

        async with aiohttp.ClientSession() as session:
            for company in WORKDAY_COMPANIES:
                result = await self._fetch_company_jobs(session, company)
                all_jobs.extend(result)
                await asyncio.sleep(self.rate_limit_seconds)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
