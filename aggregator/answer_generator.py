"""
AI-powered answer generator.
Uses Claude to fill in standard questions from the CV when the user hasn't answered them.
"""
import os
import json
import anthropic
from .standard_questions import STANDARD_QUESTIONS, get_question_by_id


def get_claude():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))


def build_answers_from_profile(
    parsed_cv: dict,
    user_preferences: dict,
    job: dict,
    existing_answers: dict,
) -> dict:
    """
    Build a complete answers dict for auto-apply.
    Sources (priority order):
    1. existing_answers (user explicitly provided)
    2. Direct CV fields
    3. AI deduction via Claude
    4. Default values
    """
    answers = {}

    # 1. Start with user-provided answers
    answers.update(existing_answers or {})

    # 2. Fill from CV fields directly
    cv_field_map = {
        "first_name": _extract_first_name(parsed_cv.get("name", "")),
        "last_name": _extract_last_name(parsed_cv.get("name", "")),
        "email": parsed_cv.get("email", ""),
        "phone": parsed_cv.get("phone", ""),
        "linkedin_url": parsed_cv.get("linkedin", ""),
        "years_experience": parsed_cv.get("years_experience"),
    }

    for field, value in cv_field_map.items():
        if value and field not in answers:
            answers[field] = value

    # 3. Fill from user preferences
    pref_map = {
        "salary_expectation": user_preferences.get("salary_expectation"),
        "start_date": "Inmediatamente",
        "english_level": _infer_english_level(parsed_cv.get("languages", [])),
        "current_location": "Santiago, Chile",
        "work_authorization": "Sí",
        "requires_sponsorship": "No",
    }
    for field, value in pref_map.items():
        if value and field not in answers:
            answers[field] = value

    # 4. Apply defaults for anything missing
    for q in STANDARD_QUESTIONS:
        qid = q["id"]
        if qid not in answers and "default" in q and q["default"] is not None:
            answers[qid] = q["default"]

    return answers


def ai_fill_answers(
    parsed_cv: dict,
    user_preferences: dict,
    job: dict,
    existing_answers: dict,
) -> dict:
    """
    Use Claude to fill in answers that can't be derived directly from the CV.
    Returns complete answers dict.
    """
    # Start with what we can fill without AI
    answers = build_answers_from_profile(parsed_cv, user_preferences, job, existing_answers)

    # Build context for AI
    context = {
        "name": parsed_cv.get("name", ""),
        "first_name": answers.get("first_name", ""),
        "skills": ", ".join(parsed_cv.get("skills", [])[:10]),
        "seniority": parsed_cv.get("seniority", "semi-senior"),
        "years_experience": parsed_cv.get("years_experience", 0),
        "current_role": parsed_cv.get("current_role", ""),
        "education": "; ".join(parsed_cv.get("education", [])),
        "languages": ", ".join(parsed_cv.get("languages", [])),
        "summary": parsed_cv.get("summary", ""),
        "job_title": job.get("title", ""),
        "company": job.get("company", ""),
        "candidate_name": answers.get("first_name", parsed_cv.get("name", "")),
    }

    # Questions that need AI
    ai_questions = [
        q for q in STANDARD_QUESTIONS
        if q.get("ai_prompt")
        and q["ai_prompt"] != "GENERATE_COVER_LETTER"
        and q["id"] not in answers
    ]

    if not ai_questions:
        return answers

    # Batch all AI questions in one call for efficiency
    questions_text = "\n".join([
        f"- {q['id']}: {q['ai_prompt'].format(**{k: context.get(k, '') for k in context})}"
        for q in ai_questions
    ])

    prompt = f"""Eres un asistente que ayuda a completar formularios de postulación laboral.

PERFIL DEL CANDIDATO:
- Nombre: {context['name']}
- Cargo actual: {context['current_role']}
- Skills: {context['skills']}
- Seniority: {context['seniority']}
- Años de experiencia: {context['years_experience']}
- Educación: {context['education']}
- Idiomas: {context['languages']}
- Resumen: {context['summary']}

TRABAJO AL QUE POSTULA:
- Cargo: {context['job_title']}
- Empresa: {context['company']}

Completa las siguientes preguntas. Para cada una, da una respuesta concisa y profesional.
Responde SOLO con JSON válido, donde cada key es el id de la pregunta:

{questions_text}

Responde con JSON:
"""

    try:
        client = get_claude()
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text
        json_match = __import__("re").search(r'\{[\s\S]*\}', content)
        if json_match:
            ai_answers = json.loads(json_match.group(0))
            for qid, val in ai_answers.items():
                if qid not in answers or not answers[qid]:
                    answers[qid] = val
    except Exception as e:
        print(f"[ANSWER_GEN] AI fill error: {e}")

    return answers


def _extract_first_name(full_name: str) -> str:
    parts = (full_name or "").strip().split()
    return parts[0] if parts else ""


def _extract_last_name(full_name: str) -> str:
    parts = (full_name or "").strip().split()
    return " ".join(parts[1:]) if len(parts) > 1 else ""


def _infer_english_level(languages: list) -> str:
    langs_str = " ".join(languages).lower()
    if "native" in langs_str or "nativo" in langs_str:
        return "Nativo"
    if "fluent" in langs_str or "fluido" in langs_str or "advanced" in langs_str or "avanzado" in langs_str:
        return "Avanzado"
    if "intermediate" in langs_str or "intermedio" in langs_str:
        return "Intermedio"
    if "english" in langs_str or "inglés" in langs_str:
        return "Intermedio"
    return "Básico"
