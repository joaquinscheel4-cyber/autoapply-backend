"""
Apollo.io integration for finding recruiter/HR contacts at Chilean companies.
Uses the people search API with HR-specific titles filtered to Chile.
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")
APOLLO_URL = "https://api.apollo.io/api/v1/mixed_people/search"

HR_TITLES = [
    "recruiter",
    "talent acquisition",
    "recursos humanos",
    "rrhh",
    "people",
    "selección",
    "seleccion",
    "head of people",
    "hr manager",
    "human resources",
    "talent",
    "people & culture",
    "people and culture",
]

# Apollo returns these statuses when the email is real and deliverable
VALID_EMAIL_STATUSES = {"verified", "likely to engage", "email_not_found", "unavailable", ""}


async def search_recruiter(company_name: str) -> dict | None:
    """
    Search Apollo.io for a recruiter/HR contact at the given company in Chile.

    Returns:
        {"name": str, "email": str, "title": str, "company": str}  or  None
    """
    if not APOLLO_API_KEY:
        logger.warning("APOLLO_API_KEY not set — skipping Apollo search")
        return None

    if not company_name or not company_name.strip():
        return None

    payload = {
        "api_key": APOLLO_API_KEY,
        "q_organization_name": company_name.strip(),
        "person_titles": HR_TITLES,
        "person_locations": ["Chile"],
        "page": 1,
        "per_page": 5,
    }

    try:
        logger.info(f"Apollo: searching recruiter at '{company_name}'")
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                APOLLO_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
            )

        if resp.status_code == 429:
            logger.warning("Apollo: rate limit hit")
            return None

        if resp.status_code != 200:
            logger.error(f"Apollo API error {resp.status_code}: {resp.text[:300]}")
            return None

        data = resp.json()
        people = data.get("people", [])
        logger.info(f"Apollo: {len(people)} contacts found for '{company_name}'")

        for person in people:
            email = person.get("email") or ""

            # Skip placeholder emails Apollo returns when the real one isn't revealed
            if not email or email.startswith("email_not") or "@" not in email:
                logger.debug(f"Apollo: skipping contact with no email — {person.get('name', '')}")
                continue

            email_status = person.get("email_status") or ""
            if email_status not in VALID_EMAIL_STATUSES:
                logger.debug(f"Apollo: skipping {email} (status: {email_status})")
                continue

            first = person.get("first_name") or ""
            last = person.get("last_name") or ""
            name = f"{first} {last}".strip() or None
            title = person.get("title") or person.get("headline") or None
            org = (person.get("organization") or {}).get("name") or company_name

            logger.info(f"Apollo: found {name} <{email}> — {title} @ {org}")
            return {"name": name, "email": email, "title": title, "company": org}

        logger.info(f"Apollo: no contacts with verified email for '{company_name}'")

    except httpx.TimeoutException:
        logger.error(f"Apollo: timeout searching '{company_name}'")
    except Exception as e:
        logger.error(f"Apollo: unexpected error for '{company_name}': {e}")

    return None
