"""
Master list of Chilean companies mapped to their ATS system.
All industries included — not just tech.
"""

# ── Greenhouse ─────────────────────────────────────────────────────────────
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
    {"slug": "rappi", "name": "Rappi"},
    {"slug": "conekta", "name": "Conekta"},
    {"slug": "kavak", "name": "Kavak"},
    {"slug": "clip", "name": "Clip"},
    {"slug": "platzi", "name": "Platzi"},
    {"slug": "globant", "name": "Globant"},
    {"slug": "endava", "name": "Endava"},
    {"slug": "wizeline", "name": "Wizeline"},
    {"slug": "ioet", "name": "ioet"},
    {"slug": "encora", "name": "Encora"},
    {"slug": "abstracta", "name": "Abstracta"},
    # International with Chile presence
    {"slug": "cloudflare", "name": "Cloudflare"},
    {"slug": "gitlab", "name": "GitLab"},
    {"slug": "hashicorp", "name": "HashiCorp"},
    {"slug": "twilio", "name": "Twilio"},
    {"slug": "deel", "name": "Deel"},
    {"slug": "remote", "name": "Remote"},
    {"slug": "lemonadestand", "name": "Lemon"},
    # Consultoría / Servicios
    {"slug": "accenture", "name": "Accenture"},
    {"slug": "thoughtworks", "name": "Thoughtworks"},
    {"slug": "ey", "name": "EY"},
    # Salud
    {"slug": "biontech", "name": "BioNTech"},
    {"slug": "life360", "name": "Life360"},
]

# ── Lever ──────────────────────────────────────────────────────────────────
LEVER_COMPANIES = [
    # Chilean startups
    {"slug": "fintual", "name": "Fintual"},
    {"slug": "betterfly", "name": "Betterfly"},
    {"slug": "cheki-chile", "name": "Cheki Chile"},
    {"slug": "jooycar", "name": "JooyCar"},
    {"slug": "broota", "name": "Broota"},
    {"slug": "houm", "name": "Houm"},
    {"slug": "hapi", "name": "Hapi"},
    {"slug": "chipax", "name": "Chipax"},
    {"slug": "simple", "name": "Simple"},
    {"slug": "osana", "name": "Osana"},
    # Tech companies with Chile presence
    {"slug": "cornershop", "name": "Cornershop"},
    {"slug": "notco", "name": "NotCo"},
    {"slug": "xcala", "name": "Xcala"},
    # LATAM tech
    {"slug": "liftoff", "name": "Liftoff"},
    {"slug": "bitso", "name": "Bitso"},
    {"slug": "konfio", "name": "Konfio"},
    {"slug": "menta-network", "name": "Menta Network"},
    {"slug": "aumenta", "name": "Aumenta"},
    {"slug": "getjusto", "name": "Justo"},
    {"slug": "adyen", "name": "Adyen"},
    # Retail / Consumo
    {"slug": "pedidosya", "name": "PedidosYa"},
    {"slug": "ifood", "name": "iFood"},
]

# ── SmartRecruiters ────────────────────────────────────────────────────────
SMARTRECRUITERS_COMPANIES = [
    # Retail grande
    {"slug": "Falabella", "name": "Falabella"},
    {"slug": "CencosudSA", "name": "Cencosud"},
    {"slug": "Ripley", "name": "Ripley"},
    # Banca
    {"slug": "BancoSantanderChile", "name": "Banco Santander Chile"},
    {"slug": "Itau", "name": "Itaú Chile"},
    # Salud
    {"slug": "EmpresasBanmedica", "name": "Banmédica"},
    {"slug": "RedSalud", "name": "RedSalud"},
    # Telecom
    {"slug": "Entel", "name": "Entel"},
    {"slug": "WOM", "name": "WOM"},
    # Logística
    {"slug": "DHL", "name": "DHL"},
    {"slug": "Fedex", "name": "FedEx"},
    # Consumo masivo
    {"slug": "Nestl", "name": "Nestlé Chile"},
    {"slug": "UnileverChile", "name": "Unilever Chile"},
    {"slug": "CocaCola", "name": "Coca-Cola Andina"},
    # Construcción
    {"slug": "Sodimac", "name": "Sodimac"},
    # Seguros
    {"slug": "MetLifeChile", "name": "MetLife Chile"},
    {"slug": "MAPFREChile", "name": "MAPFRE Chile"},
]

# ── Workday ────────────────────────────────────────────────────────────────
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
    {
        "name": "LATAM Airlines",
        "tenant": "latam",
        "board": "External",
        "base_url": "https://latam.wd3.myworkdayjobs.com"
    },
    {
        "name": "Walmart Chile",
        "tenant": "walmart",
        "board": "External",
        "base_url": "https://walmart.wd5.myworkdayjobs.com"
    },
    {
        "name": "ABB Chile",
        "tenant": "abb",
        "board": "External",
        "base_url": "https://abb.wd3.myworkdayjobs.com"
    },
    {
        "name": "IBM Chile",
        "tenant": "ibm",
        "board": "External",
        "base_url": "https://ibm.wd3.myworkdayjobs.com"
    },
]

# ── Computrabajo role slugs — todas las industrias ─────────────────────────
COMPUTRABAJO_ROLE_SLUGS = [
    # Tech
    "desarrollador", "desarrollador-web", "desarrollador-backend",
    "desarrollador-frontend", "analista-de-datos", "data-scientist",
    "ingeniero-de-software", "devops", "scrum-master", "product-manager",
    "ux-designer", "ciberseguridad", "inteligencia-artificial",
    # Negocios / Admin
    "administrador-de-empresas", "gerente-comercial", "ejecutivo-comercial",
    "analista-financiero", "contador", "auditor", "economista",
    "recursos-humanos", "reclutador", "asistente-administrativo",
    "secretaria", "recepcionista",
    # Marketing / Ventas
    "marketing-digital", "community-manager", "ejecutivo-de-ventas",
    "vendedor", "publicidad", "relaciones-publicas", "periodista",
    # Ingeniería / Construcción
    "ingeniero-industrial", "ingeniero-civil", "arquitecto",
    "ingeniero-electrico", "ingeniero-mecanico", "ingeniero-quimico",
    "tecnico-en-electricidad", "maestro-de-obra",
    # Salud
    "medico", "enfermero", "kinesiologo", "psicologo", "nutricionista",
    "tecnico-en-enfermeria", "dentista", "farmaceutico",
    # Educación
    "profesor", "educador", "docente",
    # Legal
    "abogado", "asistente-legal", "compliance",
    # Logística / Operaciones
    "logistica", "supply-chain", "bodeguero", "operario",
    "conductor", "chofer", "repartidor",
    # Minería / Energía
    "mineria", "geólogo", "operador-planta",
    # Gastronomía / Hotelería
    "chef", "cocinero", "mozo", "recepcionista-hotel", "turismo",
    # Diseño
    "diseñador-grafico", "diseñador-ux", "diseñador-industrial",
]
