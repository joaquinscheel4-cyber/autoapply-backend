def filter_jobs(jobs, profile):
    preferences = profile.get("job_preferences", {})

    target_roles = [r.lower() for r in preferences.get("target_roles", [])]
    excluded_roles = [r.lower() for r in preferences.get("excluded_roles", [])]
    excluded_companies = [c.lower() for c in preferences.get("excluded_companies", [])]
    preferred_locations = [l.lower() for l in preferences.get("preferred_locations", [])]

    filtered = []

    for job in jobs:
        title = job["title"].lower()
        company = job["company"].lower()
        location = job["location"].lower()

        # excluir roles
        if any(excl in title for excl in excluded_roles):
            continue

        # excluir empresas
        if any(excl in company for excl in excluded_companies):
            continue

        # filtrar por roles deseados (si existen)
        if target_roles:
            if not any(role in title for role in target_roles):
                continue

        # filtrar por ubicación (suave)
        if preferred_locations:
            if not any(loc in location for loc in preferred_locations):
                continue

        filtered.append(job)

    return filtered