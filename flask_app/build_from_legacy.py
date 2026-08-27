from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

BASE_URL = "http://127.0.0.1:8099"
COMPANY_SHORT = "Urban Sky Web Ltd is registered in England and Wales. Company number: 17421062. Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX."
COMPANY_SENTENCE = "Urban Sky Web Ltd is a company registered in England and Wales under company number 17421062. Its registered office is 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX."
OPERATOR_ROUTES = {"/about/", "/affiliate-disclosure/", "/terms/"}
ESSENTIAL_ROUTES = {
    "/",
    "/learn-english/",
    "/teach-english/",
    "/english-level-test/",
    "/shop/",
    "/contact/",
    "/privacy-policy/",
    "/terms/",
    "/learn-english/a1/",
    "/learn-english/a2/",
    "/learn-english/b1/",
    "/learn-english/b2/",
    "/learn-english/c1/",
    "/learn-english/c2/",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.add(str(href))


def normalise_route(value: str) -> str | None:
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc and parsed.netloc not in {
        "englishasaforeignlanguage.com",
        "www.englishasaforeignlanguage.com",
        "127.0.0.1:8099",
    }:
        return None
    path = parsed.path or "/"
    if path.startswith("/assets/") or path.startswith("/.well-known/"):
        return None
    suffix = Path(path).suffix.lower()
    if suffix in {".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".xml", ".txt", ".pdf", ".zip"}:
        return None
    path = "/" + path.lstrip("/")
    if path != "/" and not path.endswith("/"):
        path += "/"
    return path


def routes_from_sitemap(sitemap: Path) -> set[str]:
    routes: set[str] = set()
    if not sitemap.exists():
        return routes
    try:
        root = ElementTree.parse(sitemap).getroot()
    except ElementTree.ParseError:
        return routes
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            route = normalise_route(element.text.strip())
            if route:
                routes.add(route)
    return routes


def wait_for_server() -> None:
    for _ in range(40):
        try:
            with urlopen(f"{BASE_URL}/", timeout=2) as response:
                if response.status < 500:
                    return
        except (HTTPError, URLError, TimeoutError, OSError):
            time.sleep(0.25)
    raise RuntimeError("The temporary PHP server did not start")


def fetch_page(route: str) -> tuple[int, str]:
    request = Request(
        urljoin(BASE_URL + "/", route.lstrip("/")),
        headers={"Host": "englishasaforeignlanguage.com", "User-Agent": "EFL-Flask-builder/1.0"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")



def add_company_disclosure(route: str, html: str) -> str:
    if "company-disclosure" not in html:
        footer_disclosure = (
            '<div class="company-disclosure">'
            '<p><strong>EnglishAsAForeignLanguage.com is operated by Urban Sky Web Ltd.</strong></p>'
            f'<p>{COMPANY_SHORT}</p>'
            '</div>'
        )
        footer_close = re.search(r"</footer\s*>", html, flags=re.IGNORECASE)
        if footer_close:
            html = html[: footer_close.start()] + footer_disclosure + html[footer_close.start() :]
        else:
            body_close = re.search(r"</body\s*>", html, flags=re.IGNORECASE)
            insertion = body_close.start() if body_close else len(html)
            html = html[:insertion] + f"<footer>{footer_disclosure}</footer>" + html[insertion:]

    if route in OPERATOR_ROUTES and "company-operator" not in html:
        operator_section = (
            '<section class="company-operator" aria-labelledby="company-operator-title">'
            '<h2 id="company-operator-title">Website operator</h2>'
            '<p>EnglishAsAForeignLanguage.com is operated by Urban Sky Web Ltd.</p>'
            f'<p>{COMPANY_SENTENCE}</p>'
            '</section>'
        )
        main_close = re.search(r"</main\s*>", html, flags=re.IGNORECASE)
        insertion = main_close.start() if main_close else html.lower().rfind("</body>")
        if insertion < 0:
            insertion = len(html)
        html = html[:insertion] + operator_section + html[insertion:]

    return html


def apply_compliance_updates(route: str, html: str) -> str:
    """Apply the data-protection copy and controls to rendered legacy pages."""
    html = re.sub(
        r"©\s*\d{4}\s*EFL by Level",
        "© 2026 Urban Sky Web Ltd. EFL by Level is a trading name of Urban Sky Web Ltd.",
        html,
    )
    html = re.sub(
        r'<button type="button" class="text-button" data-cookie-settings>Cookie settings</button>',
        "",
        html,
    )
    html = re.sub(
        r'<div class="cookie-banner" data-cookie-banner hidden>.*?</div></div>',
        "",
        html,
        count=1,
        flags=re.DOTALL,
    )

    privacy_ack = (
        '<label class="consent"><input type="checkbox" name="privacy_ack" value="yes" required>'
        '<span>I have read the <a href="/privacy-policy/">privacy notice</a> and understand how my details will be used to provide this request.</span></label>'
    )
    marketing_choice = (
        '<label class="consent"><input type="checkbox" name="marketing_consent" value="yes">'
        '<span>Optional: send me relevant learning or teaching emails. I can unsubscribe at any time.</span></label>'
    )
    html = html.replace(
        '<label class="consent"><input type="checkbox" name="consent" value="yes" required><span>I agree to receive this resource and relevant learning or teaching emails. I can unsubscribe at any time.</span></label>',
        privacy_ack + marketing_choice + '<p class="form-note">Forms are intended for people aged 16 or over. A parent, guardian or teacher should submit for a younger learner.</p>',
    )
    html = html.replace(
        '<label class="consent"><input type="checkbox" name="consent" value="yes" required><span>I agree to EFL by Level using these details to respond to my message.</span></label>',
        privacy_ack,
    )

    if route == "/contact/":
        company_contact = (
            '<section class="section section-tint"><div class="shell narrow">'
            '<h2>Company contact details</h2>'
            '<p>EnglishAsAForeignLanguage.com is operated by Urban Sky Web Ltd, registered in England and Wales under company number 17421062.</p>'
            '<p>Registered office: 14/2E Docklands Business Centre, 10–16 Tiller Road, London, E14 8PX.</p>'
            '</div></section>'
        )
        main_close = re.search(r"</main\s*>", html, flags=re.IGNORECASE)
        if main_close:
            html = html[: main_close.start()] + company_contact + html[main_close.start() :]

    if route in {"/privacy/", "/privacy-policy/"}:
        privacy = f'''<section class="legal-page"><div class="shell legal-content">
        <p class="eyebrow">Last updated 27 August 2026</p><h1>Privacy Policy</h1>
        <h2>Controller and contact</h2><p>Urban Sky Web Ltd is the controller of personal information handled through EnglishAsAForeignLanguage.com. {COMPANY_SENTENCE} Use the <a href="/contact/">contact page</a> for privacy questions and rights requests.</p>
        <h2>Information we collect</h2><p>When you request a resource, save a level-test result or contact us, we may collect your name, email address, selected resource, estimated CEFR level, message, privacy acknowledgement, optional marketing choice, submission time and originating page. Our hosting provider may also process routine IP-address, browser, page, time, error and security logs. The level-test answers and score are calculated in your browser; only the result level is submitted if you choose to save it.</p>
        <h2>Purposes and lawful bases</h2><p>We use submitted details to provide a requested resource or saved result, respond to a message and administer the relationship. We rely on steps taken at your request in connection with a service and on legitimate interests in responding, correcting content, securing the website and keeping proportionate records. Optional marketing relies on consent. We may also process information to meet a legal obligation or establish, exercise or defend legal claims.</p>
        <h2>Marketing choice</h2><p>Marketing is optional and is not a condition of receiving a resource, saving a result or receiving a reply. You can withdraw marketing consent at any time using the unsubscribe method in a message or the contact page, without affecting earlier lawful processing.</p>
        <h2>Cookies, storage and fonts</h2><p>The current site does not use analytics or advertising cookies. Test and form state is held temporarily in the page while you use it. Pages request font files through Google Fonts, which means Google may receive technical request information such as an IP address and browser details; we rely on legitimate interests in presenting a readable service and keep this use under review.</p>
        <h2>Recipients and international transfers</h2><p>Information may be processed by providers supporting hosting, security, email and font delivery, and by professional advisers or public authorities where necessary. Some providers may process information outside the United Kingdom. Where required, Urban Sky Web Ltd relies on an applicable adequacy regulation or approved contractual safeguards and supplementary measures. You may ask for information about the safeguard used.</p>
        <h2>Retention</h2><p>Website submissions are automatically removed after 24 months. Correspondence is normally deleted within 24 months after it is closed unless a longer period is needed for an ongoing relationship, legal claim or legal obligation. Hosting and security logs follow the provider's operational schedule. Retention is reviewed and information is deleted or anonymised when no longer needed.</p>
        <h2>Your rights</h2><p>Depending on the circumstances, you may request access, correction, deletion, restriction or portability. You may object to processing based on legitimate interests. You may withdraw consent at any time. We may need reasonable information to locate and verify a request and normally respond within one month.</p>
        <h2>Automated results and children</h2><p>The short level test uses fixed rules to estimate a CEFR level for educational guidance. It does not make a decision with legal or similarly significant effects. Forms are intended for people aged 16 or over; a parent, guardian or teacher should submit on behalf of a younger learner.</p>
        <h2>Complaints</h2><p>Please contact us first so we can investigate. You also have the right to complain to the <a href="https://ico.org.uk/make-a-complaint/data-protection-complaints/">Information Commissioner's Office</a>.</p>
        </div></section>'''
        html = re.sub(
            r'<section class="legal-page">.*?</section>',
            privacy,
            html,
            count=1,
            flags=re.DOTALL,
        )
    return html


def update_copied_assets(output: Path) -> None:
    site_script = output / "assets" / "js" / "site.js"
    if site_script.exists():
        text = site_script.read_text(encoding="utf-8")
        text = re.sub(
            r"\n  const banner = document\.querySelector\('\[data-cookie-banner\]'\);.*?\n\n  document\.querySelectorAll\('\[data-lead-form\]'\)",
            "\n\n  document.querySelectorAll('[data-lead-form]')",
            text,
            count=1,
            flags=re.DOTALL,
        )
        site_script.write_text(text, encoding="utf-8")

    level_script = output / "assets" / "js" / "level-test.js"
    if level_script.exists():
        text = level_script.read_text(encoding="utf-8")
        old = '<label class="consent"><input type="checkbox" name="consent" value="yes" required><span>Send my result and relevant study guidance. I can unsubscribe at any time.</span></label>'
        new = (
            '<label class="consent"><input type="checkbox" name="privacy_ack" value="yes" required><span>I have read the <a href="/privacy-policy/">privacy notice</a> and understand how my result and details will be saved.</span></label>'
            '<label class="consent"><input type="checkbox" name="marketing_consent" value="yes"><span>Optional: send me relevant study guidance. I can unsubscribe at any time.</span></label>'
            '<p class="form-note">Forms are intended for people aged 16 or over. A parent, guardian or teacher should submit for a younger learner.</p>'
        )
        level_script.write_text(text.replace(old, new), encoding="utf-8")


def page_name(route: str) -> str:
    return hashlib.sha256(route.encode("utf-8")).hexdigest()[:24] + ".html"


def build(legacy_root: Path, router: Path, output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "pages").mkdir(parents=True)
    (output / "public").mkdir(parents=True)
    (output / "storage").mkdir(parents=True)

    server_log = output.parent / "legacy-php-server.log"
    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            ["php", "-S", "127.0.0.1:8099", "-t", str(legacy_root), str(router)],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            wait_for_server()
            pending = set(ESSENTIAL_ROUTES) | routes_from_sitemap(legacy_root / "sitemap.xml")
            visited: set[str] = set()
            manifest: dict[str, str] = {}

            while pending and len(visited) < 750:
                route = sorted(pending)[0]
                pending.remove(route)
                if route in visited:
                    continue
                visited.add(route)
                status, html = fetch_page(route)
                if html.strip():
                    html = apply_compliance_updates(route, html)
                    html = add_company_disclosure(route, html)
                if status >= 500 or not html.strip():
                    continue
                if status < 400 or route in {"/404/", "/404"}:
                    filename = page_name(route)
                    (output / "pages" / filename).write_text(html, encoding="utf-8")
                    manifest[route] = filename
                    manifest[route.rstrip("/") or "/"] = filename
                if status < 400 and ("<html" in html.lower() or "<!doctype html" in html.lower()):
                    parser = LinkParser()
                    parser.feed(html)
                    for href in parser.links:
                        linked = normalise_route(href)
                        if linked and linked not in visited:
                            pending.add(linked)

            if "/" not in manifest:
                raise RuntimeError("Homepage could not be rendered from the existing site")

            _, not_found_html = fetch_page("/__flask_missing_page__/")
            if not_found_html.strip():
                filename = page_name("/404/")
                (output / "pages" / filename).write_text(not_found_html, encoding="utf-8")
                manifest["/404/"] = filename
                manifest["/404"] = filename

            (output / "page_manifest.json").write_text(
                json.dumps(dict(sorted(manifest.items())), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

    assets = legacy_root / "assets"
    if assets.exists():
        shutil.copytree(assets, output / "assets")
        update_copied_assets(output)
    for name in ("robots.txt", "sitemap.xml", "favicon.ico", "favicon.svg", "apple-touch-icon.png"):
        source = legacy_root / name
        if source.exists():
            shutil.copy2(source, output / "public" / name)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-root", type=Path, required=True)
    parser.add_argument("--router", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.legacy_root.resolve(), args.router.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
