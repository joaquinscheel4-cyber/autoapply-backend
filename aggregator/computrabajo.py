"""
Computrabajo.cl scraper.
Largest job board in Chile by volume. Uses HTML scraping with JSON-LD extraction.
"""
import asyncio
import re
import json
import aiohttp
from .base import BaseConnector, NormalizedJob
from .companies_chile import COMPUTRABAJO_ROLE_SLUGS
from .greenhouse import extract_skills_from_content, detect_seniority

BASE_URL = "https://www.computrabajo.cl"
DETAIL_BASE = "https://cl.computrabajo.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def extract_job_urls_from_html(html: str) -> list[str]:
    """Extract offer URLs from the listing page via JSON-LD ItemList."""
    urls = []
    for m in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    ):
        try:
            d = json.loads(m.strip())
            graph = d.get("@graph", []) if isinstance(d, dict) else []
            for item in graph:
                if item.get("@type") == "ItemList":
                    for entry in item.get("itemListElement", []):
                        url = entry.get("url")
                        if url:
                            urls.append(url)
        except Exception:
            pass

    # Fallback: regex link extraction
    if not urls:
        for href in re.findall(r'href="(/ofertas-de-trabajo/oferta-[^"]+)"', html):
            urls.append(f"{DETAIL_BASE}{href}")

    return list(dict.fromkeys(urls))  # deduplicate preserving order


def parse_job_detail(html: str, url: str) -> NormalizedJob | None:
    """Parse a job detail page and return a NormalizedJob."""

    # Title
    title_m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if not title_m:
        return None
    title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
    if not title:
        return None

    # Company — from hiringOrganization JSON-LD or visible text
    company = "Empresa confidencial"
    for m in re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html, re.DOTALL
    ):
        try:
            d = json.loads(m.strip())
            if isinstance(d, list):
                d = d[0]
            org = d.get("hiringOrganization") or {}
            if org.get("name"):
                company = org["name"]
                break
        except Exception:
            pass

    if company == "Empresa confidencial":
        # Look for company name in a span/div near the title
        co_m = re.search(
            r'<[a-z]+[^>]*class="[^"]*(?:fs16|company|empresa)[^"]*"[^>]*>([^<]+)',
            html, re.I
        )
        if co_m:
            candidate = co_m.group(1).strip()
            # Ignore navigation/placeholder text
            if candidate and candidate.lower() not in ("buscar empresas", "empresas", "ver empresa"):
                company = candidate

    # Extract from the URL text pattern: "empresa-X-en-city"
    if company == "Empresa confidencial":
        url_m = re.search(r'trabajo-de-[^-]+-(?:en-[^-]+-)?([a-z0-9-]+)-[A-F0-9]{32}', url, re.I)
        # Also try to find company in the page subtitle
        sub_m = re.search(r'<p[^>]*class="[^"]*fs16[^"]*"[^>]*>([^<]{3,60})</p>', html)
        if sub_m:
            candidate = sub_m.group(1).strip()
            if candidate and not any(bad in candidate.lower() for bad in
                ["buscar", "trabajo", "empleos", "postulaciones", "computrabajo"]):
                company = candidate

    # Description — find the longest raw text block
    texts = re.findall(r'<[^>]+>([^<]{80,3000})<', html)
    description = ""
    if texts:
        best = max(texts, key=len)
        # Make sure it's not script/style content
        if not any(k in best[:50] for k in ["function", "window.", "var ", ".css"]):
            description = best.strip()

    # Location
    location = "Chile"
    loc_m = re.search(r'Abenis\s*[-–]\s*([^<\n]{3,60})', html)
    if not loc_m:
        loc_m = re.search(
            r'<[^>]*class="[^"]*(?:location|ciudad|ubicacion)[^"]*"[^>]*>([^<]{3,60})',
            html, re.I
        )
    if loc_m:
        location = loc_m.group(1).strip()

    # Modality
    html_lower = html.lower()
    modality = None
    if "teletrabajo" in html_lower or "trabajo remoto" in html_lower or "100% remoto" in html_lower:
        modality = "remote"
    elif "híbrido" in html_lower or "hibrido" in html_lower:
        modality = "hybrid"
    elif "presencial" in html_lower:
        modality = "presencial"

    # External ID from URL hash
    id_m = re.search(r'([A-F0-9]{32})', url, re.I)
    external_id = f"ct_{id_m.group(1)}" if id_m else f"ct_{abs(hash(url))}"

    return NormalizedJob(
        external_id=external_id,
        source="computrabajo",
        title=title,
        company=company,
        location=location,
        country="CL",
        modality=modality,
        description=description[:3000],
        apply_link=url,
        skills=extract_skills_from_content(description),
        seniority=detect_seniority(title, description),
    )


