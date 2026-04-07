"""
Auto-apply engine using Playwright.
Supports: Greenhouse, Lever, Workday, generic forms.
"""
import asyncio
import base64
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser


# ── Detectar qué ATS usa un link ──────────────────────────────────────────────

def detect_ats(apply_link: str) -> str:
    """Return the ATS name from the apply URL."""
    if not apply_link:
        return "unknown"
    url = apply_link.lower()
    if "greenhouse.io" in url or "job-boards.greenhouse" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "myworkdayjobs.com" in url:
        return "workday"
    if "smartrecruiters.com" in url:
        return "smartrecruiters"
    if "computrabajo" in url:
        return "computrabajo"
    if "laborum" in url:
        return "laborum"
    if "bumeran" in url or "multitrabajos" in url:
        return "bumeran"
    return "generic"


# ── Playwright helpers ────────────────────────────────────────────────────────

async def safe_fill(page: Page, selector: str, value: str, timeout: int = 3000):
    """Fill a field if it exists, ignore if not."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.fill(selector, value)
    except Exception:
        pass


async def safe_select(page: Page, selector: str, value: str, timeout: int = 3000):
    """Select an option if the element exists."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.select_option(selector, label=value)
    except Exception:
        try:
            await page.select_option(selector, value=value)
        except Exception:
            pass


