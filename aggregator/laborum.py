"""
Laborum.cl scraper.
Second-largest job board in Chile. Uses JSON API endpoint.
"""
import asyncio
import aiohttp
import re
import json
from .base import BaseConnector, NormalizedJob
from .greenhouse import extract_skills_from_content, detect_seniority

BASE_URL = "https://www.laborum.cl"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "es-CL,es;q=0.9",
}

LABORUM_ROLE_QUERIES = [
    "desarrollador", "ingeniero software", "data analyst",
    "product manager", "diseñador ux", "devops",
    "contador", "recursos humanos", "marketing digital",
    "ingeniero civil", "medico", "enfermero", "abogado",
]


class LaborumConnector(BaseConnector):
    name = "laborum"
    rate_limit_seconds = 0.5

    async def _search_jobs(
        self, session: aiohttp.ClientSession, query: str
    ) -> list[NormalizedJob]:
        """Search jobs using Laborum's internal API."""
        # Laborum exposes a JSON API used by its own frontend
        api_url = (
            f"{BASE_URL}/api/v2/aviso/search"
            f"?q={query.replace(' ', '+')}"
            f"&country=CL&page=1&limit=20"
        )

        try:
            async with session.get(
                api_url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return self._parse_api_response(data)
        except Exception:
            pass

        # Fallback: scrape HTML listing
        return await self._scrape_listing(session, query)

    def _parse_api_response(self, data: dict) -> list[NormalizedJob]:
        jobs = data.get("avisos") or data.get("results") or data.get("data") or []
        normalized = []

        for j in jobs:
            title = j.get("titulo") or j.get("title") or ""
            if not title:
                continue

            company = (
                j.get("empresa", {}).get("nombre") or
                j.get("company") or
                j.get("empresa") or
                "Empresa confidencial"
            )
            if isinstance(company, dict):
                company = company.get("nombre") or "Empresa confidencial"

            location = (
                j.get("ciudad", {}).get("nombre") or
                j.get("location") or
                "Santiago"
            )
            if isinstance(location, dict):
                location = location.get("nombre") or "Santiago"

            description = j.get("descripcion") or j.get("description") or ""
            job_id = str(j.get("id") or j.get("slug") or abs(hash(title + str(company))))
            link = j.get("url") or f"{BASE_URL}/empleo/{job_id}"

            remote = j.get("modalidad_trabajo") or j.get("workModality") or ""
            if isinstance(remote, dict):
                remote = remote.get("nombre") or ""
            remote_str = str(remote).lower()

            if "remoto" in remote_str or "teletrabajo" in remote_str:
                modality = "remote"
            elif "híbrido" in remote_str or "hibrido" in remote_str:
                modality = "hybrid"
            else:
                modality = "presencial" if remote_str else None

            normalized.append(NormalizedJob(
                external_id=f"lab_{job_id}",
                source="laborum",
                title=title,
                company=str(company),
                location=str(location),
                country="CL",
                modality=modality,
                description=description[:3000],
                apply_link=link if link.startswith("http") else f"{BASE_URL}{link}",
                skills=extract_skills_from_content(description),
                seniority=detect_seniority(title, description),
                posted_at=j.get("fecha_publicacion") or j.get("publishedAt"),
            ))

        return normalized

    async def _scrape_listing(
        self, session: aiohttp.ClientSession, query: str
    ) -> list[NormalizedJob]:
        """Fallback: scrape the HTML listing page."""
        url = f"{BASE_URL}/empleos/{query.replace(' ', '-')}"
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)
            ) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

                # Try to find __NEXT_DATA__ or similar JSON injection
                m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
                if m:
                    try:
                        data = json.loads(m.group(1))
                        # Navigate to the jobs array in Next.js page props
                        props = data.get("props", {}).get("pageProps", {})
                        jobs = (
                            props.get("avisos") or
                            props.get("jobs") or
                            props.get("results") or
                            []
                        )
                        if jobs:
                            return self._parse_api_response({"avisos": jobs})
                    except Exception:
                        pass
        except Exception as e:
            self.log(f"Scrape error for {query}: {e}")

        return []

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        all_queries = list(dict.fromkeys(
            [r.lower() for r in roles] + LABORUM_ROLE_QUERIES
        ))[:15]

        self.log(f"Searching {len(all_queries)} queries...")
        all_jobs: list[NormalizedJob] = []
        seen_ids: set[str] = set()

        async with aiohttp.ClientSession() as session:
            tasks = [self._search_jobs(session, q) for q in all_queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                for job in result:
                    if job.external_id not in seen_ids:
                        seen_ids.add(job.external_id)
                        all_jobs.append(job)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
