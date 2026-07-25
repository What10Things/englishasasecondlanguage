from __future__ import annotations

import argparse
import ftplib
import os
from pathlib import Path

HOST = "englishasaforeignlanguage.com"
USERNAME = os.environ["FTP_USERNAME"]
PASSWORD = os.environ["FTP_PASSWORD"]
SERVER_DIR = os.environ.get("FTP_SERVER_DIR", "./").strip()


def connect() -> ftplib.FTP_TLS:
    ftp = ftplib.FTP_TLS(timeout=30)
    ftp.connect(HOST, 21)
    ftp.auth()
    ftp.login(USERNAME, PASSWORD)
    ftp.prot_p()
    if SERVER_DIR not in {"", ".", "./", "/"}:
        ftp.cwd(SERVER_DIR.removeprefix("./").rstrip("/"))
    return ftp


def remove_tree(ftp: ftplib.FTP_TLS, path: str) -> None:
    try:
        entries = list(ftp.mlsd(path))
    except (ftplib.error_perm, AttributeError):
        return
    for name, facts in entries:
        if name in {".", ".."}:
            continue
        child = f"{path.rstrip('/')}/{name}"
        if facts.get("type") == "dir":
            remove_tree(ftp, child)
        else:
            try:
                ftp.delete(child)
            except ftplib.error_perm:
                pass
    try:
        ftp.rmd(path)
    except ftplib.error_perm:
        pass


def prepare() -> None:
    with connect() as ftp:
        for name in (
            ".ftp-deploy-efl-state.json",
            ".htaccess",
            "index.php",
            "content.php",
            "index.html",
            "index.htm",
            "default.html",
            "default.htm",
        ):
            try:
                ftp.delete(name)
                print(f"Removed {name}")
            except ftplib.error_perm:
                pass
        for directory in ("api", "__pycache__"):
            remove_tree(ftp, directory)


def force_files(local_root: Path) -> None:
    required = (
        ".htaccess",
        "app.py",
        "passenger_wsgi.py",
        "tmp/restart.txt",
    )
    with connect() as ftp:
        for relative in required:
            local_file = local_root / relative
            if not local_file.exists():
                raise SystemExit(f"Missing deployment file: {relative}")
            parent = str(Path(relative).parent).replace("\\", "/")
            if parent not in {"", "."}:
                current = ftp.pwd()
                for part in parent.split("/"):
                    try:
                        ftp.mkd(part)
                    except ftplib.error_perm:
                        pass
                    ftp.cwd(part)
                ftp.cwd(current)
            with local_file.open("rb") as handle:
                ftp.storbinary(f"STOR {relative}", handle)
            print(f"Forced {relative}")

        lines: list[bytes] = []
        ftp.retrbinary("RETR .htaccess", lines.append)
        content = b"".join(lines).decode("utf-8", errors="replace")
        required_text = (
            "PassengerAppRoot \"/home/uak0tydpqj02/public_html/englishasaforeignlanguage.com\"",
            "PassengerBaseURI \"/\"",
            "PassengerPython \"/home/uak0tydpqj02/virtualenv/flask_app/3.11/bin/python\"",
        )
        missing = [text for text in required_text if text not in content]
        if missing:
            raise SystemExit(f"Remote Passenger configuration is incomplete: {missing}")
        print("Remote Passenger configuration verified")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "force"))
    parser.add_argument("--local-root", type=Path, default=Path("deploy"))
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    else:
        force_files(args.local_root.resolve())


if __name__ == "__main__":
    main()
