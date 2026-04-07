from pathlib import Path
import re
import unicodedata
from typing import Any

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    from PIL import Image
except ImportError:
    Image = None


COMMON_SKILLS = [
    "excel", "python", "sql", "power bi", "tableau", "sap", "oracle",
    "finanzas", "finance", "financial modeling", "modelacion financiera",
    "modelación financiera", "analisis financiero", "análisis financiero",
    "valuation", "valoracion", "valoración", "dcf", "forecast", "budgeting",
    "presupuestos", "reporting", "accounting", "contabilidad",
    "renta fija", "fixed income", "renta variable", "equity research",
    "mercados de capitales", "capital markets", "gestion de riesgos",
    "gestión de riesgos", "risk management", "machine learning",
    "data analytics", "business intelligence", "research", "bloomberg",
    "portfolio management", "portfolio manager", "asset allocation",
    "crm", "sales", "ventas", "marketing", "logistica", "logística",
    "operaciones", "operations", "customer service", "atención al cliente",
    "project management", "gestion de proyectos", "gestión de proyectos",
    "microsoft office", "powerpoint", "word", "google sheets"
]

SECTION_KEYWORDS = {
    "experience": [
        "experiencia", "experiencia profesional", "professional experience",
        "work experience", "employment history", "career history"
    ],
    "education": [
        "educacion", "educación", "education", "academic background",
        "formacion academica", "formación académica"
    ],
    "skills": [
        "skills", "habilidades", "competencias", "technical skills",
        "herramientas", "stack"
    ],
    "languages": [
        "idiomas", "languages", "language skills"
    ],
    "certifications": [
        "certificaciones", "certifications", "certification", "licenses"
    ],
    "summary": [
        "resumen", "resumen profesional", "profile", "professional summary",
        "about me", "perfil profesional"
    ]
}


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")


def clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_text_from_pdf(file_path: Path) -> str:
    parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            page_text = page.get_text("text")
            if page_text:
                parts.append(page_text)
    return "\n".join(parts)


def extract_text_with_ocr(file_path: Path) -> str:
    text_parts = []

    with fitz.open(file_path) as doc:
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_bytes = pix.tobytes("png")

            image = Image.open(Path("/tmp/ocr_temp.png")) if False else Image.open(__import__("io").BytesIO(img_bytes))
            image_np = np.array(image)

            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np

            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

            text = pytesseract.image_to_string(thresh, lang="eng+spa")
            if text:
                text_parts.append(text)

    return "\n".join(text_parts)


def extract_text_from_docx_fallback(file_path: Path) -> str:
    try:
        from docx import Document
        doc = Document(str(file_path))
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(lines)
    except Exception:
        return ""


def text_quality_score(text: str) -> float:
    if not text:
        return 0.0

    lines = clean_lines(text)
    if not lines:
        return 0.0

    score = 0.0

    if len(text) > 500:
        score += 0.25
    if re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text):
        score += 0.2
    if re.search(r'20\d{2}', text):
        score += 0.15
    if len(lines) > 10:
        score += 0.15

    weird_ratio = text.count("�") / max(len(text), 1)
    if weird_ratio < 0.01:
        score += 0.1

    avg_line_len = sum(len(x) for x in lines) / max(len(lines), 1)
    if avg_line_len > 20:
        score += 0.15

    return round(min(score, 1.0), 2)


def read_cv_text(file_path: Path) -> tuple[str, str, float]:
    ext = file_path.suffix.lower()

    text = ""
    method = "unknown"

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
        method = "pymupdf_text"
    elif ext == ".docx":
        text = extract_text_from_docx_fallback(file_path)
        method = "python_docx"

    quality = text_quality_score(text)

    if ext == ".pdf" and quality < 0.45:
        ocr_text = extract_text_with_ocr(file_path)
        ocr_quality = text_quality_score(ocr_text)

        if ocr_quality > quality:
            text = ocr_text
            quality = ocr_quality
            method = "ocr_tesseract"

    return text, method, quality