class ComputrabajoConnector(BaseConnector):
    name = "computrabajo"
    rate_limit_seconds = 0.3

    def __init__(self, max_per_role: int = 10, roles_to_fetch: int = 10):
        self.max_per_role = max_per_role
        self.roles_to_fetch = roles_to_fetch

    async def _fetch_listing(
        self, session: aiohttp.ClientSession, slug: str
    ) -> list[str]:
        url = f"{BASE_URL}/trabajo-de-{slug}"
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                return extract_job_urls_from_html(html)
        except Exception as e:
            self.log(f"Listing error for {slug}: {e}")
            return []

    async def _fetch_detail(
        self, session: aiohttp.ClientSession, url: str
    ) -> NormalizedJob | None:
        try:
            async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as resp:
                if resp.status != 200:
                    return None
                html = await resp.text()
                return parse_job_detail(html, url)
        except Exception as e:
            self.log(f"Detail error {url}: {e}")
            return None

    async def fetch_jobs(self, roles: list[str]) -> list[NormalizedJob]:
        """
        Fetch jobs for user's target roles + a broad set of popular roles.
        roles: user's specific target roles (e.g. ["desarrollador fullstack"])
        """
        # Build role slugs: from user roles + popular slugs
        def to_slug(role: str) -> str:
            import unicodedata
            slug = role.lower().strip().replace(" ", "-")
            slug = unicodedata.normalize("NFD", slug)
            slug = re.sub(r'[\u0300-\u036f]', '', slug)
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            return slug

        user_slugs = [to_slug(r) for r in roles]
        popular_slugs = COMPUTRABAJO_ROLE_SLUGS[:self.roles_to_fetch]
        all_slugs = list(dict.fromkeys(user_slugs + popular_slugs))

        self.log(f"Fetching {len(all_slugs)} role listings...")
        all_detail_urls: list[str] = []

        async with aiohttp.ClientSession() as session:
            # Fetch all listings concurrently
            listing_tasks = [self._fetch_listing(session, slug) for slug in all_slugs]
            listing_results = await asyncio.gather(*listing_tasks, return_exceptions=True)

            for result in listing_results:
                if isinstance(result, list):
                    all_detail_urls.extend(result[:self.max_per_role])

            # Deduplicate
            all_detail_urls = list(dict.fromkeys(all_detail_urls))
            self.log(f"Fetching {len(all_detail_urls)} job details...")

            # Fetch details in batches of 15 to avoid overwhelming the server
            batch_size = 15
            all_jobs: list[NormalizedJob] = []

            for i in range(0, len(all_detail_urls), batch_size):
                batch = all_detail_urls[i:i + batch_size]
                detail_tasks = [self._fetch_detail(session, url) for url in batch]
                detail_results = await asyncio.gather(*detail_tasks, return_exceptions=True)

                for result in detail_results:
                    if isinstance(result, NormalizedJob):
                        all_jobs.append(result)

                if i + batch_size < len(all_detail_urls):
                    await asyncio.sleep(self.rate_limit_seconds)

        self.log(f"Total: {len(all_jobs)} jobs scraped")
        return all_jobs
