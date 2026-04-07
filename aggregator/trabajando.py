"""
Trabajando.com scraper — Chile's largest generalist job board.
Uses their internal search API.
"""
import asyncio
import aiohttp
import re
import json
from .base import BaseConnector, NormalizedJob
from .greenhouse import extract_skills_from_content, detect_seniority

BASE_URL = "https://www.trabajando.cl"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9",
    "Referer": "https://www.trabajando.cl/",
}

TRABAJANDO_QUERIES = [
    "desarrollador", "programador", "ingeniero software", "analista datos",
    "contador", "administrador empresas", "recursos humanos", "marketing",
    "ventas", "ejecutivo comercial", "medico", "enfermero", "abogado",
    "ingeniero civil", "arquitecto", "diseñador", "logistica", "operario",
    "profesor", "cocinero", "secretaria", "recepcionista",
]


class TrabajandoConnector(BaseConnector):
    name = "trabajando"
    rate_limit_seconds = 1.0

    async def _search(
        self, session: aiohttp.ClientSession, query: str
    ) -> list[NormalizedJob]:
        url = f"{BASE_URL}/empleos/?q={query.replace(' ', '+')}&pa=1"
        try:
            async with session.get(
                url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

            # Try Next.js __NEXT_DATA__
            m = re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    props = data.get("props", {}).get("pageProps", {})
                    jobs_raw = (
                        props.get("jobs") or props.get("avisos") or
                        props.get("offers") or props.get("results") or []
                    )
                    if jobs_raw:
                        return self._parse(jobs_raw)
                except Exception:
                    pass

            # Try JSON-LD
            matches = re.findall(
                r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
                html, re.DOTALL
            )
            for raw in matches:
                try:
                    obj = json.loads(raw)
                    if obj.get("@type") == "JobPosting":
                        return [self._parse_jsonld(obj)]
                    if obj.get("@type") == "ItemList":
                        items = obj.get("itemListElement", [])
                        result = []
                        for item in items:
                            job = item.get("item") or item
                            if job.get("@type") == "JobPosting":
                                result.append(self._parse_jsonld(job))
                        if result:
                            return result
                except Exception:
                    continue

            # Fallback: extract job cards from HTML
            return self._parse_html(html)

        except Exception as e:
            self.log(f"Error for '{query}': {e}")
            return []

    def _parse(self, jobs_raw: list) -> list[NormalizedJob]:
        normalized = []
        for j in jobs_raw:
            if not isinstance(j, dict):
                continue
            title = j.get("titulo") or j.get("title") or j.get("nombre") or ""
            if not title:
                continue

            company_raw = j.get("empresa") or j.get("company") or {}
            if isinstance(company_raw, dict):
                company = company_raw.get("nombre") or company_raw.get("name") or "Empresa confidencial"
            else:
                company = str(company_raw) or "Empresa confidencial"

            location_raw = j.get("ciudad") or j.get("location") or j.get("region") or {}
            if isinstance(location_raw, dict):
                location = location_raw.get("nombre") or location_raw.get("name") or "Santiago"
            else:
                location = str(location_raw) or "Santiago"

            description = j.get("descripcion") or j.get("description") or ""
            job_id = str(j.get("id") or j.get("slug") or abs(hash(title + company)))
            link = j.get("url") or j.get("link") or f"{BASE_URL}/empleo/{job_id}"
            if not link.startswith("http"):
                link = f"{BASE_URL}{link}"

            modality_raw = str(j.get("modalidad") or j.get("modality") or "").lower()
            if "remoto" in modality_raw or "teletrabajo" in modality_raw:
                modality = "remote"
            elif "híbrido" in modality_raw or "hibrido" in modality_raw:
                modality = "hybrid"
            elif modality_raw:
                modality = "presencial"
            else:
                modality = None

            normalized.append(NormalizedJob(
                external_id=f"trab_{job_id}",
                source="trabajando",
                title=title,
                company=company,
                location=location,
                country="CL",
                modality=modality,
                description=description[:3000],
                apply_link=link,
                skills=extract_skills_from_content(description),
                seniority=detect_seniority(title, description),
                posted_at=j.get("fecha_publicacion") or j.get("publishedAt"),
            ))
        return normalized

    def _parse_jsonld(self, obj: dict) -> NormalizedJob:
        title = obj.get("title") or obj.get("name") or "Sin título"
        company_raw = obj.get("hiringOrganization") or {}
        company = company_raw.get("name") or "Empresa confidencial" if isinstance(company_raw, dict) else str(company_raw)
        location_raw = obj.get("jobLocation") or {}
        if isinstance(location_raw, dict):
            addr = location_raw.get("address") or {}
            location = addr.get("addressLocality") or addr.get("addressRegion") or "Santiago"
        else:
            location = "Santiago"
        description = obj.get("description") or ""
        link = obj.get("url") or obj.get("identifier", {}).get("value") or BASE_URL
        job_id = str(abs(hash(title + company)))

        return NormalizedJob(
            external_id=f"trab_{job_id}",
            source="trabajando",
            title=title,
            company=company,
            location=location,
            country="CL",
            description=description[:3000],
            apply_link=link if link.startswith("http") else f"{BASE_URL}{link}",
            skills=extract_skills_from_content(description),
            seniority=detect_seniority(title, description),
        )

    def _parse_html(self, html: str) -> list[NormalizedJob]:
        """Last resort: regex extract job titles from HTML."""
        results = []
        # Look for job card patterns
        pattern = re.compile(
            r'href="(/empleo/[^"]+)"[^>]*>.*?<[^>]*class="[^"]*(?:title|titulo)[^"]*"[^>]*>([^<]+)',
            re.DOTALL
        )
        for m in pattern.finditer(html)[:20]:
            link = f"{BASE_URL}{m.group(1)}"
            title = m.group(2).strip()
            if not title:
                continue
            job_id = str(abs(hash(link)))
            results.append(NormalizedJob(
                external_id=f"trab_{job_id}",
                source="trabajando",
                title=title,
                company="Ver oferta",
                location="Chile",
                country="CL",
                apply_link=link,
            ))
        return results

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        queries = list(dict.fromkeys(
            [r.lower() for r in roles] + TRABAJANDO_QUERIES
        ))[:20]

        self.log(f"Searching {len(queries)} queries...")
        all_jobs: list[NormalizedJob] = []
        seen_ids: set[str] = set()

        async with aiohttp.ClientSession() as session:
            for query in queries:
                results = await self._search(session, query)
                for job in results:
                    if job.external_id not in seen_ids:
                        seen_ids.add(job.external_id)
                        all_jobs.append(job)
                await asyncio.sleep(self.rate_limit_seconds)

        self.log(f"Total: {len(all_jobs)} jobs")
        return all_jobs
