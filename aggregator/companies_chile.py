"""
Master list of Chilean companies mapped to their ATS system.
Extend this file to add more companies.
"""

# Companies using Greenhouse Job Board API
# API: https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true
GREENHOUSE_COMPANIES = [
    # Fintech / Startups Chile
    {"slug": "nubank", "name": "Nubank"},
    {"slug": "kushki", "name": "Kushki"},
    {"slug": "xepelin", "name": "Xepelin"},
    {"slug": "aptuno", "name": "Aptuno"},
    {"slug": "u-planner", "name": "U-Planner"},
    {"slug": "buk-hr", "name": "Buk"},
    # Tech LATAM
    {"slug": "mercadolibre", "name": "Mercado Libre"},
    {"slug": "conekta", "name": "Conekta"},
    {"slug": "kavak", "name": "Kavak"},
    {"slug": "clip", "name": "Clip"},
    {"slug": "platzi", "name": "Platzi"},
    {"slug": "globant", "name": "Globant"},
    {"slug": "endava", "name": "Endava"},
    {"slug": "wizeline", "name": "Wizeline"},
    {"slug": "ioet", "name": "ioet"},
    # International with Chile offices
    {"slug": "cloudflare", "name": "Cloudflare"},
    {"slug": "gitlab", "name": "GitLab"},
    {"slug": "hashicorp", "name": "HashiCorp"},
    {"slug": "twilio", "name": "Twilio"},
]

# Companies using Lever Postings API
# API: https://api.lever.co/v0/postings/{slug}?mode=json
LEVER_COMPANIES = [
    # Chilean startups
    {"slug": "fintual", "name": "Fintual"},
    {"slug": "betterfly", "name": "Betterfly"},
    {"slug": "cheki-chile", "name": "Cheki Chile"},
    {"slug": "jooycar", "name": "JooyCar"},
    {"slug": "broota", "name": "Broota"},
    # Tech companies with Chile presence
    {"slug": "cornershop", "name": "Cornershop"},
    {"slug": "notco", "name": "NotCo"},
    {"slug": "xcala", "name": "Xcala"},
    {"slug": "habitat-for-humanity", "name": "Habitat Chile"},
    # LATAM tech
    {"slug": "liftoff", "name": "Liftoff"},
    {"slug": "quixy", "name": "Quixy"},
    {"slug": "encora", "name": "Encora"},
    {"slug": "bitso", "name": "Bitso"},
    {"slug": "konfio", "name": "Konfio"},
]

# Companies using SmartRecruiters
# API: https://api.smartrecruiters.com/v1/companies/{id}/postings
SMARTRECRUITERS_COMPANIES = [
    {"slug": "Falabella", "name": "Falabella"},
    {"slug": "CencosudSA", "name": "Cencosud"},
    {"slug": "BancoSantanderChile", "name": "Banco Santander Chile"},
    {"slug": "EmpresasBanmedica", "name": "Banmédica"},
    {"slug": "Entel", "name": "Entel"},
]

# Companies with public Workday JSON APIs
# Format: https://{company}.wd1.myworkdayjobs.com/wday/cxs/{company}/{board}/jobs
WORKDAY_COMPANIES = [
    {
        "name": "BHP",
        "tenant": "bhp",
        "board": "External_Career_Site",
        "base_url": "https://bhp.wd3.myworkdayjobs.com"
    },
    {
        "name": "Codelco",
        "tenant": "codelco",
        "board": "CodelcoExternal",
        "base_url": "https://codelco.wd1.myworkdayjobs.com"
    },
    {
        "name": "Scotiabank Chile",
        "tenant": "scotiabank",
        "board": "External",
        "base_url": "https://scotiabank.wd3.myworkdayjobs.com"
    },
    {
        "name": "Enel Chile",
        "tenant": "enel",
        "board": "External",
        "base_url": "https://enel.wd3.myworkdayjobs.com"
    },
]

# Computrabajo role slugs to search
# These map to: https://www.computrabajo.cl/trabajo-de-{slug}
COMPUTRABAJO_ROLE_SLUGS = [
    "desarrollador",
    "desarrollador-web",
    "desarrollador-backend",
    "desarrollador-frontend",
    "analista-de-datos",
    "data-scientist",
    "ingeniero-de-software",
    "ingeniero-de-sistemas",
    "devops",
    "scrum-master",
    "product-manager",
    "ux-designer",
    "marketing-digital",
    "contador",
    "ingeniero-industrial",
    "administrador-de-empresas",
    "recursos-humanos",
    "ventas",
    "finanzas",
    "mineria",
    "ingeniero-civil",
    "arquitecto",
    "medico",
    "enfermero",
    "abogado",
    "periodista",
    "diseñador-grafico",
    "logistica",
    "supply-chain",
    "gerente-comercial",
]