async def upload_file(page: Page, selector: str, file_path: str, timeout: int = 5000):
    """Upload a file to a file input."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        await page.set_input_files(selector, file_path)
    except Exception:
        pass


# ── Greenhouse auto-apply ─────────────────────────────────────────────────────

async def apply_greenhouse(
    page: Page,
    answers: dict,
    cv_path: str,
    cover_letter: str,
) -> dict:
    """
    Fill and submit a Greenhouse application form.
    Returns {"success": bool, "message": str}
    """
    try:
        # Wait for the form to load
        await page.wait_for_selector("#first_name", timeout=15000)

        # Basic fields
        await safe_fill(page, "#first_name", answers.get("first_name", ""))
        await safe_fill(page, "#last_name", answers.get("last_name", ""))
        await safe_fill(page, "#email", answers.get("email", ""))
        await safe_fill(page, "#phone", answers.get("phone", ""))

        # Upload CV
        if cv_path and Path(cv_path).exists():
            await upload_file(page, "#resume", cv_path)
            await asyncio.sleep(1)

        # Cover letter as file (save to temp) or text
        if cover_letter:
            # Try text area first
            cl_textarea = await page.query_selector("textarea[id*='cover_letter']")
            if cl_textarea:
                await cl_textarea.fill(cover_letter)
            else:
                # Upload as file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(cover_letter)
                    cl_path = f.name
                await upload_file(page, "#cover_letter", cl_path)

        # Location
        if answers.get("current_location"):
            await safe_fill(page, "#job_application_location", answers["current_location"])

        # LinkedIn
        if answers.get("linkedin_url"):
            await safe_fill(page, "input[id*='linkedin']", answers["linkedin_url"])
            # Also try question_* fields
            linkedin_inputs = await page.query_selector_all("input[aria-label*='LinkedIn']")
            for inp in linkedin_inputs:
                await inp.fill(answers["linkedin_url"])

        # Custom questions — scan all question_* inputs
        all_inputs = await page.query_selector_all("input[id^='question_'], textarea[id^='question_'], select[id^='question_']")
        for inp in all_inputs:
            label_text = await inp.get_attribute("aria-label") or ""
            label_lower = label_text.lower()

            # Match label to answer
            answer = _match_label_to_answer(label_lower, answers)
            if answer:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                if tag == "textarea":
                    await inp.fill(str(answer))
                elif tag == "select":
                    try:
                        await inp.select_option(label=str(answer))
                    except Exception:
                        pass
                else:
                    await inp.fill(str(answer))

        # Checkboxes (e.g. GDPR consent, disability disclosure)
        checkboxes = await page.query_selector_all("input[type='checkbox']")
        for cb in checkboxes:
            label = await cb.get_attribute("aria-label") or ""
            # Auto-accept GDPR/privacy consent
            if any(w in label.lower() for w in ["consent", "gdpr", "privacy", "terms"]):
                is_checked = await cb.is_checked()
                if not is_checked:
                    await cb.check()

        # Submit
        submit_btn = await page.query_selector("button[type='submit'], input[type='submit']")
        if submit_btn:
            await submit_btn.click()
            await asyncio.sleep(3)

            # Check for success
            page_text = await page.inner_text("body")
            success_phrases = [
                "application submitted", "thank you", "gracias",
                "aplicación enviada", "postulación enviada", "we received"
            ]
            if any(p in page_text.lower() for p in success_phrases):
                return {"success": True, "message": "Postulación enviada via Greenhouse"}
            else:
                # Take screenshot for debugging
                return {"success": True, "message": "Formulario enviado (verificar confirmación)"}
        else:
            return {"success": False, "message": "No se encontró el botón de envío"}

    except Exception as e:
        return {"success": False, "message": f"Error en Greenhouse: {str(e)}"}


# ── Lever auto-apply ──────────────────────────────────────────────────────────

async def apply_lever(
    page: Page,
    answers: dict,
    cv_path: str,
    cover_letter: str,
) -> dict:
    """Fill and submit a Lever application form."""
    try:
        await page.wait_for_selector("input[name='name'], #name", timeout=15000)

        # Full name
        full_name = f"{answers.get('first_name', '')} {answers.get('last_name', '')}".strip()
        await safe_fill(page, "input[name='name'], #name", full_name)
        await safe_fill(page, "input[name='email'], #email", answers.get("email", ""))
        await safe_fill(page, "input[name='phone'], #phone", answers.get("phone", ""))

        # Current company/org
        await safe_fill(page, "input[name='org'], #org", answers.get("current_company", ""))

        # LinkedIn
        if answers.get("linkedin_url"):
            await safe_fill(page, "input[name='urls[LinkedIn]']", answers["linkedin_url"])

        # Resume upload
        if cv_path and Path(cv_path).exists():
            await upload_file(page, "input[type='file']", cv_path)
            await asyncio.sleep(1)

        # Cover letter
        if cover_letter:
            cl_area = await page.query_selector("textarea[name='comments'], #comments, textarea[placeholder*='cover']")
            if cl_area:
                await cl_area.fill(cover_letter)

        # Custom questions
        custom_inputs = await page.query_selector_all(".application-question input, .application-question textarea, .application-question select")
        for inp in custom_inputs:
            label_el = await inp.query_selector("xpath=../../label")
            label_text = ""
            if label_el:
                label_text = (await label_el.inner_text()).lower()
            else:
                label_text = (await inp.get_attribute("placeholder") or "").lower()

            answer = _match_label_to_answer(label_text, answers)
            if answer:
                tag = await inp.evaluate("el => el.tagName.toLowerCase()")
                if tag == "textarea":
                    await inp.fill(str(answer))
                elif tag == "select":
                    try:
                        await inp.select_option(label=str(answer))
                    except Exception:
                        pass
                else:
                    await inp.fill(str(answer))

        # Submit
        await page.click("button[type='submit'], .submit-app-btn")
        await asyncio.sleep(3)

        page_text = await page.inner_text("body")
        if any(p in page_text.lower() for p in ["thank you", "gracias", "submitted", "success"]):
            return {"success": True, "message": "Postulación enviada via Lever"}
        return {"success": True, "message": "Formulario enviado (verificar confirmación)"}

    except Exception as e:
        return {"success": False, "message": f"Error en Lever: {str(e)}"}


# ── Generic form apply ────────────────────────────────────────────────────────

async def apply_generic(
    page: Page,
    answers: dict,
    cv_path: str,
    cover_letter: str,
) -> dict:
    """Try to fill any generic job application form."""
    try:
        await asyncio.sleep(3)  # Wait for JS to render

        # Map common field names/labels
        field_map = {
            "name": ["name", "nombre", "full_name", "fullname"],
            "first_name": ["first_name", "firstname", "nombre"],
            "last_name": ["last_name", "lastname", "apellido"],
            "email": ["email", "correo", "mail"],
            "phone": ["phone", "telefono", "celular", "tel"],
            "linkedin": ["linkedin"],
            "cover_letter": ["cover_letter", "carta", "presentacion", "message", "mensaje"],
        }

        for answer_key, selectors in field_map.items():
            value = answers.get(answer_key, "")
            if not value:
                continue

            for sel in selectors:
                # Try various selector strategies
                for strategy in [
                    f"input[name='{sel}']",
                    f"input[id='{sel}']",
                    f"input[placeholder*='{sel}']",
                    f"textarea[name='{sel}']",
                    f"textarea[id='{sel}']",
                ]:
                    try:
                        el = await page.query_selector(strategy)
                        if el:
                            await el.fill(str(value))
                            break
                    except Exception:
                        pass

        # Upload CV
        file_inputs = await page.query_selector_all("input[type='file']")
        if file_inputs and cv_path and Path(cv_path).exists():
            await file_inputs[0].set_input_files(cv_path)
            await asyncio.sleep(1)

        # Cover letter in textarea
        if cover_letter:
            textareas = await page.query_selector_all("textarea")
            for ta in textareas:
                ph = (await ta.get_attribute("placeholder") or "").lower()
                if any(w in ph for w in ["cover", "letter", "message", "carta", "presentaci"]):
                    await ta.fill(cover_letter)
                    break

        # Submit
        for selector in ["button[type='submit']", "input[type='submit']", "button.submit", ".btn-apply"]:
            btn = await page.query_selector(selector)
            if btn:
                await btn.click()
                await asyncio.sleep(3)
                return {"success": True, "message": "Formulario enviado"}

        return {"success": False, "message": "No se encontró botón de envío"}

    except Exception as e:
        return {"success": False, "message": f"Error en formulario genérico: {str(e)}"}


# ── Label matching ────────────────────────────────────────────────────────────

def _match_label_to_answer(label: str, answers: dict) -> Optional[str]:
    """Match a form label to the best answer from user's answers dict."""
    label = label.lower().strip()

    patterns = [
        (["linkedin", "perfil profesional"], "linkedin_url"),
        (["github", "portfolio", "portafolio", "website", "sitio web"], "portfolio_url"),
        (["salary", "salario", "sueldo", "renta", "pretensión", "expectativa"], "salary_expectation"),
        (["start", "inicio", "empezar", "disponibilidad"], "start_date"),
        (["english", "inglés", "ingles"], "english_level"),
        (["years", "años de experiencia", "experiencia"], "years_experience"),
        (["why", "por qué", "porque quieres", "motivaci"], "why_company"),
        (["strength", "fortaleza", "mejor cualidad"], "greatest_strength"),
        (["achievement", "logro", "mayor logro"], "biggest_achievement"),
        (["cover letter", "carta de presentación", "carta"], "cover_letter"),
        (["location", "ubicación", "ciudad", "ciudad actual"], "current_location"),
        (["phone", "teléfono", "celular"], "phone"),
        (["rut"], "rut"),
        (["how did you hear", "cómo conociste", "cómo te enteraste"], "referred_by"),
        (["authorization", "permiso de trabajo", "work permit"], "work_authorization"),
        (["relocation", "reubicar", "traslado"], "willing_to_relocate"),
        (["sponsorship", "visa", "patrocinio"], "requires_sponsorship"),
        (["vehicle", "vehículo", "auto"], "has_vehicle"),
        (["disability", "discapacidad"], "has_disability"),
        (["gender", "género"], "gender"),
    ]

    for keywords, answer_key in patterns:
        if any(kw in label for kw in keywords):
            return str(answers.get(answer_key, "")) or None

    return None


