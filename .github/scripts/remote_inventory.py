from __future__ import annotations

import ftplib
import os

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()


def list_dir(ftp: ftplib.FTP_TLS, path: str, depth: int = 0, max_depth: int = 2) -> None:
    prefix = "  " * depth
    try:
        entries = list(ftp.mlsd(path))
    except (ftplib.error_perm, AttributeError):
        current = ftp.pwd()
        ftp.cwd(path)
        entries = [(name, {"type": "unknown"}) for name in ftp.nlst()]
        ftp.cwd(current)

    for name, facts in sorted(entries, key=lambda item: item[0].lower()):
        if name in {".", ".."}:
            continue
        item_type = facts.get("type", "unknown")
        display_path = f"{path.rstrip('/')}/{name}" if path not in {"", ".", "./", "/"} else name
        print(f"{prefix}{item_type}: {display_path}")
        if item_type == "dir" and depth < max_depth and name not in {".well-known", "storage"}:
            list_dir(ftp, display_path, depth + 1, max_depth)


with ftplib.FTP_TLS(timeout=30) as ftp:
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))
    print(f"Remote root: {ftp.pwd()}")
    list_dir(ftp, ".")
