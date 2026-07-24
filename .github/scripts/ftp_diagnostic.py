from __future__ import annotations

import ftplib
import os
import socket
import sys
from pathlib import Path


def finish(state: str, message: str) -> int:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as output:
            output.write(f"state={state}\n")
            output.write(f"message={message}\n")
    print(message, flush=True)
    return 0 if state == "success" else 1


server = os.environ.get("FTP_SERVER", "").strip()
username = os.environ.get("FTP_USERNAME", "").strip()
password = os.environ.get("FTP_PASSWORD", "")
server_dir = os.environ.get("FTP_SERVER_DIR", "").strip()

if not all((server, username, password, server_dir)):
    raise SystemExit(finish("failure", "One or more required FTP secrets are missing"))

if "://" in server or "/" in server:
    raise SystemExit(finish("failure", "FTP_SERVER must be a hostname only, with no protocol or path"))

try:
    socket.getaddrinfo(server, 21)
    with socket.create_connection((server, 21), timeout=15):
        pass
except OSError:
    raise SystemExit(finish("failure", "FTP_SERVER could not be reached on port 21"))

try:
    with ftplib.FTP_TLS(timeout=30) as ftp:
        ftp.connect(server, 21)
        ftp.auth()
        ftp.prot_p()
        ftp.login(username, password)

        target = server_dir
        if target not in {".", "./", "/"}:
            target = target.removeprefix("./").rstrip("/")
            try:
                ftp.cwd(target)
            except ftplib.error_perm:
                raise SystemExit(
                    finish("failure", "FTP login works, but FTP_SERVER_DIR is not accessible")
                )

        ftp.pwd()
except ftplib.error_perm as exc:
    error = str(exc)
    if error.startswith("530"):
        raise SystemExit(finish("failure", "FTP username or password was rejected by GoDaddy"))
    raise SystemExit(finish("failure", f"GoDaddy rejected the FTPS request: {error[:70]}"))
except (ftplib.Error, OSError, EOFError):
    raise SystemExit(finish("failure", "GoDaddy FTPS/TLS connection could not be established"))

raise SystemExit(finish("success", "FTPS hostname, login and target directory are valid"))
