from __future__ import annotations

import ftplib
import io
import os
from pathlib import Path

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()
LOCAL_PATH = Path("godaddy/.htaccess")

content = LOCAL_PATH.read_bytes()
if not content.startswith(b"PassengerEnabled off\n"):
    raise SystemExit("Local .htaccess does not disable inherited Passenger")

with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))

    ftp.storbinary("STOR .htaccess", io.BytesIO(content))

    downloaded = bytearray()
    ftp.retrbinary("RETR .htaccess", downloaded.extend)

remote = bytes(downloaded)
if remote != content:
    raise SystemExit("Remote .htaccess differs from the forced upload")
if not remote.startswith(b"PassengerEnabled off\n"):
    raise SystemExit("Remote .htaccess does not disable inherited Passenger")

print("Remote .htaccess verified with PassengerEnabled off")