# ── Main apply orchestrator ───────────────────────────────────────────────────

async def auto_apply(
    apply_link: str,
    answers: dict,
    cv_base64: str,
    cover_letter: str,
    headless: bool = True,
) -> dict:
    """
    Main entry point. Auto-applies to any job given the URL.

    Args:
        apply_link: URL of the job application page
        answers: Dict of all standard answers (from user profile + AI)
        cv_base64: Base64-encoded CV PDF
        cover_letter: Generated cover letter text
        headless: Run browser without GUI

    Returns:
        {"success": bool, "message": str, "ats": str}
    """
    ats = detect_ats(apply_link)

    # Save CV to temp file
    cv_path = None
    try:
        cv_bytes = base64.b64decode(cv_base64)
        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False,
            prefix=f"cv_{answers.get('first_name', 'candidate')}_"
        ) as f:
            f.write(cv_bytes)
            cv_path = f.name
    except Exception as e:
        return {"success": False, "message": f"Error decodificando CV: {e}", "ats": ats}

    try:
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="es-CL",
            )
            page = await context.new_page()

            # Navigate to the application page
            await page.goto(apply_link, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Route to the right handler
            if ats == "greenhouse":
                result = await apply_greenhouse(page, answers, cv_path, cover_letter)
            elif ats == "lever":
                result = await apply_lever(page, answers, cv_path, cover_letter)
            else:
                result = await apply_generic(page, answers, cv_path, cover_letter)

            await browser.close()
            result["ats"] = ats
            return result

    except Exception as e:
        return {
            "success": False,
            "message": f"Error Playwright: {str(e)}",
            "ats": ats,
        }
    finally:
        # Clean up temp CV file
        if cv_path and Path(cv_path).exists():
            Path(cv_path).unlink(missing_ok=True)
