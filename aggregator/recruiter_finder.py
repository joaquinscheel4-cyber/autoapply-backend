"""
Finds recruiter/HR emails for a company using:
1. Hunter.io domain search (if API key available)
2. Common HR email patterns as fallback
"""
import os
import httpx

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "")

# Company name → domain mapping (same as frontend company-logos)
COMPANY_DOMAINS: dict[str, str] = {
    "mercado libre": "mercadolibre.com", "mercadolibre": "mercadolibre.com",
    "rappi": "rappi.com", "kavak": "kavak.com", "nubank": "nubank.com.br",
    "kushki": "kushki.com", "notco": "notco.com", "xepelin": "xepelin.com",
    "houm": "houm.com", "buk": "buk.cl", "betterfly": "betterfly.com",
    "fintual": "fintual.cl", "cornershop": "cornershopapp.com",
    "getjusto": "getjusto.com", "get justo": "getjusto.com",
    "falabella": "falabella.com", "cencosud": "cencosud.com",
    "ripley": "ripley.cl", "sodimac": "sodimac.com",
    "walmart": "walmart.cl", "lider": "lider.cl",
    "banco santander": "santander.cl", "santander": "santander.cl",
    "banco chile": "bancochile.cl", "bci": "bci.cl",
    "scotiabank": "scotiabank.cl", "banco estado": "bancoestado.cl",
    "itaú": "itau.cl", "itau": "itau.cl",
    "entel": "entel.cl", "movistar": "movistar.cl", "wom": "wom.cl",
    "codelco": "codelco.com", "bhp": "bhp.com",
    "latam": "latam.com", "latam airlines": "latam.com",
    "accenture": "accenture.com", "deloitte": "deloitte.com",
    "pwc": "pwc.com", "kpmg": "kpmg.com",
    "ibm": "ibm.com", "oracle": "oracle.com", "sap": "sap.com",
    "google": "google.com", "microsoft": "microsoft.com",
    "amazon": "amazon.com", "salesforce": "salesforce.com",
    "nestlé": "nestle.com", "nestle": "nestle.com",
    "unilever": "unilever.com", "dhl": "dhl.com",
}

# Common HR email prefixes to try as fallback
HR_PREFIXES = [
    "reclutamiento", "seleccion", "selección", "recruiting",
    "careers", "jobs", "hr", "rrhh", "talento", "people",
    "empleo", "postulaciones",
]


def get_domain_for_company(company: str, apply_link: str = "") -> str | None:
    """Resolve company name → domain."""
    key = company.lower().strip()

    # Direct match
    if key in COMPANY_DOMAINS:
        return COMPANY_DOMAINS[key]

    # Partial match
    for name, domain in COMPANY_DOMAINS.items():
        if name in key or key in name:
            return domain

    # Extract from apply_link if it's a company careers page (not ATS)
    if apply_link:
        import re
        skip = ["greenhouse.io", "lever.co", "workday", "smartrecruiters", "linkedin.com",
                "computrabajo", "laborum", "trabajando.cl", "indeed.com"]
        if not any(s in apply_link for s in skip):
            m = re.search(r"https?://(?:www\.|careers\.|jobs\.)?([^/]+\.[a-z]{2,})", apply_link)
            if m:
                return m.group(1)

    return None


async def hunter_search(domain: str) -> str | None:
    """Use Hunter.io to find the best recruiting email for a domain."""
    if not HUNTER_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={
                    "domain": domain,
                    "type": "generic",  # generic = department/role emails
                    "api_key": HUNTER_API_KEY,
                    "limit": 10,
                },
            )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", {})
        emails = data.get("emails", [])

        # Prefer emails with HR/recruiting keywords
        hr_keywords = ["recruit", "hr", "people", "talent", "career", "job", "rrhh",
                        "seleccion", "reclutamiento", "empleo"]
        for email_obj in emails:
            addr = email_obj.get("value", "").lower()
            if any(kw in addr for kw in hr_keywords):
                return email_obj["value"]

        # Return first verified email if no HR-specific one found
        for email_obj in emails:
            if email_obj.get("confidence", 0) >= 70:
                return email_obj["value"]

    except Exception:
        pass
    return None


async def find_recruiter_email(company: str, apply_link: str = "") -> str | None:
    """
    Main entry point. Returns the best email to send an application to.
    Priority:
    1. Hunter.io domain search
    2. Common HR email patterns
    """
    domain = get_domain_for_company(company, apply_link)
    if not domain:
        return None

    # 1. Hunter.io
    email = await hunter_search(domain)
    if email:
        return email

    # 2. Common patterns — return the most likely one
    return f"reclutamiento@{domain}"
