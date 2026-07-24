from __future__ import annotations

import ftplib
import os

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()
LEGACY_INDEX_FILES = ("index.html", "index.htm", "default.html", "default.htm")

with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))

    removed: list[str] = []
    for filename in LEGACY_INDEX_FILES:
        try:
            ftp.delete(filename)
            removed.append(filename)
        except ftplib.error_perm as exc:
            if not str(exc).startswith("550"):
                raise

print("Removed legacy index files: " + (", ".join(removed) if removed else "none present"), flush=True)
