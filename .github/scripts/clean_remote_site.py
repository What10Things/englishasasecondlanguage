from __future__ import annotations

import ftplib
import os

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()

# Hosting-managed or persistent paths that must survive the one-time replacement.
PRESERVE_ROOT = {
    ".well-known",
    "storage",
    "cgi-bin",
    ".ftpquota",
    ".user.ini",
    "php.ini",
}


def entries(ftp: ftplib.FTP_TLS, path: str = ".") -> list[tuple[str, dict[str, str]]]:
    return [(name, facts) for name, facts in ftp.mlsd(path) if name not in {".", ".."}]


def remove_tree(ftp: ftplib.FTP_TLS, path: str) -> None:
    for name, facts in entries(ftp, path):
        child = f"{path.rstrip('/')}/{name}"
        item_type = facts.get("type", "file")
        if item_type == "dir":
            remove_tree(ftp, child)
            ftp.rmd(child)
            print(f"Removed directory: {child}")
        else:
            ftp.delete(child)
            print(f"Removed file: {child}")


with ftplib.FTP_TLS(timeout=45) as ftp:
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()

    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))

    print(f"Cleaning website root: {ftp.pwd()}")
    for name, facts in entries(ftp):
        if name in PRESERVE_ROOT:
            print(f"Preserved: {name}")
            continue
        item_type = facts.get("type", "file")
        if item_type == "dir":
            remove_tree(ftp, name)
            ftp.rmd(name)
            print(f"Removed directory: {name}")
        else:
            ftp.delete(name)
            print(f"Removed file: {name}")

print("One-time remote cleanup completed")
