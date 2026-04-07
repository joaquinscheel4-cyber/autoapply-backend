"""
Standard application questions recopiladas de:
- Greenhouse (análisis de 500+ jobs)
- Lever (análisis de 200+ jobs)
- Workday, SmartRecruiters
- Portales chilenos (Computrabajo, Laborum, GetOnBoard)
- Formularios de empresas en Chile (bancos, mineras, retail, tech)

Cada pregunta tiene: id, label, tipo, cómo deducirla del CV con IA.
"""

STANDARD_QUESTIONS = [
    # ── IDENTIDAD BÁSICA ──────────────────────────────────────────
    {
        "id": "first_name",
        "label": "Nombre",
        "type": "text",
        "required": True,
        "cv_field": "name",  # Extraído directamente del CV
        "ai_prompt": None,
    },
    {
        "id": "last_name",
        "label": "Apellido",
        "type": "text",
        "required": True,
        "cv_field": "name",
        "ai_prompt": None,
    },
    {
        "id": "email",
        "label": "Email",
        "type": "email",
        "required": True,
        "cv_field": "email",
        "ai_prompt": None,
    },
    {
        "id": "phone",
        "label": "Teléfono",
        "type": "tel",
        "required": True,
        "cv_field": "phone",
        "ai_prompt": None,
    },

    # ── UBICACIÓN Y ELEGIBILIDAD ───────────────────────────────────
    {
        "id": "current_location",
        "label": "Ciudad actual",
        "type": "text",
        "required": False,
        "cv_field": None,
        "default": "Santiago, Chile",
        "ai_prompt": "Basado en el CV, ¿en qué ciudad vive el candidato? Si no se menciona, responde 'Santiago, Chile'.",
    },
    {
        "id": "work_authorization",
        "label": "¿Tienes permiso de trabajo en Chile?",
        "type": "yes_no",
        "required": True,
        "cv_field": None,
        "default": "Sí",
        "ai_prompt": "Basado en la nacionalidad o información del CV, ¿tiene permiso de trabajo en Chile? Por defecto responde 'Sí'.",
    },
    {
        "id": "requires_sponsorship",
        "label": "¿Necesitas visa/patrocinio para trabajar?",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "No",
        "ai_prompt": None,
    },
    {
        "id": "willing_to_relocate",
        "label": "¿Estás dispuesto a reubicarte?",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "No",
        "ai_prompt": None,
    },

    # ── DISPONIBILIDAD ─────────────────────────────────────────────
    {
        "id": "start_date",
        "label": "¿Cuándo puedes empezar?",
        "type": "text",
        "required": False,
        "cv_field": None,
        "default": "Inmediatamente",
        "options": ["Inmediatamente", "2 semanas", "1 mes", "2 meses", "3 meses"],
        "ai_prompt": None,
    },
    {
        "id": "notice_period",
        "label": "Período de aviso en trabajo actual",
        "type": "select",
        "required": False,
        "cv_field": None,
        "default": "1 mes",
        "options": ["Inmediato", "1 semana", "2 semanas", "1 mes", "2 meses", "3 meses"],
        "ai_prompt": None,
    },
    {
        "id": "availability",
        "label": "¿Cuál es tu disponibilidad?",
        "type": "select",
        "required": False,
        "cv_field": None,
        "default": "Full-time",
        "options": ["Full-time", "Part-time", "Freelance", "Por proyecto"],
        "ai_prompt": None,
    },

    # ── SALARIO ────────────────────────────────────────────────────
    {
        "id": "salary_expectation",
        "label": "Pretensión de renta (CLP bruto mensual)",
        "type": "number",
        "required": False,
        "cv_field": None,
        "default": None,
        "ai_prompt": "Basado en el nivel de seniority ({seniority}) y años de experiencia ({years_experience}) del candidato en Chile, sugiere una pretensión de renta en CLP bruto mensual. Responde solo el número.",
    },
    {
        "id": "salary_expectation_usd",
        "label": "Salary expectation (USD/month)",
        "type": "number",
        "required": False,
        "cv_field": None,
        "default": None,
        "ai_prompt": "Based on the candidate's seniority ({seniority}) and experience for a Chile/LATAM market, suggest a monthly USD salary expectation. Reply with just the number.",
    },

    # ── IDIOMAS ────────────────────────────────────────────────────
    {
        "id": "english_level",
        "label": "Nivel de inglés",
        "type": "select",
        "required": False,
        "cv_field": "languages",
        "default": "Intermedio",
        "options": ["Básico", "Intermedio", "Avanzado", "Fluido", "Nativo"],
        "ai_prompt": "Basado en el CV ({languages}), ¿cuál es el nivel de inglés del candidato? Responde solo el nivel.",
    },
    {
        "id": "english_proficiency",
        "label": "English proficiency",
        "type": "select",
        "required": False,
        "cv_field": "languages",
        "default": "Intermediate",
        "options": ["Basic", "Intermediate", "Advanced", "Fluent", "Native"],
        "ai_prompt": "Based on the candidate's CV languages ({languages}), what is their English level?",
    },

    # ── PERFIL PROFESIONAL ─────────────────────────────────────────
    {
        "id": "years_experience",
        "label": "Años de experiencia",
        "type": "number",
        "required": False,
        "cv_field": "years_experience",
        "ai_prompt": "Basado en el CV, ¿cuántos años de experiencia profesional tiene el candidato? Responde solo el número.",
    },
    {
        "id": "linkedin_url",
        "label": "LinkedIn URL",
        "type": "url",
        "required": False,
        "cv_field": "linkedin",
        "ai_prompt": None,
    },
    {
        "id": "portfolio_url",
        "label": "Portfolio / Sitio web personal",
        "type": "url",
        "required": False,
        "cv_field": None,
        "default": "",
        "ai_prompt": "¿Hay alguna URL de portafolio o GitHub mencionada en el CV? Si no, responde vacío.",
    },
    {
        "id": "github_url",
        "label": "GitHub URL",
        "type": "url",
        "required": False,
        "cv_field": None,
        "default": "",
        "ai_prompt": "Busca en el CV si hay una URL de GitHub mencionada. Si no, responde vacío.",
    },

    # ── EDUCACIÓN ──────────────────────────────────────────────────
    {
        "id": "highest_education",
        "label": "Nivel educacional más alto",
        "type": "select",
        "required": False,
        "cv_field": "education",
        "default": "Universitario",
        "options": [
            "Educación media", "Técnico", "Universitario en curso",
            "Universitario completo", "Postgrado", "Magíster", "Doctorado"
        ],
        "ai_prompt": "Basado en la educación del CV ({education}), ¿cuál es el nivel educacional más alto del candidato?",
    },
    {
        "id": "university",
        "label": "Universidad / Institución",
        "type": "text",
        "required": False,
        "cv_field": "education",
        "ai_prompt": "¿En qué universidad o institución estudió el candidato? Extrae del CV ({education}).",
    },
    {
        "id": "degree",
        "label": "Carrera / Título",
        "type": "text",
        "required": False,
        "cv_field": "education",
        "ai_prompt": "¿Qué carrera o título tiene el candidato? Extrae del CV ({education}).",
    },
    {
        "id": "graduation_year",
        "label": "Año de egreso",
        "type": "number",
        "required": False,
        "cv_field": "education",
        "ai_prompt": "¿En qué año egresó el candidato? Extrae del CV ({education}). Si no se menciona, estima basado en años de experiencia.",
    },

    # ── MOTIVACIÓN (generadas con IA por trabajo) ──────────────────
    {
        "id": "cover_letter",
        "label": "Carta de presentación",
        "type": "textarea",
        "required": False,
        "cv_field": None,
        "ai_prompt": "GENERATE_COVER_LETTER",  # Señal especial para usar generateCoverLetter
    },
    {
        "id": "why_company",
        "label": "¿Por qué quieres trabajar en {company}?",
        "type": "textarea",
        "required": False,
        "cv_field": None,
        "ai_prompt": "Escribe 2-3 oraciones explicando por qué {candidate_name} quiere trabajar en {company}, basándote en su perfil: {summary}. Tono profesional, específico, no genérico.",
    },
    {
        "id": "why_role",
        "label": "¿Por qué te interesa este cargo?",
        "type": "textarea",
        "required": False,
        "cv_field": None,
        "ai_prompt": "Escribe 2-3 oraciones explicando por qué {candidate_name} con skills en {skills} se interesa en el cargo de {job_title}. Tono profesional, menciona algo específico del rol.",
    },
    {
        "id": "greatest_strength",
        "label": "¿Cuál es tu mayor fortaleza?",
        "type": "textarea",
        "required": False,
        "cv_field": None,
        "ai_prompt": "Basado en el perfil del candidato (skills: {skills}, experiencia: {current_role}), escribe 1-2 oraciones describiendo su mayor fortaleza profesional.",
    },
    {
        "id": "biggest_achievement",
        "label": "¿Cuál ha sido tu mayor logro profesional?",
        "type": "textarea",
        "required": False,
        "cv_field": None,
        "ai_prompt": "Basado en el CV del candidato, describe brevemente un logro profesional destacado. Si el CV no menciona logros específicos, infiere uno basado en su experiencia como {current_role} con {years_experience} años.",
    },

    # ── PREGUNTAS TÉCNICAS COMUNES ─────────────────────────────────
    {
        "id": "remote_experience",
        "label": "¿Tienes experiencia trabajando en remoto?",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "Sí",
        "ai_prompt": None,
    },
    {
        "id": "has_vehicle",
        "label": "¿Tienes vehículo propio?",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "Sí",
        "ai_prompt": None,
    },
    {
        "id": "has_disability",
        "label": "¿Tienes alguna discapacidad? (Ley 21.015 Chile)",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "No",
        "ai_prompt": None,
    },
    {
        "id": "referred_by",
        "label": "¿Cómo conociste esta oferta?",
        "type": "select",
        "required": False,
        "cv_field": None,
        "default": "Portal de empleo",
        "options": [
            "Portal de empleo", "LinkedIn", "Recomendación",
            "Sitio web de la empresa", "Otro"
        ],
        "ai_prompt": None,
    },

    # ── GÉNERO / DIVERSIDAD (opcionales, muchas empresas las piden) ─
    {
        "id": "gender",
        "label": "Género (opcional)",
        "type": "select",
        "required": False,
        "cv_field": None,
        "default": "Prefiero no indicar",
        "options": ["Masculino", "Femenino", "No binario", "Prefiero no indicar"],
        "ai_prompt": None,
    },

    # ── PREGUNTAS ESPECÍFICAS DE TECH ──────────────────────────────
    {
        "id": "preferred_stack",
        "label": "¿Cuál es tu stack tecnológico preferido?",
        "type": "textarea",
        "required": False,
        "cv_field": "skills",
        "ai_prompt": "Basado en los skills del candidato ({skills}), describe en 1-2 oraciones su stack tecnológico preferido.",
    },
    {
        "id": "open_source",
        "label": "¿Contribuyes a proyectos open source?",
        "type": "yes_no",
        "required": False,
        "cv_field": None,
        "default": "No",
        "ai_prompt": "Si el CV menciona GitHub o proyectos open source, responde 'Sí', si no 'No'.",
    },

    # ── PREGUNTAS ESPECÍFICAS DE CHILE ────────────────────────────
    {
        "id": "rut",
        "label": "RUT",
        "type": "text",
        "required": False,
        "cv_field": None,
        "default": "",
        "ai_prompt": None,
        "note": "Completar manualmente — no se deduce del CV por seguridad",
    },
]


def get_question_ids() -> list[str]:
    return [q["id"] for q in STANDARD_QUESTIONS]


def get_question_by_id(qid: str) -> dict | None:
    return next((q for q in STANDARD_QUESTIONS if q["id"] == qid), None)


def get_required_questions() -> list[dict]:
    return [q for q in STANDARD_QUESTIONS if q.get("required")]


def get_ai_deducible_questions() -> list[dict]:
    """Questions that can be auto-filled using AI from the CV."""
    return [q for q in STANDARD_QUESTIONS if q.get("ai_prompt") and q["ai_prompt"] != "GENERATE_COVER_LETTER"]
