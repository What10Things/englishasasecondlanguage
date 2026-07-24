from __future__ import annotations

import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://englishasaforeignlanguage.com"
CHECKS = {
    "/": ("English that meets you", "Two clear journeys"),
    "/english-level-test/": ("24 short questions", "Find your starting point"),
    "/learn-english/a1/": ("Core grammar",),
    "/teach-english/": ("Ready-made resources", "Teacher hub"),
}


def compact(value: str, limit: int = 115) -> str:
    return re.sub(r"\s+", " ", value).strip()[:limit]


def page_identity(html: str) -> str:
    for pattern in (r"<title[^>]*>(.*?)</title>", r"<h1[^>]*>(.*?)</h1>"):
        match = re.search(pattern, html, flags=re.I | re.S)
        if match:
            return compact(re.sub(r"<[^>]+>", "", match.group(1)))
    return compact(re.sub(r"<[^>]+>", " ", html)[:300]) or "empty response"


failures: list[str] = []
for path, required in CHECKS.items():
    url = f"{BASE}{path}?diagnostic={int(time.time())}"
    request = Request(
        url,
        headers={
            "Accept": "text/html",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
            "User-Agent": "EFL-live-diagnostic/1.0",
        },
    )
    try:
        with urlopen(request, timeout=25) as response:
            status = response.status
            html = response.read().decode("utf-8", errors="replace")
        missing = [phrase for phrase in required if phrase not in html]
        if missing:
            failures.append(f"{path} HTTP {status}, served '{page_identity(html)}'")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        failures.append(f"{path} HTTP {exc.code}, served '{page_identity(body)}'")
    except (URLError, TimeoutError, OSError) as exc:
        failures.append(f"{path} connection {type(exc).__name__}")

state = "success" if not failures else "failure"
message = "Live rebuilt site is responding correctly" if not failures else failures[0]
print(message, flush=True)

output_path = os.environ.get("GITHUB_OUTPUT")
if output_path:
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"state={state}\n")
        output.write(f"message={compact(message, 135)}\n")

raise SystemExit(0 if state == "success" else 1)