def extract_email(text: str) -> tuple[str | None, float]:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if match:
        return match.group(0), 0.99
    return None, 0.0


def extract_phone(text: str) -> tuple[str | None, float]:
    compact = collapse_spaces(text)

    patterns = [
        r'(\+56\s?9\s?\d{4}\s?\d{4})',
        r'(\+56\s?\d{8,9})',
        r'(\b9\s?\d{4}\s?\d{4}\b)',
        r'(\+\d{1,3}\s?\d{6,14})',
    ]

    for pattern in patterns:
        match = re.search(pattern, compact)
        if match:
            return match.group(1).strip(), 0.95

    return None, 0.0


def extract_linkedin(text: str) -> tuple[str | None, float]:
    compact = collapse_spaces(text)
    match = re.search(
        r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/%]+',
        compact,
        re.IGNORECASE
    )
    if match:
        return match.group(0), 0.98
    return None, 0.0


def extract_name(text: str) -> tuple[str | None, float]:
    lines = clean_lines(text)
    blocked = {
        "curriculum vitae", "resume", "cv", "resumen profesional",
        "experiencia profesional", "education", "educacion", "educación"
    }

    for line in lines[:30]:
        raw = line.strip()
        low = normalize_text(raw).lower()

        if low in blocked:
            continue
        if "@" in raw or "linkedin" in low:
            continue
        if re.search(r"\d", raw):
            continue
        if len(raw) < 5 or len(raw) > 60:
            continue

        words = raw.split()
        if 2 <= len(words) <= 5:
            if raw == raw.upper():
                return raw.title(), 0.90
            if sum(1 for w in words if w[:1].isupper()) >= 2:
                return raw.title(), 0.75

    return None, 0.0


def detect_sections(text: str) -> dict[str, str]:
    lines = clean_lines(text)
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "experience": [],
        "education": [],
        "skills": [],
        "languages": [],
        "certifications": [],
        "other": [],
    }

    current = "header"

    for line in lines:
        low = normalize_text(line).lower()

        matched_section = None
        for section, keywords in SECTION_KEYWORDS.items():
            if any(keyword in low for keyword in keywords):
                matched_section = section
                break

        if matched_section:
            current = matched_section
            continue

        sections[current].append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


def extract_skills(text: str) -> tuple[list[str], float]:
    lowered = normalize_text(text).lower()
    found = []

    for skill in COMMON_SKILLS:
        if normalize_text(skill).lower() in lowered:
            found.append(skill)

    found = sorted(set(found))
    confidence = 0.85 if found else 0.0
    return found, confidence


def extract_languages(text: str) -> tuple[list[str], float]:
    lowered = normalize_text(text).lower()
    langs = []

    mapping = {
        "espanol": "Español",
        "spanish": "Español",
        "ingles": "Inglés",
        "english": "Inglés",
        "aleman": "Alemán",
        "german": "Alemán",
        "frances": "Francés",
        "french": "Francés",
        "portugues": "Portugués",
        "portuguese": "Portugués",
        "italiano": "Italiano",
        "italian": "Italiano",
    }

    for key, value in mapping.items():
        if key in lowered:
            langs.append(value)

    langs = sorted(set(langs))
    return langs, (0.9 if langs else 0.0)


def estimate_years_experience(text: str, sections: dict[str, str]) -> tuple[int, float]:
    lowered = normalize_text(text).lower()

    explicit = re.findall(r'(\d+)\s*(anos|año|años|years)', lowered)
    if explicit:
        years = max(int(x[0]) for x in explicit)
        return years, 0.9

    exp_text = sections.get("experience", text)
    years_found = [int(y) for y in re.findall(r'20\d{2}', exp_text)]
    years_found = sorted(set(years_found))

    if len(years_found) >= 2:
        estimate = max(years_found) - min(years_found) + 1
        if estimate >= 0:
            return estimate, 0.6

    if len(years_found) == 1:
        return 1, 0.4

    return 0, 0.0


