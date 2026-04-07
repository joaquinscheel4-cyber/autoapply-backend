"""
Auto-apply using Playwright connected to Browserless.io (remote Chrome).
Supports Greenhouse, Lever, and generic ATS forms.
"""
import asyncio
import base64
import os
import tempfile
from typing import Optional

BROWSERLESS_TOKEN = os.environ.get("BROWSERLESS_TOKEN", "")
BROWSERLESS_WS = f"wss://production-sfo.browserless.io?token={BROWSERLESS_TOKEN}"


def detect_ats(apply_link: str) -> str:
    url = apply_link.lower()
    if "greenhouse.io" in url or "job-boards.greenhouse" in url:
        return "greenhouse"
    if "lever.co" in url:
        return "lever"
    if "myworkdayjobs.com" in url:
        return "workday"
    if "smartrecruiters.com" in url:
        return "smartrecruiters"
    return "generic"


async def auto_apply(
    apply_link: str,
    answers: dict,
    cv_base64: str,
    cover_letter: str = "",
    headless: bool = True,
) -> dict:
    """
    Connect to Browserless, navigate to job form, fill it, submit.
    Returns {"success": bool, "message": str}
    """
    if not BROWSERLESS_TOKEN:
        return {"success": False, "message": "BROWSERLESS_TOKEN no configurado"}

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"success": False, "message": "playwright no instalado en el backend"}

    ats = detect_ats(apply_link)

    # Write CV to temp file for upload
    cv_path = None
    if cv_base64:
        try:
            cv_bytes = base64.b64decode(cv_base64)
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(cv_bytes)
            tmp.flush()
            cv_path = tmp.name
        except Exception:
            cv_path = None

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.connect_over_cdp(BROWSERLESS_WS)
            context = await browser.new_context(
                accept_downloads=True,
                locale="es-CL",
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            page.set_default_timeout(30000)

            try:
                if ats == "greenhouse":
                    result = await apply_greenhouse(page, apply_link, answers, cv_path, cover_letter)
                elif ats == "lever":
                    result = await apply_lever(page, apply_link, answers, cv_path, cover_letter)
                else:
                    result = await apply_generic(page, apply_link, answers, cv_path, cover_letter)
            finally:
                await context.close()
                await browser.close()

        return result

    except Exception as e:
        return {"success": False, "message": f"Error en auto-apply: {str(e)}"}
    finally:
        if cv_path:
            try:
                os.unlink(cv_path)
            except Exception:
                pass


async def safe_fill(page, selector: str, value: str):
    """Fill a field if it exists."""
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            await el.fill(value)
            return True
    except Exception:
        pass
    return False


async def safe_upload(page, selector: str, file_path: str):
    """Upload a file if selector exists."""
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            await el.set_input_files(file_path)
            return True
    except Exception:
        pass
    return False


async def apply_greenhouse(page, url: str, answers: dict, cv_path: Optional[str], cover_letter: str) -> dict:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    await safe_fill(page, 'input[name="first_name"], input[id*="first_name"]', answers.get("first_name", ""))
    await safe_fill(page, 'input[name="last_name"], input[id*="last_name"]', answers.get("last_name", ""))
    await safe_fill(page, 'input[name="email"], input[type="email"]', answers.get("email", ""))
    await safe_fill(page, 'input[name="phone"], input[type="tel"]', answers.get("phone", ""))
    await safe_fill(page, 'input[name="location"], input[id*="location"]', answers.get("location", "Santiago, Chile"))

    linkedin = answers.get("linkedin_url", "")
    if linkedin:
        await safe_fill(page, 'input[id*="linkedin"], input[placeholder*="LinkedIn"]', linkedin)

    if cv_path:
        await safe_upload(page, 'input[type="file"][name*="resume"], input[type="file"][id*="resume"]', cv_path)
        await page.wait_for_timeout(1000)

    if cover_letter:
        await safe_fill(page, 'textarea[name*="cover"], textarea[id*="cover"]', cover_letter)

    # Extra visible questions
    inputs = await page.locator("input[type='text']:visible, textarea:visible").all()
    for inp in inputs:
        try:
            placeholder = (await inp.get_attribute("placeholder") or "").lower()
            label_text = ""
            label_id = await inp.get_attribute("id") or ""
            if label_id:
                lbl = page.locator(f'label[for="{label_id}"]')
                if await lbl.count() > 0:
                    label_text = (await lbl.inner_text()).lower()

            combined = placeholder + " " + label_text
            current_val = await inp.input_value()
            if current_val:
                continue

            if "salary" in combined or "sueldo" in combined or "pretensión" in combined:
                await inp.fill(str(answers.get("salary_expectation", "")))
            elif "rut" in combined:
                await inp.fill(answers.get("rut", ""))
            elif "linkedin" in combined:
                await inp.fill(answers.get("linkedin_url", ""))
            elif "website" in combined or "portfolio" in combined:
                await inp.fill(answers.get("website", ""))
        except Exception:
            continue

    submitted = False
    for selector in [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Submit")', 'button:has-text("Apply")', 'button:has-text("Send")',
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(3000)
                submitted = True
                break
        except Exception:
            continue

    if submitted:
        content = await page.content()
        success = any(s in content.lower() for s in ["thank you", "gracias", "submitted", "received", "confirmación", "success"])
        return {"success": success, "message": "Formulario Greenhouse enviado" if success else "Enviado (verifica tu email)", "ats": "greenhouse"}

    return {"success": False, "message": "No se encontró botón de envío en Greenhouse", "ats": "greenhouse"}


async def apply_lever(page, url: str, answers: dict, cv_path: Optional[str], cover_letter: str) -> dict:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    await safe_fill(page, 'input[name="name"], input[id*="name"]', answers.get("full_name", ""))
    await safe_fill(page, 'input[name="email"], input[type="email"]', answers.get("email", ""))
    await safe_fill(page, 'input[name="phone"], input[type="tel"]', answers.get("phone", ""))
    await safe_fill(page, 'input[name="org"]', answers.get("current_company", ""))
    await safe_fill(page, 'input[name="urls[LinkedIn]"], input[placeholder*="LinkedIn"]', answers.get("linkedin_url", ""))

    if cover_letter:
        await safe_fill(page, 'textarea[name="comments"], textarea[id*="cover"]', cover_letter)

    if cv_path:
        await safe_upload(page, 'input[type="file"]', cv_path)
        await page.wait_for_timeout(1500)

    submitted = False
    for selector in ['button[type="submit"]', 'button:has-text("Submit application")', 'button:has-text("Apply")']:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(3000)
                submitted = True
                break
        except Exception:
            continue

    if submitted:
        content = await page.content()
        success = any(s in content.lower() for s in ["thank you", "gracias", "submitted", "received", "success"])
        return {"success": success, "message": "Formulario Lever enviado", "ats": "lever"}

    return {"success": False, "message": "No se encontró botón de envío en Lever", "ats": "lever"}


async def apply_generic(page, url: str, answers: dict, cv_path: Optional[str], cover_letter: str) -> dict:
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)

    field_map = [
        (['input[name*="first"][type="text"]', 'input[placeholder*="First"]'], answers.get("first_name", "")),
        (['input[name*="last"][type="text"]', 'input[placeholder*="Last"]'], answers.get("last_name", "")),
        (['input[name*="name"][type="text"]', 'input[placeholder*="name" i]'], answers.get("full_name", "")),
        (['input[type="email"]', 'input[name*="email"]'], answers.get("email", "")),
        (['input[type="tel"]', 'input[name*="phone"]'], answers.get("phone", "")),
        (['input[name*="linkedin" i]', 'input[placeholder*="linkedin" i]'], answers.get("linkedin_url", "")),
    ]

    for selectors, value in field_map:
        if not value:
            continue
        for sel in selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    current = await el.input_value()
                    if not current:
                        await el.fill(value)
                    break
            except Exception:
                continue

    if cv_path:
        await safe_upload(page, 'input[type="file"]', cv_path)
        await page.wait_for_timeout(1500)

    if cover_letter:
        await safe_fill(page, 'textarea', cover_letter)

    submitted = False
    for selector in [
        'button[type="submit"]', 'input[type="submit"]',
        'button:has-text("Apply")', 'button:has-text("Submit")',
        'button:has-text("Send")', 'button:has-text("Enviar")',
        'button:has-text("Postular")',
    ]:
        try:
            btn = page.locator(selector).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                await page.wait_for_timeout(3000)
                submitted = True
                break
        except Exception:
            continue

    if submitted:
        content = await page.content()
        success = any(s in content.lower() for s in ["thank you", "gracias", "submitted", "received", "success", "confirmación"])
        return {"success": success, "message": "Formulario enviado", "ats": "generic"}

    return {"success": False, "message": "No se pudo enviar el formulario", "ats": "generic"}
