"""
Fetches recruiter emails from Hunter.io for top 10 companies
and updates existing jobs in Supabase with apply_email.

Run once: python scripts/fetch_recruiter_emails.py
"""
import asyncio
import httpx
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregator.storage import get_client

HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY", "efc795df3dcd6dfc91cf176bc0955eeabe671676")

TOP_COMPANIES = [
    ("Falabella", "falabella.com"),
    ("Buk", "buk.cl"),
    ("Fintual", "fintual.cl"),
    ("Betterfly", "betterfly.com"),
    ("Xepelin", "xepelin.com"),
    ("Houm", "houm.com"),
    ("GetJusto", "getjusto.com"),
    ("Kushki", "kushki.com"),
    ("Mercado Libre", "mercadolibre.com"),
    ("Rappi", "rappi.com"),
]

HR_KEYWORDS = ["recruit", "hr", "people", "talent", "career", "job",
               "rrhh", "seleccion", "reclutamiento", "empleo"]


async def find_email(company: str, domain: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "type": "generic", "api_key": HUNTER_API_KEY, "limit": 10},
            )
        if resp.status_code != 200:
            print(f"  [{company}] Error Hunter: {resp.status_code}")
            return None

        emails = resp.json().get("data", {}).get("emails", [])
        # Prefer HR emails
        for e in emails:
            if any(kw in e.get("value", "").lower() for kw in HR_KEYWORDS):
                return e["value"]
        # Fallback: highest confidence
        for e in sorted(emails, key=lambda x: x.get("confidence", 0), reverse=True):
            if e.get("confidence", 0) >= 50:
                return e["value"]
    except Exception as ex:
        print(f"  [{company}] Exception: {ex}")
    return None


async def main():
    supabase = get_client()
    results = []

    for company, domain in TOP_COMPANIES:
        print(f"Searching {company} ({domain})...")
        email = await find_email(company, domain)
        if email:
            print(f"  ✅ Found: {email}")
            results.append((company, domain, email))

            # Update all jobs from this company that have no apply_email
            try:
                supabase.table("jobs") \
                    .update({"apply_email": email}) \
                    .ilike("company", f"%{company}%") \
                    .is_("apply_email", "null") \
                    .execute()
                print(f"  📝 Updated jobs for {company}")
            except Exception as e:
                print(f"  ⚠️ Supabase update error: {e}")
        else:
            print(f"  ❌ No email found")

        await asyncio.sleep(1)  # Rate limit

    print("\n=== RESULTS ===")
    for company, domain, email in results:
        print(f"{company}: {email}")
    print(f"\nTotal found: {len(results)}/{len(TOP_COMPANIES)}")


if __name__ == "__main__":
    asyncio.run(main())