def infer_seniority(years_experience: int, skills: list[str], text: str) -> tuple[str, float]:
    low = normalize_text(text).lower()

    if years_experience >= 6:
        return "senior", 0.9
    if years_experience >= 2:
        return "semi-senior", 0.85

    leadership_signals = ["manager", "lead", "head", "jefe", "gerente", "director"]
    if any(signal in low for signal in leadership_signals):
        return "semi-senior", 0.55

    if len(skills) >= 8:
        return "semi-senior", 0.5

    return "junior", 0.8


def extract_current_role(sections: dict[str, str]) -> tuple[str | None, float]:
    exp_lines = clean_lines(sections.get("experience", ""))

    for line in exp_lines[:20]:
        low = normalize_text(line).lower()
        if any(word in low for word in [
            "analista", "analyst", "manager", "associate", "engineer",
            "consultant", "intern", "practicante", "portfolio", "specialist",
            "coordinator", "coordinador", "assistant", "executive"
        ]):
            return line, 0.7

    return None, 0.0


def extract_education_items(sections: dict[str, str]) -> list[str]:
    return clean_lines(sections.get("education", ""))[:8]


def extract_experience_items(sections: dict[str, str]) -> list[str]:
    return clean_lines(sections.get("experience", ""))[:12]


def build_warnings(profile: dict[str, Any], extraction_quality: float) -> list[str]:
    warnings = []

    if extraction_quality < 0.5:
        warnings.append("La calidad de extracción del documento fue baja; revisar datos manualmente.")
    if not profile["name"]["value"]:
        warnings.append("No se pudo detectar el nombre con confianza suficiente.")
    if not profile["email"]["value"]:
        warnings.append("No se pudo detectar el email.")
    if not profile["phone"]["value"]:
        warnings.append("No se pudo detectar el teléfono.")
    if len(profile["skills"]["value"]) == 0:
        warnings.append("No se detectaron skills; puede requerir revisión manual.")
    if profile["years_experience"]["confidence"] < 0.5:
        warnings.append("Los años de experiencia son estimados, no explícitos.")

    return warnings


def parse_cv_text(text: str, extraction_quality: float = 1.0, extraction_method: str = "unknown") -> dict[str, Any]:
    sections = detect_sections(text)

    name, name_conf = extract_name(text)
    email, email_conf = extract_email(text)
    phone, phone_conf = extract_phone(text)
    linkedin, linkedin_conf = extract_linkedin(text)
    skills, skills_conf = extract_skills(text)
    languages, lang_conf = extract_languages(text)
    years_exp, years_conf = estimate_years_experience(text, sections)
    seniority, seniority_conf = infer_seniority(years_exp, skills, text)
    current_role, role_conf = extract_current_role(sections)

    profile = {
        "name": {"value": name, "confidence": round(name_conf, 2)},
        "email": {"value": email, "confidence": round(email_conf, 2)},
        "phone": {"value": phone, "confidence": round(phone_conf, 2)},
        "linkedin": {"value": linkedin, "confidence": round(linkedin_conf, 2)},
        "current_role": {"value": current_role, "confidence": round(role_conf, 2)},
        "skills": {"value": skills, "confidence": round(skills_conf, 2)},
        "languages": {"value": languages, "confidence": round(lang_conf, 2)},
        "years_experience": {"value": years_exp, "confidence": round(years_conf, 2)},
        "seniority": {"value": seniority, "confidence": round(seniority_conf, 2)},
        "education_items": extract_education_items(sections),
        "experience_items": extract_experience_items(sections),
    }

    warnings = build_warnings(profile, extraction_quality)

    return {
        "raw_text": text,
        "sections": sections,
        "profile": profile,
        "warnings": warnings,
        "extraction_method": extraction_method,
        "extraction_quality_score": extraction_quality,
    }