"""
Lever Postings API connector.
No authentication required — completely public.
Docs: https://github.com/lever/lever-api-docs
"""
import asyncio
import aiohttp
from .base import BaseConnector, NormalizedJob
from .companies_chile import LEVER_COMPANIES
from .greenhouse import extract_skills_from_content, detect_seniority


def map_lever_modality(posting: dict) -> str | None:
    commitment = (posting.get("commitment") or "").lower()
    workplaceType = (posting.get("workplaceType") or "").lower()
    location = (posting.get("categories", {}).get("location") or "").lower()
    tags = [t.lower() for t in (posting.get("tags") or [])]

    if workplaceType == "remote" or "remote" in location or "remoto" in location:
        return "remote"
    if workplaceType == "hybrid" or "híbrido" in location or "hybrid" in location:
        return "hybrid"
    if "remote" in tags or "remoto" in tags:
        return "remote"
    if commitment in ("contract", "internship"):
        return None
    return "presencial"


def map_lever_seniority(posting: dict) -> str | None:
    title = posting.get("text") or ""
    description = posting.get("descriptionPlain") or ""
    lists = " ".join(
        item.get("content", "") for item in (posting.get("lists") or [])
    )
    return detect_seniority(title, description + " " + lists)


class LeverConnector(BaseConnector):
    name = "lever"
    rate_limit_seconds = 0.3

    async def _fetch_company_jobs(
        self, session: aiohttp.ClientSession, company: dict
    ) -> list[NormalizedJob]:
        slug = company["slug"]
        company_name = company["name"]
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 404:
                    return []
                if resp.status != 200:
                    self.log(f"HTTP {resp.status} for {slug}")
                    return []
                data = await resp.json()

        except Exception as e:
            self.log(f"Error fetching {slug}: {e}")
            return []

        if not isinstance(data, list):
            return []

        normalized = []
        for posting in data:
            title = posting.get("text") or ""
            description = posting.get("descriptionPlain") or ""
            # Concatenate all list items as part of description
            for lst in (posting.get("lists") or []):
                description += "\n" + (lst.get("content") or "")

            location = (
                (posting.get("categories") or {}).get("location")
                or "Chile"
            )

            normalized.append(NormalizedJob(
                external_id=f"lever_{posting['id']}",
                source="lever",
                title=title,
                company=company_name,
                location=location,
                country="CL",
                modality=map_lever_modality(posting),
                description=description[:3000],
                apply_link=posting.get("hostedUrl") or posting.get("applyUrl"),
                skills=extract_skills_from_content(description),
                seniority=map_lever_seniority(posting),
                posted_at=None,
            ))

        if normalized:
            self.log(f"{company_name}: {len(normalized)} jobs")
        return normalized

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        self.log(f"Fetching from {len(LEVER_COMPANIES)} companies...")
        all_jobs = []

        async with aiohttp.ClientSession() as session:
            tasks = [
                self._fetch_company_jobs(session, company)
                for company in LEVER_COMPANIES
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
