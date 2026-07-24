from __future__ import annotations

import ftplib
import json
import os
from io import BytesIO
from pathlib import Path

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()

buffer = BytesIO()
with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))
    ftp.retrbinary("RETR .htaccess", buffer.write)

remote = buffer.getvalue().decode("utf-8", errors="replace")
local_path = Path("godaddy/.htaccess")
local = local_path.read_text(encoding="utf-8", errors="replace") if local_path.exists() else ""

def clean_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip() and not line.lstrip().startswith("#")]

results = {"remote": clean_lines(remote), "local": clean_lines(local), "same": remote == local}
Path("/tmp/htaccess-results.json").write_text(json.dumps(results), encoding="utf-8")
print(json.dumps(results, indent=2), flush=True)
