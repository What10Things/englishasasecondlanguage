from __future__ import annotations

import argparse
import hashlib
import json
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
ESSENTIAL_ROUTES = {
    "/",
    "/learn-english/",
    "/teach-english/",
    "/english-level-test/",
    "/shop/",
    "/contact/",
    "/privacy/",
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
