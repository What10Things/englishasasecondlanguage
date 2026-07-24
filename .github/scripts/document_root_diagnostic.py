from __future__ import annotations

import ftplib
import io
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

FTP_HOST = "englishasaforeignlanguage.com"
WEB_HOST = "https://englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()
MARKER_NAME = "efl-github-document-root-marker.txt"
MARKER_VALUE = f"EFL_GITHUB_ROOT_{int(time.time())}"

with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(FTP_HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))
    ftp.storbinary(f"STOR {MARKER_NAME}", io.BytesIO(MARKER_VALUE.encode("utf-8")))
    ftp_path = ftp.pwd()

paths = [
    f"/{MARKER_NAME}",
    f"/englishasaforeignlanguage.com/{MARKER_NAME}",
]
found = ""
results: list[str] = []
for path in paths:
    request = Request(
        f"{WEB_HOST}{path}?check={int(time.time())}",
        headers={"Cache-Control": "no-cache", "User-Agent": "EFL-document-root-check/1.0"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            results.append(f"{path}=HTTP{response.status}")
            if MARKER_VALUE in body:
                found = path
                break
    except HTTPError as exc:
        results.append(f"{path}=HTTP{exc.code}")
    except (URLError, TimeoutError, OSError):
        results.append(f"{path}=connection-error")

with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(FTP_HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))
    try:
        ftp.delete(MARKER_NAME)
    except ftplib.error_perm:
        pass

if found == f"/{MARKER_NAME}":
    state = "success"
    message = f"Domain document root matches FTP root {ftp_path}"
elif found:
    state = "failure"
    message = "Domain points to the parent folder; set cPanel document root to public_html/englishasaforeignlanguage.com"
else:
    state = "failure"
    message = "Uploaded FTP marker is not served by the domain; cPanel document root or DNS targets another site"

print(message)
print("; ".join(results))
output_path = os.environ.get("GITHUB_OUTPUT")
if output_path:
    with Path(output_path).open("a", encoding="utf-8") as output:
        output.write(f"state={state}\n")
        output.write(f"message={message[:135]}\n")

raise SystemExit(0 if state == "success" else 1)
